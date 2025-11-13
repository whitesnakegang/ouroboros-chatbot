"""
채팅 관련 라우터
LangChain을 사용한 RAG 챗봇
"""
from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.ingest.pipeline import IngestPipeline
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

# Ingest 파이프라인 인스턴스 (벡터 스토어와 임베딩 생성기 공유)
ingest_pipeline = IngestPipeline()

# RAG 서비스 초기화
try:
    rag_service = RAGService(
        vectorstore=ingest_pipeline.vectorstore,
        embedder=ingest_pipeline.embedder
    )
except ValueError as e:
    # OpenAI API 키가 없는 경우 경고만 출력하고 나중에 초기화
    print(f"Warning: RAG service not initialized: {e}")
    rag_service = None


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    사용자 메시지를 받아 RAG 기반 응답을 반환합니다.
    
    공식 문서를 검색하여 관련 정보를 찾고, LLM을 사용하여 답변을 생성합니다.
    """
    if rag_service is None:
        raise HTTPException(
            status_code=500,
            detail="RAG service is not available. Please set OPENAI_API_KEY in .env file"
        )
    
    try:
        # RAG를 사용한 응답 생성
        result = rag_service.chat(
            question=request.message,
            top_k=settings.retrieval_top_k
        )
        
        # 소스 정보를 문자열 리스트로 변환
        sources = []
        for source in result.get("sources", []):
            source_str = f"Document: {source.get('document_id', 'unknown')}"
            if source.get("filename"):
                source_str += f" ({source['filename']})"
            sources.append(source_str)
        
        return ChatResponse(
            response=result["response"],
            conversation_id=request.conversation_id or "default",
            sources=sources if sources else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

