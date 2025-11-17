"""
문서 관련 라우터
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from app.models import (
    DocumentRequest,
    DocumentResponse,
    DocumentListResponse,
    BulkDocumentResponse,
    SearchRequest,
    SearchResponse,
    StatsResponse,
    ChunkListResponse,
    ChunkResponse
)
from app.ingest.pipeline import IngestPipeline
from app.ingest.loader import DocumentLoader
from app.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

# Ingest 파이프라인 인스턴스
ingest_pipeline = IngestPipeline()


@router.post("", response_model=DocumentResponse)
async def add_document(request: DocumentRequest):
    """
    문서를 벡터 데이터베이스에 추가합니다.
    """
    try:
        result = ingest_pipeline.ingest_text(
            text=request.text,
            metadata=request.metadata,
            document_id=request.document_id
        )
        
        return DocumentResponse(
            message=result["message"],
            document_id=result["document_id"],
            chunks_count=result["chunks_count"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """
    저장된 문서 목록을 반환합니다.
    """
    try:
        # 고유한 문서만 추출 (청크가 아닌 원본 문서)
        all_docs = ingest_pipeline.get_all_documents()
        
        # 문서 ID별로 그룹화
        document_map = {}
        for doc in all_docs:
            doc_id = doc.get("metadata", {}).get("document_id")
            if doc_id and doc_id not in document_map:
                document_map[doc_id] = {
                    "id": doc_id,
                    "metadata": doc.get("metadata", {}),
                    "chunks_count": 0
                }
            if doc_id:
                document_map[doc_id]["chunks_count"] += 1
        
        documents = list(document_map.values())
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    문서를 삭제합니다.
    """
    try:
        success = ingest_pipeline.delete_document(document_id)
        if success:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@router.delete("", summary="모든 문서 삭제")
async def delete_all_documents():
    """
    벡터 데이터베이스의 모든 문서를 삭제합니다.
    
    ⚠️ 주의: 이 작업은 되돌릴 수 없습니다!
    """
    try:
        # 삭제 전 문서 수 확인
        stats_before = ingest_pipeline.vectorstore.count()
        
        success = ingest_pipeline.delete_all_documents()
        
        if success:
            return {
                "message": f"All documents deleted successfully",
                "deleted_count": stats_before
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete all documents")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting all documents: {str(e)}")


@router.post("/reset", summary="컬렉션 초기화")
async def reset_collection():
    """
    벡터 데이터베이스 컬렉션을 완전히 삭제하고 재생성합니다.
    
    ⚠️ 주의: 이 작업은 되돌릴 수 없습니다! 모든 데이터가 삭제됩니다.
    """
    try:
        # 삭제 전 문서 수 확인
        stats_before = ingest_pipeline.vectorstore.count()
        
        success = ingest_pipeline.reset_collection()
        
        if success:
            return {
                "message": "Collection reset successfully",
                "deleted_count": stats_before
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reset collection")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting collection: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
async def get_document_stats():
    """
    벡터 데이터베이스 통계를 반환합니다.
    """
    try:
        all_docs = ingest_pipeline.get_all_documents()
        total_chunks = len(all_docs)
        
        # 고유한 문서 ID 추출
        document_ids = set()
        for doc in all_docs:
            doc_id = doc.get("metadata", {}).get("document_id")
            if doc_id:
                document_ids.add(doc_id)
        
        total_documents = len(document_ids)
        
        return StatsResponse(
            total_documents=total_documents,
            total_chunks=total_chunks,
            collection_name=settings.collection_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    벡터 검색을 수행합니다.
    """
    try:
        # 쿼리 임베딩 생성
        query_text = request.query
        # multilingual-e5 모델의 경우 "query: " prefix 사용
        if "multilingual-e5" in settings.embedding_model.lower():
            query_text = f"query: {query_text}"
        
        query_embedding = ingest_pipeline.embedder.embed_text(query_text)
        
        # 벡터 검색
        search_results = ingest_pipeline.vectorstore.search(
            query_embedding=query_embedding,
            n_results=request.n_results
        )
        
        # 결과 포맷팅
        results = []
        for i, (doc, distance, metadata, doc_id) in enumerate(zip(
            search_results["documents"],
            search_results["distances"],
            search_results["metadatas"],
            search_results["ids"]
        )):
            results.append({
                "rank": i + 1,
                "document_id": doc_id,
                "text": doc[:200] + "..." if len(doc) > 200 else doc,  # 처음 200자만
                "distance": float(distance),
                "metadata": metadata
            })
        
        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")


@router.post("/upload-markdown", response_model=BulkDocumentResponse)
async def upload_markdown_files(
    files: List[UploadFile] = File(..., description="마크다운 파일들"),
    base_metadata: Optional[str] = Form(None, description="기본 메타데이터 (JSON 문자열)")
):
    """
    마크다운 파일들을 업로드하여 벡터 데이터베이스에 추가합니다.
    
    마크다운 파일을 헤더 기반으로 청킹하여 처리합니다.
    """
    import json
    
    processed_count = 0
    total_chunks = 0
    document_ids = []
    errors = []
    
    # 기본 메타데이터 파싱
    base_meta = {}
    if base_metadata:
        try:
            base_meta = json.loads(base_metadata)
        except json.JSONDecodeError:
            errors.append("Invalid JSON in base_metadata")
    
    for file in files:
        try:
            # 파일 확장자 확인
            if not file.filename.lower().endswith(('.md', '.markdown')):
                errors.append(f"Skipped {file.filename}: Not a markdown file")
                continue
            
            # 파일 읽기
            file_bytes = await file.read()
            
            # 마크다운 파싱
            document = DocumentLoader.load_markdown_from_bytes(
                file_bytes=file_bytes,
                filename=file.filename,
                metadata={**base_meta, "upload_source": "api"}
            )
            
            # Ingest 파이프라인 실행
            result = ingest_pipeline.ingest_text(
                text=document["text"],
                metadata=document["metadata"],
                document_id=document["id"]
            )
            
            processed_count += 1
            total_chunks += result["chunks_count"]
            document_ids.append(result["document_id"])
            
        except Exception as e:
            errors.append(f"Error processing {file.filename}: {str(e)}")
            continue
    
    return BulkDocumentResponse(
        message=f"Processed {processed_count} markdown file(s)",
        total_documents=processed_count,
        total_chunks=total_chunks,
        document_ids=document_ids,
        errors=errors if errors else None
    )


@router.post("/upload-directory", response_model=BulkDocumentResponse)
async def upload_markdown_directory(
    directory_path: str = Form(..., description="마크다운 파일이 있는 디렉토리 경로"),
    pattern: str = Form("*.md", description="파일 패턴 (예: *.md)"),
    base_metadata: Optional[str] = Form(None, description="기본 메타데이터 (JSON 문자열)")
):
    """
    디렉토리 경로를 제공하여 마크다운 파일들을 일괄 처리합니다.
    
    서버에서 접근 가능한 디렉토리 경로를 제공하면 해당 디렉토리의 모든 마크다운 파일을 처리합니다.
    """
    import json
    
    # 기본 메타데이터 파싱
    base_meta = {}
    if base_metadata:
        try:
            base_meta = json.loads(base_metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in base_metadata")
    
    try:
        # 디렉토리에서 마크다운 파일 로드
        documents = DocumentLoader.load_markdown_directory(
            directory_path=directory_path,
            pattern=pattern,
            metadata={**base_meta, "upload_source": "directory"}
        )
        
        if not documents:
            raise HTTPException(status_code=404, detail="No markdown files found in directory")
        
        # 모든 문서 처리
        processed_count = 0
        total_chunks = 0
        document_ids = []
        errors = []
        
        for document in documents:
            try:
                result = ingest_pipeline.ingest_text(
                    text=document["text"],
                    metadata=document["metadata"],
                    document_id=document["id"]
                )
                
                processed_count += 1
                total_chunks += result["chunks_count"]
                document_ids.append(result["document_id"])
                
            except Exception as e:
                errors.append(f"Error processing {document.get('metadata', {}).get('source', 'unknown')}: {str(e)}")
                continue
        
        return BulkDocumentResponse(
            message=f"Processed {processed_count} markdown file(s) from directory",
            total_documents=processed_count,
            total_chunks=total_chunks,
            document_ids=document_ids,
            errors=errors if errors else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing directory: {str(e)}")


@router.get("/chunks", response_model=ChunkListResponse)
async def list_chunks(
    document_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    저장된 모든 청크를 조회합니다.
    
    Args:
        document_id: 특정 문서의 청크만 조회 (선택적)
        limit: 반환할 최대 청크 수 (기본값: 100)
        offset: 건너뛸 청크 수 (기본값: 0)
    """
    try:
        all_docs = ingest_pipeline.get_all_documents()
        
        chunks = []
        for doc in all_docs:
            # document_id 필터링
            if document_id:
                doc_metadata = doc.get("metadata", {})
                if doc_metadata.get("document_id") != document_id:
                    continue
            
            chunks.append(ChunkResponse(
                chunk_id=doc.get("id", ""),
                text=doc.get("text", ""),
                metadata=doc.get("metadata", {})
            ))
        
        # 페이징 적용
        total = len(chunks)
        paginated_chunks = chunks[offset:offset + limit]
        
        return ChunkListResponse(
            chunks=paginated_chunks,
            total=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing chunks: {str(e)}")


@router.get("/chunks/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(chunk_id: str):
    """
    특정 청크 ID로 청크를 조회합니다.
    
    Args:
        chunk_id: 조회할 청크 ID
    """
    try:
        all_docs = ingest_pipeline.get_all_documents()
        
        for doc in all_docs:
            if doc.get("id") == chunk_id:
                return ChunkResponse(
                    chunk_id=doc.get("id", ""),
                    text=doc.get("text", ""),
                    metadata=doc.get("metadata", {})
                )
        
        raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chunk: {str(e)}")


@router.get("/{document_id}/chunks", response_model=ChunkListResponse)
async def get_document_chunks(document_id: str):
    """
    특정 문서의 모든 청크를 조회합니다.
    
    Args:
        document_id: 조회할 문서 ID
    """
    try:
        all_docs = ingest_pipeline.get_all_documents()
        
        chunks = []
        for doc in all_docs:
            doc_metadata = doc.get("metadata", {})
            if doc_metadata.get("document_id") == document_id:
                chunks.append(ChunkResponse(
                    chunk_id=doc.get("id", ""),
                    text=doc.get("text", ""),
                    metadata=doc_metadata
                ))
        
        if not chunks:
            raise HTTPException(status_code=404, detail=f"No chunks found for document {document_id}")
        
        return ChunkListResponse(
            chunks=chunks,
            total=len(chunks)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document chunks: {str(e)}")

