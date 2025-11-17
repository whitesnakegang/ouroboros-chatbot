"""
FastAPI 메인 애플리케이션
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import documents, chat

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    description="간단한 RAG 시스템 챗봇 API",
    version=settings.app_version
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(documents.router)
app.include_router(chat.router)


# 기본 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot API is running",
        "version": settings.app_version
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
