"""
Pydantic 모델 정의
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str = Field(..., description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="세션 ID (없으면 자동 생성)")


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    response: str = Field(..., description="챗봇 응답")
    sources: Optional[List[str]] = Field(None, description="참조된 문서 소스")
    session_id: str = Field(..., description="세션 ID")


class DocumentRequest(BaseModel):
    """문서 추가 요청 모델"""
    text: str = Field(..., description="문서 텍스트")
    metadata: Optional[Dict[str, Any]] = Field(None, description="문서 메타데이터")
    document_id: Optional[str] = Field(None, description="문서 ID")


class DocumentResponse(BaseModel):
    """문서 추가 응답 모델"""
    message: str = Field(..., description="응답 메시지")
    document_id: str = Field(..., description="저장된 문서 ID")
    chunks_count: int = Field(..., description="생성된 청크 수")


class DocumentListResponse(BaseModel):
    """문서 목록 응답 모델"""
    documents: List[Dict[str, Any]] = Field(..., description="문서 목록")
    total: int = Field(..., description="전체 문서 수")


class BulkDocumentResponse(BaseModel):
    """대량 문서 업로드 응답 모델"""
    message: str = Field(..., description="응답 메시지")
    total_documents: int = Field(..., description="처리된 문서 수")
    total_chunks: int = Field(..., description="생성된 총 청크 수")
    document_ids: List[str] = Field(..., description="저장된 문서 ID 리스트")
    errors: Optional[List[str]] = Field(None, description="오류 메시지 리스트")


class SearchRequest(BaseModel):
    """검색 요청 모델"""
    query: str = Field(..., description="검색 쿼리")
    n_results: int = Field(5, description="반환할 결과 수", ge=1, le=20)


class SearchResponse(BaseModel):
    """검색 응답 모델"""
    query: str = Field(..., description="검색 쿼리")
    results: List[Dict[str, Any]] = Field(..., description="검색 결과")
    total: int = Field(..., description="검색된 결과 수")


class StatsResponse(BaseModel):
    """통계 응답 모델"""
    total_documents: int = Field(..., description="전체 문서 수")
    total_chunks: int = Field(..., description="전체 청크 수")
    collection_name: str = Field(..., description="컬렉션 이름")


class ChunkResponse(BaseModel):
    """청크 응답 모델"""
    chunk_id: str = Field(..., description="청크 ID")
    text: str = Field(..., description="청크 텍스트")
    metadata: Dict[str, Any] = Field(..., description="청크 메타데이터")


class ChunkListResponse(BaseModel):
    """청크 목록 응답 모델"""
    chunks: List[ChunkResponse] = Field(..., description="청크 목록")
    total: int = Field(..., description="전체 청크 수")
