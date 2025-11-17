"""
채팅 관련 라우터
LangChain을 사용한 RAG 챗봇
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models import ChatRequest, ChatResponse
from app.services.rag import RAGService, update_summary_background
from app.services.session_manager import SessionManager
from app.ingest.pipeline import IngestPipeline
from app.config import settings

logger = logging.getLogger(__name__)

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

# 세션 매니저 초기화
session_manager = SessionManager(max_history=5)




@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    사용자 메시지를 받아 RAG 기반 응답을 반환합니다.
    
    공식 문서를 검색하여 관련 정보를 찾고, LLM을 사용하여 답변을 생성합니다.
    세션 ID를 통해 대화 맥락을 유지합니다.
    요약은 백그라운드에서 처리되어 다음 요청부터 반영됩니다.
    """
    if rag_service is None:
        raise HTTPException(
            status_code=500,
            detail="RAG service is not available. Please set OPENAI_API_KEY in .env file"
        )
    
    try:
        # 세션 ID 가져오기 또는 생성
        session_id = session_manager.get_or_create_session(request.session_id)
        
        # 이전 대화 히스토리 조회
        full_history = session_manager.get_history(session_id)
        existing_summary = session_manager.get_summary(session_id) or ""
        
        # 사용자 메시지를 세션에 추가
        session_manager.add_message(session_id, "user", request.message)
        
        # 히스토리 구성 (기존 요약 사용, 업데이트는 백그라운드에서 처리)
        recent_count = 1  # 최근 1쌍(2개 메시지)만 전체 포함
        
        if len(full_history) > recent_count * 2:
            # 요약이 필요한 경우: 기존 요약 + 최근 대화 사용
            recent_history = full_history[-(recent_count * 2):]
            history_with_summary = {
                "summary": existing_summary,
                "recent": recent_history
            }
        else:
            # 요약 불필요 (최근 대화만 전달)
            history_with_summary = full_history
        
        # RAG를 사용한 응답 생성 (대화 히스토리 포함)
        # 기존 요약을 사용하므로 LLM 호출 1회만 발생
        result = rag_service.chat(
            question=request.message,
            top_k=settings.retrieval_top_k,
            conversation_history=history_with_summary
        )
        
        # 응답을 세션에 추가
        session_manager.add_message(session_id, "assistant", result["response"])
        
        # 백그라운드에서 요약 업데이트 (응답 반환 후 처리)
        # 업데이트된 요약은 다음 요청부터 사용됨
        if len(full_history) >= recent_count * 2:  # recent_count = 1이므로 2개 이상일 때 요약
            # 업데이트된 히스토리 가져오기 (방금 추가한 메시지 포함)
            updated_history = session_manager.get_history(session_id)
            background_tasks.add_task(
                update_summary_background,
                session_id=session_id,
                full_history=updated_history,
                existing_summary=existing_summary,
                session_manager=session_manager,
                history_summarizer=rag_service.history_summarizer
            )
            logger.info(f"[chat] 백그라운드 요약 업데이트 작업 추가 - 세션 {session_id}")
        
        # 소스 정보를 문자열 리스트로 변환
        sources = []
        for source in result.get("sources", []):
            source_str = f"Document: {source.get('document_id', 'unknown')}"
            if source.get("filename"):
                source_str += f" ({source['filename']})"
            sources.append(source_str)
        
        return ChatResponse(
            response=result["response"],
            sources=sources if sources else None,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"[chat] 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


@router.get("/summary/{session_id}")
async def get_summary(session_id: str):
    """
    세션의 요약된 히스토리를 조회합니다 (디버깅/확인용).
    
    Args:
        session_id: 세션 ID
        
    Returns:
        요약 정보 (요약 내용, 히스토리 개수 등)
    """
    try:
        summary = session_manager.get_summary(session_id)
        full_history = session_manager.get_history(session_id)
        
        return {
            "session_id": session_id,
            "summary": summary or "",
            "summary_length": len(summary) if summary else 0,
            "has_summary": bool(summary and summary.strip()),
            "history_count": len(full_history),
            "recent_count": len(full_history[-4:]) if len(full_history) >= 4 else len(full_history)
        }
    except Exception as e:
        logger.error(f"[get_summary] 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting summary: {str(e)}"
        )

