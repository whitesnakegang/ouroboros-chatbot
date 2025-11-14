"""
문서 처리 파이프라인
"""
from typing import List, Dict, Any, Optional
from app.ingest.loader import DocumentLoader
from app.ingest.chunker import DocumentChunker
from app.ingest.embedder import Embedder
from app.vectorstore.chroma import ChromaVectorStore


class IngestPipeline:
    """문서 수집 및 처리 파이프라인"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        embedding_model: str = None,
        collection_name: str = None
    ):
        """
        파이프라인 초기화
        
        Args:
            chunk_size: 청크 크기
            chunk_overlap: 청크 오버랩
            embedding_model: 임베딩 모델 이름
            collection_name: 벡터 스토어 컬렉션 이름
        """
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embedder = Embedder(model_name=embedding_model)
        self.vectorstore = ChromaVectorStore(collection_name=collection_name)
    
    def ingest_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        텍스트를 수집하고 벡터 스토어에 저장
        
        Args:
            text: 문서 텍스트
            metadata: 문서 메타데이터
            document_id: 문서 ID (없으면 자동 생성)
            
        Returns:
            처리 결과 딕셔너리
        """
        # 1. 문서 로드
        if metadata is None:
            metadata = {}
        if document_id:
            metadata["document_id"] = document_id
        
        document = self.loader.load_text(text, metadata)
        
        # 2. 문서 청킹 (마크다운으로 처리)
        chunks = self.chunker.chunk_markdown_document(
            document,
            preserve_metadata=True,
            preserve_headers=True
        )
        
        if not chunks:
            raise ValueError("No chunks created from document")
        
        # 3. 임베딩 생성
        chunk_texts = [chunk["text"] for chunk in chunks]
        # multilingual-e5 모델의 경우 "passage: " prefix 사용
        instruction = "passage: " if "multilingual-e5" in self.embedder.model_name.lower() else None
        embeddings = self.embedder.embed_texts(chunk_texts, instruction=instruction)
        
        # 4. 메타데이터 준비
        chunk_metadatas = [chunk["metadata"] for chunk in chunks]
        
        # 5. 청크 ID 생성
        import uuid
        chunk_ids = [
            f"{document['id']}_chunk_{i}" for i in range(len(chunks))
        ]
        
        # 6. 벡터 스토어에 저장
        stored_ids = self.vectorstore.add_documents(
            texts=chunk_texts,
            embeddings=embeddings,
            metadatas=chunk_metadatas,
            ids=chunk_ids
        )
        
        return {
            "document_id": document["id"],
            "chunks_count": len(chunks),
            "chunk_ids": stored_ids,
            "message": f"Successfully ingested document with {len(chunks)} chunks"
        }
    
    def ingest_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        여러 문서를 수집하고 벡터 스토어에 저장
        
        Args:
            documents: 문서 딕셔너리 리스트 (text, metadata 포함)
            
        Returns:
            처리 결과 리스트
        """
        results = []
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            document_id = doc.get("id")
            
            result = self.ingest_text(text, metadata, document_id)
            results.append(result)
        
        return results
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        저장된 모든 문서 조회
        
        Returns:
            문서 리스트
        """
        return self.vectorstore.get_all_documents()
    
    def delete_document(self, document_id: str) -> bool:
        """
        문서 삭제 (모든 청크 포함)
        
        Args:
            document_id: 삭제할 문서 ID
            
        Returns:
            성공 여부
        """
        # 해당 문서의 모든 청크 찾기
        all_docs = self.vectorstore.get_all_documents()
        chunk_ids = [
            doc["id"] for doc in all_docs
            if doc.get("metadata", {}).get("document_id") == document_id
        ]
        
        if chunk_ids:
            return self.vectorstore.delete_documents(chunk_ids)
        return False

