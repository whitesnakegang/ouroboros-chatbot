"""
애플리케이션 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 설정
    app_name: str = "RAG Chatbot API"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LLM 설정
    openai_api_key: Optional[str] = None
    llm_model: str = "gpt-5-mini"  # OpenAI 모델 이름 (GMS 사용 시: "gpt-5-mini" 등)
    llm_temperature: float = 1  # LLM 온도 설정
    max_tokens: int = 1000  # 최대 토큰 수
    
    # GMS (Gen AI Management System) 설정
    use_gms: bool = False  # GMS 사용 여부
    gms_base_url: Optional[str] = None  # GMS API 엔드포인트 (예: "https://gms.ssafy.io/gmsapi/api.openai.com/v1")
    gms_api_key: Optional[str] = None  # GMS API 키 (GMS_KEY)
    
    # 임베딩 모델 설정
    # 추천 모델 옵션:
    # - "intfloat/multilingual-e5-base" (기본값): 다국어 지원 강화, 768차원, 100개 이상 언어 지원
    #   * instruction prefix 자동 적용: 문서는 "passage: ", 쿼리는 "query: " 사용
    # - "intfloat/multilingual-e5-large": 더 높은 품질, 1024차원, 느리지만 매우 정확함
    # - "intfloat/multilingual-e5-small": 경량 버전, 빠르지만 품질은 낮음
    # - "sentence-transformers/all-MiniLM-L6-v2": 빠르고 가벼움, 384차원, CPU 친화적
    # - "sentence-transformers/all-mpnet-base-v2": 더 높은 품질, 768차원, 느리지만 정확함
    # - "jhgan/ko-sroberta-multitask": 한국어 특화 모델 (768차원)
    embedding_model: str = "intfloat/multilingual-e5-base"
    embedding_device: str = "cpu"  # "cpu" or "cuda"
    
    # 벡터 DB 설정
    vector_db_type: str = "chroma"
    chroma_db_path: str = "./vector_db"
    collection_name: str = "documents"
    
    # 문서 처리 설정
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # RAG 설정
    retrieval_top_k: int = 5  # 검색할 문서 수
    similarity_threshold: float = 0.5  # 유사도 임계값 (거리가 이 값보다 크면 관련성 낮음으로 판단)
    rag_prompt_template: str = """다음 공식 문서를 참고하여 사용자의 질문에 답변해주세요.

공식 문서 내용:
{context}

사용자 질문: {question}

답변:"""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()

