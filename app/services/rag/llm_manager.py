"""
LLM 관리 모듈
LangChain ChatOpenAI 초기화 및 설정
"""
import os
import logging
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


def create_llm(llm: Optional[Any] = None) -> ChatOpenAI:
    """
    LangChain ChatOpenAI 인스턴스 생성
    
    Args:
        llm: 기존 LLM 인스턴스 (있으면 재사용)
        
    Returns:
        ChatOpenAI 인스턴스
        
    Raises:
        ValueError: API 키가 없는 경우
    """
    if llm is not None:
        return llm
    
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
    llm_kwargs = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "openai_api_key": api_key,
    }
    
    # base_url이 설정되어 있으면 (GMS 사용 시) 추가
    if base_url:
        llm_kwargs["openai_api_base"] = base_url
        # GMS는 max_completion_tokens만 사용 (max_tokens 지원 안 함)
        llm_kwargs["model_kwargs"] = {
            "max_completion_tokens": settings.max_tokens
        }
        logger.info(f"[LLMManager] GMS 설정 - max_completion_tokens: {settings.max_tokens}")
    else:
        # 일반 OpenAI는 max_tokens 사용
        llm_kwargs["max_tokens"] = settings.max_tokens
        logger.info(f"[LLMManager] OpenAI 설정 - max_tokens: {settings.max_tokens}")
    
    return ChatOpenAI(**llm_kwargs)

