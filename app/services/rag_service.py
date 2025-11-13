"""
RAG (Retrieval-Augmented Generation) 서비스
LangChain을 사용한 벡터 검색 및 LLM 응답 생성
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.config import settings
from app.ingest.embedder import Embedder
from app.vectorstore.chroma import ChromaVectorStore


class RAGService:
    """RAG 서비스 - 벡터 검색 + LLM 응답 생성"""
    
    def __init__(
        self,
        vectorstore: Optional[ChromaVectorStore] = None,
        embedder: Optional[Embedder] = None,
        llm: Optional[ChatOpenAI] = None
    ):
        """
        RAG 서비스 초기화
        
        Args:
            vectorstore: 벡터 스토어 인스턴스
            embedder: 임베딩 생성기 인스턴스
            llm: LangChain LLM 인스턴스
        """
        self.vectorstore = vectorstore
        self.embedder = embedder
        
        # LLM 초기화
        if llm is None:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file")
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.max_tokens,
                openai_api_key=settings.openai_api_key
            )
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
    
    def generate_response(
        self,
        question: str,
        context_documents: Optional[List[Dict[str, Any]]] = None,
        top_k: int = None
    ) -> Dict[str, Any]:
        """
        RAG 기반 응답 생성
        
        Args:
            question: 사용자 질문
            context_documents: 컨텍스트 문서 (없으면 자동 검색)
            top_k: 검색할 문서 수
            
        Returns:
            응답 딕셔너리 (response, sources, retrieved_docs)
        """
        # 문서 검색 (없는 경우)
        if context_documents is None:
            context_documents = self.retrieve_documents(question, top_k=top_k)
        
        # 컨텍스트 구성
        if not context_documents:
            return {
                "response": "죄송합니다. 관련된 문서를 찾을 수 없습니다. 다른 질문을 해주시거나 문서를 먼저 추가해주세요.",
                "sources": [],
                "retrieved_docs": []
            }
        
        # 문서 내용을 하나의 컨텍스트로 합치기
        context_parts = []
        sources = []
        
        for doc in context_documents:
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
        
        # 프롬프트 생성
        prompt = self.prompt_template.format(
            context=context,
            question=question
        )
        
        # LLM 호출
        try:
            # LangChain 0.1.0+ 버전에서는 invoke 또는 predict 사용
            # ChatOpenAI는 HumanMessage를 받거나 문자열을 직접 받을 수 있음
            try:
                # 먼저 invoke 시도 (최신 API)
                from langchain.schema import HumanMessage
                messages = [HumanMessage(content=prompt)]
                result = self.llm.invoke(messages)
                response = result.content if hasattr(result, 'content') else str(result)
            except (AttributeError, TypeError):
                # predict 메서드 시도 (구버전 API)
                response = self.llm.predict(prompt)
        except Exception as e:
            return {
                "response": f"오류가 발생했습니다: {str(e)}",
                "sources": sources,
                "retrieved_docs": context_documents
            }
        
        return {
            "response": response,
            "sources": sources,
            "retrieved_docs": context_documents
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

