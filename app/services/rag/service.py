"""
RAG 서비스 - 메인 모듈
벡터 검색 및 LLM 응답 생성 통합 서비스
"""
import logging
from typing import List, Dict, Any, Optional
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from app.config import settings
from app.ingest.embedder import Embedder
from app.vectorstore.chroma import ChromaVectorStore
from .llm_manager import create_llm
from .conversation import HistorySummarizer

logger = logging.getLogger(__name__)


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
        self.llm = create_llm(llm)
        
        # 히스토리 요약기 초기화
        self.history_summarizer = HistorySummarizer(self.llm)
    
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
        top_k: int = None,
        similarity_threshold: Optional[float] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        RAG 기반 응답 생성
        
        Args:
            question: 사용자 질문
            context_documents: 컨텍스트 문서 (없으면 자동 검색)
            top_k: 검색할 문서 수 (기본값: settings.retrieval_top_k)
            similarity_threshold: (사용 안 함) LLM이 관련성을 판단하므로 이 파라미터는 무시됩니다.
            conversation_history: 이전 대화 히스토리 (선택적)
            
        Returns:
            응답 딕셔너리 (response, sources, retrieved_docs)
        """
        # 문서 검색 (없는 경우)
        if context_documents is None:
            context_documents = self.retrieve_documents(question, top_k=top_k)
        
        # 컨텍스트 구성
        context_parts = []
        sources = []
        has_documents = bool(context_documents)
        
        if context_documents:
            # 모든 검색된 문서를 LLM에 전달 (필터링 없이)
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
                
                # 문서 내용만 컨텍스트에 추가
                context_parts.append(content)
        
        context = "\n\n".join(context_parts) if context_parts else ""
        
        # SystemMessage 생성
        system_message = SystemMessage(content="""당신은 공식 문서 가이드입니다. 사용자의 질문에 대해 공식 문서를 참고하여 정확하고 간결하게 답변하는 것이 역할입니다.

답변 작성 시 다음 원칙을 지켜주세요:
- 답변은 간결하고 핵심적인 내용만 포함하세요. 불필요하게 길게 작성하지 마세요.
- 중요한 부분만 요약하여 제공하세요.
- 여러 문서가 제공되면, 질문과 관련성이 높은 문서만 선택하여 참고하세요.
- 질문과 직접적으로 관련이 있는 문서만 사용하여 답변하세요. 관련성이 낮은 문서는 무시하세요.
- 사용자의 질문에서 "이거", "이것", "이 라이브러리", "이 도구" 등 지시어가 나오면, 이전 대화 맥락이나 제공된 문서를 통해 무엇을 가리키는지 파악하고 해당 공식 문서/라이브러리로 인식하여 답변하세요.
- 제공된 문서 정보를 최대한 활용하여 답변을 만들어주세요. 문서에서 관련 정보를 찾을 수 있으면 반드시 참고하여 답변하세요.
- 질문이 공식 문서와 전혀 관련이 없는 일반적인 대화나 정보 질문인 경우(예: 날씨, 뉴스, 개인적인 일상 대화 등), 공식 문서를 참고하지 말고 자연스럽게 답변하되, 공식 문서에 관한 질문을 하도록 친절하게 유도해주세요.
- 만약 사용자가 당신이 누구인지, 어떤 역할을 하는지 물어보는 경우(예: "너 누구야", "너는 뭐야", "역할이 뭐야" 등), 공식 문서를 참고하지 말고 "공식 문서 도우미 챗봇"이라고 답하고 역할을 간결하게 설명해주세요.
- 이전 대화 맥락을 고려하여 답변하세요. 사용자가 이전에 언급한 내용을 참고할 수 있습니다.""")
        
        # 메시지 리스트 구성
        messages = [system_message]
        
        # 이전 대화 히스토리 추가 (요약 포함)
        history_messages = self.history_summarizer.build_history_messages(conversation_history)
        messages.extend(history_messages)
        
        # 현재 사용자 질문과 문서 컨텍스트
        # 문서가 있는 경우와 없는 경우에 따라 프롬프트 구성
        if has_documents:
            user_message = HumanMessage(content=f"""다음은 벡터 검색으로 찾은 공식 문서들입니다.

공식 문서 목록:
{context}

사용자 질문: {question}

위 문서들을 참고하여 답변해주세요:
- 질문에서 "이거", "이것", "이 라이브러리" 등 지시어가 있으면, 이전 대화 맥락이나 문서 내용을 통해 무엇을 가리키는지 파악하여 답변하세요. 못 찾겠는 경우, 지시어를 공식문서로 생각하고 답변하세요.
- 문서에서 관련 정보를 찾을 수 있으면 반드시 참고하여 답변하세요.
- 질문과 관련성이 높은 문서를 우선적으로 참고하고, 관련성이 낮은 문서는 무시하세요.
- 질문이 공식 문서와 관련이 없는 일반적인 대화인 경우, 자연스럽게 답변하되 공식 문서에 관한 질문을 하도록 친절하게 유도해주세요.

답변:""")
        else:
            # 문서가 없는 경우
            user_message = HumanMessage(content=f"""사용자 질문: {question}

답변:""")
        messages.append(user_message)
        
        # LLM 호출
        try:
            logger.info(f"[generate_response] LLM 호출 시작 - 질문: {question[:50]}...")
            logger.info(f"[generate_response] 메시지 구조 - 개수: {len(messages)}, 총 길이: {sum(len(str(msg.content)) for msg in messages if hasattr(msg, 'content'))} 문자")
            
            result = self.llm.invoke(messages)
            
            # 즉시 결과 확인
            logger.info(f"[generate_response] LLM 호출 완료 - result 타입: {type(result)}")
            if hasattr(result, 'content'):
                logger.info(f"[generate_response] result.content 길이: {len(result.content) if result.content else 0} 문자")
            
            # 응답이 객체인 경우 content 속성 추출, 아니면 문자열로 변환
            if isinstance(result, AIMessage):
                response = result.content
            elif hasattr(result, 'content'):
                response = result.content
            elif hasattr(result, 'text'):
                response = result.text
            else:
                response = str(result)
            
            # 빈 응답 체크 및 로깅
            if not response or (isinstance(response, str) and response.strip() == ""):
                logger.error(f"[generate_response] ⚠️ LLM이 빈 응답을 반환했습니다!")
                logger.error(f"[generate_response] result 타입: {type(result)}, result: {result}")
                
                # AIMessage인지 확인
                if isinstance(result, AIMessage):
                    logger.error(f"[generate_response] ✅ AIMessage 블록 진입 확인")
                    logger.error(f"[generate_response]   - content: '{result.content}'")
                    logger.error(f"[generate_response]   - content 타입: {type(result.content)}")
                    logger.error(f"[generate_response]   - content 길이: {len(result.content) if result.content else 0}")
                    
                    # AIMessage의 모든 속성 확인
                    all_attrs = [attr for attr in dir(result) if not attr.startswith('_')]
                    logger.error(f"[generate_response]   - AIMessage 속성 목록: {all_attrs}")
                    
                    # response_metadata 확인 (다양한 방법 시도)
                    # 방법 1: hasattr로 확인
                    has_metadata_attr = hasattr(result, 'response_metadata')
                    logger.error(f"[generate_response]   - hasattr(response_metadata): {has_metadata_attr}")
                    
                    # 방법 2: 직접 접근 시도
                    try:
                        if has_metadata_attr:
                            metadata = result.response_metadata
                            logger.error(f"[generate_response] ✅ response_metadata 직접 접근 성공")
                            logger.error(f"[generate_response]   - response_metadata 타입: {type(metadata)}")
                            logger.error(f"[generate_response]   - response_metadata 상세: {metadata}")
                            
                            if isinstance(metadata, dict):
                                for key, value in metadata.items():
                                    logger.error(f"[generate_response]     - {key}: {value}")
                                
                                # 핵심 정보 확인
                                finish_reason = metadata.get('finish_reason')
                                token_usage = metadata.get('token_usage', {})
                                logger.error(f"[generate_response]   - finish_reason: {finish_reason}")
                                logger.error(f"[generate_response]   - token_usage: {token_usage}")
                                
                                if finish_reason == "length":
                                    logger.error(f"[generate_response] ⚠️ 토큰 제한으로 응답이 잘렸습니다!")
                                    logger.error(f"[generate_response]   - max_completion_tokens 설정: {settings.max_tokens}")
                                    if isinstance(token_usage, dict):
                                        completion_tokens = token_usage.get('completion_tokens', 0)
                                        logger.error(f"[generate_response]   - completion_tokens: {completion_tokens}")
                                elif finish_reason:
                                    logger.error(f"[generate_response]   - finish_reason: {finish_reason} (정상 종료 아님)")
                    except AttributeError as e:
                        logger.error(f"[generate_response] ⚠️ response_metadata 접근 실패: {e}")
                    except Exception as e:
                        logger.error(f"[generate_response] ⚠️ response_metadata 확인 중 오류: {e}", exc_info=True)
                    
                    # 방법 3: getattr로 확인
                    metadata_via_getattr = getattr(result, 'response_metadata', None)
                    if metadata_via_getattr is not None:
                        logger.error(f"[generate_response] ✅ getattr로 response_metadata 발견: {metadata_via_getattr}")
                    else:
                        logger.error(f"[generate_response] ⚠️ getattr로도 response_metadata를 찾을 수 없습니다!")
                    
                    # usage_metadata 확인
                    usage_metadata = getattr(result, 'usage_metadata', None)
                    if usage_metadata is not None:
                        logger.error(f"[generate_response]   - usage_metadata: {usage_metadata}")
                    
                    # 추가: id 속성 확인 (LangChain AIMessage)
                    msg_id = getattr(result, 'id', None)
                    if msg_id:
                        logger.error(f"[generate_response]   - message id: {msg_id}")
                    
                    # 추가: response_metadata를 dict로 직접 접근 시도
                    if isinstance(result, dict):
                        logger.error(f"[generate_response]   - result가 dict 타입입니다: {result}")
                    elif hasattr(result, '__dict__'):
                        result_dict = result.__dict__
                        logger.error(f"[generate_response]   - result.__dict__: {list(result_dict.keys())}")
                        if 'response_metadata' in result_dict:
                            logger.error(f"[generate_response] ✅ __dict__에 response_metadata 발견: {result_dict['response_metadata']}")
                else:
                    logger.error(f"[generate_response] ⚠️ result가 AIMessage 타입이 아닙니다. 타입: {type(result)}")
                
                # LLM 설정 확인
                model_kwargs_val = getattr(self.llm, 'model_kwargs', None)
                logger.error(f"[generate_response] LLM 설정:")
                logger.error(f"[generate_response]   - model_kwargs: {model_kwargs_val}")
                logger.error(f"[generate_response]   - model_name: {getattr(self.llm, 'model_name', None)}")
                logger.error(f"[generate_response]   - openai_api_base: {getattr(self.llm, 'openai_api_base', None)}")
                
                # 메시지 길이 확인
                total_length = sum(len(str(msg.content)) for msg in messages if hasattr(msg, 'content'))
                logger.error(f"[generate_response] 총 메시지 길이: {total_length} 문자, 메시지 개수: {len(messages)}")
                
                response = "죄송하지만 응답을 생성하는 데 문제가 발생했습니다. 서버 로그를 확인해주세요."
                
        except Exception as e:
            logger.error(f"[generate_response] LLM 호출 오류: {str(e)}", exc_info=True)
            return {
                "response": f"오류가 발생했습니다: {str(e)}",
                "sources": sources,
                "retrieved_docs": context_documents or []
            }
        
        return {
            "response": response,
            "sources": sources,
            "retrieved_docs": context_documents or []
        }
    
    def chat(
        self,
        question: str,
        top_k: int = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        챗봇 인터페이스 - 질문을 받아 응답 반환
        
        Args:
            question: 사용자 질문
            top_k: 검색할 문서 수
            conversation_history: 이전 대화 히스토리 (선택적)
            
        Returns:
            응답 딕셔너리
        """
        return self.generate_response(question, top_k=top_k, conversation_history=conversation_history)

