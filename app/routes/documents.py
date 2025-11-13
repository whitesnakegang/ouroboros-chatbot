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
    StatsResponse
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


@router.post("/upload-html", response_model=BulkDocumentResponse)
async def upload_html_files(
    files: List[UploadFile] = File(..., description="HTML 파일들"),
    base_metadata: Optional[str] = Form(None, description="기본 메타데이터 (JSON 문자열)")
):
    """
    HTML 파일들을 업로드하여 벡터 데이터베이스에 추가합니다.
    
    React 정적 웹 파일 형식의 HTML 파일들을 받아서 처리합니다.
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
            if not file.filename.lower().endswith(('.html', '.htm')):
                errors.append(f"Skipped {file.filename}: Not an HTML file")
                continue
            
            # 파일 읽기
            file_bytes = await file.read()
            
            # HTML 파싱
            document = DocumentLoader.load_html_from_bytes(
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
        message=f"Processed {processed_count} HTML file(s)",
        total_documents=processed_count,
        total_chunks=total_chunks,
        document_ids=document_ids,
        errors=errors if errors else None
    )


@router.post("/upload-directory", response_model=BulkDocumentResponse)
async def upload_html_directory(
    directory_path: str = Form(..., description="HTML 파일이 있는 디렉토리 경로"),
    pattern: str = Form("*.html", description="파일 패턴 (예: *.html)"),
    base_metadata: Optional[str] = Form(None, description="기본 메타데이터 (JSON 문자열)")
):
    """
    디렉토리 경로를 제공하여 HTML 파일들을 일괄 처리합니다.
    
    서버에서 접근 가능한 디렉토리 경로를 제공하면 해당 디렉토리의 모든 HTML 파일을 처리합니다.
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
        # 디렉토리에서 HTML 파일 로드
        documents = DocumentLoader.load_html_directory(
            directory_path=directory_path,
            pattern=pattern,
            metadata={**base_meta, "upload_source": "directory"}
        )
        
        if not documents:
            raise HTTPException(status_code=404, detail="No HTML files found in directory")
        
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
            message=f"Processed {processed_count} HTML file(s) from directory",
            total_documents=processed_count,
            total_chunks=total_chunks,
            document_ids=document_ids,
            errors=errors if errors else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing directory: {str(e)}")

