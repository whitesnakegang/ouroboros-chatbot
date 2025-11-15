"""
RAG (Retrieval-Augmented Generation) 서비스
LangChain을 사용한 벡터 검색 및 LLM 응답 생성
"""
import os
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from app.config import settings
from app.ingest.embedder import Embedder
from app.vectorstore.chroma import ChromaVectorStore


class RAGService:
    """RAG 서비스 - 벡터 검색 + LLM 응답 생성"""
    
    def __init__(
        self,
        vectorstore: Optional[ChromaVectorStore] = None,
        embedder: Optional[Embedder] = None,
        llm: Optional[Any] = None
    ):
        """
        RAG 서비스 초기화
        
        Args:
            vectorstore: 벡터 스토어 인스턴스
            embedder: 임베딩 생성기 인스턴스
            llm: LangChain LLM 인스턴스 (선택적, 없으면 자동 초기화)
        """
        self.vectorstore = vectorstore
        self.embedder = embedder
        
        # LLM 초기화
        if llm is None:
            # API 키와 엔드포인트 설정
            api_key = None
            base_url = None
            
            if settings.use_gms and settings.gms_base_url and settings.gms_api_key:
                # GMS 사용 시
                api_key = settings.gms_api_key
                base_url = settings.gms_base_url
            elif settings.openai_api_key:
                # 일반 OpenAI 사용 시
                api_key = settings.openai_api_key
                # 환경 변수에서 base_url이 설정되어 있으면 사용
                base_url = os.environ.get("OPENAI_API_BASE", None)
            else:
                raise ValueError(
                    "API key is required. Set OPENAI_API_KEY or "
                    "(USE_GMS=true, GMS_API_KEY, GMS_BASE_URL) in .env file"
                )
            
            # ChatOpenAI 초기화 (GMS 지원)
            # GMS 사용 시 max_completion_tokens 사용, 일반 OpenAI는 max_tokens 사용
            llm_kwargs = {
                "model": settings.llm_model,
                "temperature": settings.llm_temperature,
                "openai_api_key": api_key,
            }
            
            # base_url이 설정되어 있으면 (GMS 사용 시) 추가
            if base_url:
                llm_kwargs["openai_api_base"] = base_url
                # GMS는 max_completion_tokens를 model_kwargs로 전달
                llm_kwargs["model_kwargs"] = {
                    "max_completion_tokens": settings.max_tokens
                }
            else:
                # 일반 OpenAI는 max_tokens 사용
                llm_kwargs["max_tokens"] = settings.max_tokens
            
            self.llm = ChatOpenAI(**llm_kwargs)
        else:
            self.llm = llm
        
        # 프롬프트 템플릿
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template=settings.rag_prompt_template
        )
    
    def retrieve_documents(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        벡터 검색으로 관련 문서 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 수
            
        Returns:
            검색 결과 리스트
        """
        if not self.vectorstore or not self.embedder:
            raise ValueError("Vectorstore and embedder must be initialized")
        
        top_k = top_k or settings.retrieval_top_k
        
        # 쿼리 임베딩 생성
        query_text = query
        if "multilingual-e5" in settings.embedding_model.lower():
            query_text = f"query: {query}"
        
        query_embedding = self.embedder.embed_text(query_text)
        
        # 벡터 검색
        search_results = self.vectorstore.search(
            query_embedding=query_embedding,
            n_results=top_k
        )
        
        # 결과 포맷팅
        results = []
        for doc, distance, metadata, doc_id in zip(
            search_results["documents"],
            search_results["distances"],
            search_results["metadatas"],
            search_results["ids"]
        ):
            results.append({
                "content": doc,
                "metadata": metadata,
                "distance": float(distance),
                "id": doc_id
            })
        
        return results
    
    def _is_self_introduction_question(self, question: str) -> bool:
        """
        자기소개 관련 질문인지 확인
        
        Args:
            question: 사용자 질문
            
        Returns:
            자기소개 질문 여부
        """
        question_lower = question.lower().strip()
        
        # 자기소개 관련 키워드
        intro_keywords = [
            "너 누구", "너는 누구", "너가 누구", "당신은 누구", "당신이 누구",
            "너 뭐야", "너는 뭐야", "너가 뭐야", "당신은 뭐야", "당신이 뭐야",
            "소개", "자기소개", "역할", "무엇", "뭐하는", "뭘하는",
            "누구세요", "뭐세요", "뭔가요", "뭐하는거", "뭘하는거"
        ]
        
        return any(keyword in question_lower for keyword in intro_keywords)
    
    def generate_response(
        self,
        question: str,
        context_documents: Optional[List[Dict[str, Any]]] = None,
        top_k: int = None,
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        RAG 기반 응답 생성
        
        Args:
            question: 사용자 질문
            context_documents: 컨텍스트 문서 (없으면 자동 검색)
            top_k: 검색할 문서 수
            similarity_threshold: 유사도 임계값 (거리가 이 값보다 크면 관련성 낮음으로 판단, None이면 설정값 사용)
            
        Returns:
            응답 딕셔너리 (response, sources, retrieved_docs)
        """
        # 자기소개 질문인 경우 참고자료 없이 역할을 명시하여 답변
        if self._is_self_introduction_question(question):
            return self._generate_introduction_response()
        
        # 유사도 임계값 설정 (기본값 사용)
        if similarity_threshold is None:
            similarity_threshold = settings.similarity_threshold
        
        # 문서 검색 (없는 경우)
        if context_documents is None:
            context_documents = self.retrieve_documents(question, top_k=top_k)
        
        # 컨텍스트 구성
        if not context_documents:
            # 문서가 없으면 일반 답변 생성 (참고자료 없이)
            return self._generate_general_response(question)
        
        # 검색된 문서의 유사도 확인 (가장 유사한 문서의 거리 확인)
        best_distance = min(doc.get("distance", 1.0) for doc in context_documents)
        
        # 유사도가 임계값보다 높으면(관련성이 낮으면) 참고자료 없이 답변
        if best_distance > similarity_threshold:
            return self._generate_general_response(question)
        
        # 관련성이 높은 문서만 필터링 (임계값 이하의 문서만 사용)
        relevant_docs = [
            doc for doc in context_documents 
            if doc.get("distance", 1.0) <= similarity_threshold
        ]
        
        if not relevant_docs:
            return self._generate_general_response(question)
        
        # 문서 내용을 하나의 컨텍스트로 합치기
        context_parts = []
        sources = []
        
        for doc in relevant_docs:
            content = doc["content"]
            metadata = doc.get("metadata", {})
            
            # 소스 정보 추출
            source_info = {
                "document_id": metadata.get("document_id", ""),
                "source": metadata.get("source", ""),
                "filename": metadata.get("filename", ""),
                "chunk_index": metadata.get("chunk_index", 0)
            }
            sources.append(source_info)
            
            # 컨텍스트에 추가
            context_parts.append(content)
        
        context = "\n\n".join(context_parts)
        
        # RAG 프롬프트 생성 (참고자료 사용)
        # SystemMessage로 역할 명시
        system_message = SystemMessage(content="""당신은 공식 문서 가이드입니다. 사용자의 질문에 대해 공식 문서를 참고하여 정확하고 간결하게 답변하는 것이 역할입니다.

답변 작성 시 다음 원칙을 지켜주세요:
- 답변은 간결하고 핵심적인 내용만 포함하세요. 불필요하게 길게 작성하지 마세요.
- 중요한 부분만 요약하여 제공하세요.
- 공식 문서 내용이 질문과 직접적으로 관련이 있는 경우에만 참고하여 답변하세요.
- 공식 문서 내용이 질문과 관련이 없거나, 문서에서 정확한 답을 찾을 수 없다면, "제공된 공식 문서에서는 해당 정보를 찾을 수 없습니다."라고 답변하세요.
- 만약 사용자가 당신이 누구인지, 어떤 역할을 하는지 물어보는 경우(예: "너 누구야", "너는 뭐야", "역할이 뭐야" 등), 공식 문서를 참고하지 말고 "공식 문서 도우미 챗봇"이라고 답하고 역할을 간결하게 설명해주세요.""")
        
        user_message = HumanMessage(content=f"""다음 공식 문서를 참고하여 사용자의 질문에 답변해주세요.

공식 문서 내용:
{context}

사용자 질문: {question}

답변:""")
        
        messages = [system_message, user_message]
        
        # LLM 호출
        try:
            result = self.llm.invoke(messages)
            
            # 응답이 객체인 경우 content 속성 추출, 아니면 문자열로 변환
            if hasattr(result, 'content'):
                response = result.content
            else:
                response = str(result)
        except Exception as e:
            return {
                "response": f"오류가 발생했습니다: {str(e)}",
                "sources": sources,
                "retrieved_docs": relevant_docs
            }
        
        return {
            "response": response,
            "sources": sources,
            "retrieved_docs": relevant_docs
        }
    
    def _generate_introduction_response(self) -> Dict[str, Any]:
        """
        자기소개 응답 생성
        챗봇의 역할과 기능을 설명
        
        Returns:
            응답 딕셔너리
        """
        system_message = SystemMessage(content="""당신은 공식 문서 가이드 챗봇입니다. 사용자에게 자신의 역할과 기능을 간결하게 소개해주세요.""")
        
        user_message = HumanMessage(content="""사용자가 당신이 누구인지 물어보고 있습니다. 
다음 내용을 포함하여 간결하게 자기소개를 해주세요:
- 공식 문서 도우미 챗봇임을 명시
- 공식 문서를 참고하여 질문에 답변하는 역할
- 간결하고 핵심적인 답변 제공

답변:""")
        
        messages = [system_message, user_message]
        
        try:
            result = self.llm.invoke(messages)
            
            if hasattr(result, 'content'):
                response = result.content
            else:
                response = str(result)
        except Exception as e:
            response = "안녕하세요! 저는 공식 문서 도우미 챗봇입니다. 공식 문서를 참고하여 여러분의 질문에 간결하고 정확하게 답변해드리는 것이 제 역할입니다."
        
        return {
            "response": response,
            "sources": [],
            "retrieved_docs": []
        }
    
    def _generate_general_response(self, question: str) -> Dict[str, Any]:
        """
        참고자료 없이 일반 답변 생성
        공식 문서와 관련이 없는 질문에 대해 사용
        
        Args:
            question: 사용자 질문
            
        Returns:
            응답 딕셔너리
        """
        # SystemMessage로 역할 명시
        system_message = SystemMessage(content="""당신은 공식 문서 가이드입니다. 사용자의 질문에 대해 정확하고 간결하게 답변하는 것이 역할입니다.

답변 작성 시 다음 원칙을 지켜주세요:
- 답변은 간결하고 핵심적인 내용만 포함하세요. 불필요하게 길게 작성하지 마세요.
- 중요한 부분만 요약하여 제공하세요.
- 정확히 모르는 내용이거나 확실하지 않은 경우에는 "죄송하지만 해당 내용에 대해 정확히 알지 못합니다."라고 솔직하게 답변해주세요.
- 억지로 답변을 만들지 말고, 모르는 것은 모른다고 답변하는 것이 중요합니다.""")
        
        user_message = HumanMessage(content=f"""사용자 질문: {question}

답변:""")
        
        messages = [system_message, user_message]
        
        try:
            result = self.llm.invoke(messages)
            
            if hasattr(result, 'content'):
                response = result.content
            else:
                response = str(result)
        except Exception as e:
            response = f"오류가 발생했습니다: {str(e)}"
        
        return {
            "response": response,
            "sources": [],
            "retrieved_docs": []
        }
    
    def chat(
        self,
        question: str,
        top_k: int = None
    ) -> Dict[str, Any]:
        """
        챗봇 인터페이스 - 질문을 받아 응답 반환
        
        Args:
            question: 사용자 질문
            top_k: 검색할 문서 수
            
        Returns:
            응답 딕셔너리
        """
        return self.generate_response(question, top_k=top_k)

