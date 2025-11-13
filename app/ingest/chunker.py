"""
문서 청킹 모듈
"""
from typing import List, Dict, Any
from app.config import settings


class DocumentChunker:
    """문서를 청크로 분할"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        청커 초기화
        
        Args:
            chunk_size: 청크 크기 (기본값: settings.chunk_size)
            chunk_overlap: 청크 오버랩 크기 (기본값: settings.chunk_overlap)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            청크 리스트
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 마지막 청크인 경우
            if end >= len(text):
                chunks.append(text[start:].strip())
                break
            
            # 문장 경계에서 자르기 시도
            # 마지막 마침표, 느낌표, 물음표 위치 찾기
            last_punctuation = max(
                text.rfind(".", start, end),
                text.rfind("!", start, end),
                text.rfind("?", start, end),
                text.rfind("\n", start, end)
            )
            
            if last_punctuation > start:
                end = last_punctuation + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 오버랩을 고려한 다음 시작 위치
            start = end - self.chunk_overlap
        
        return chunks
    
    def chunk_document(
        self,
        document: Dict[str, Any],
        preserve_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        문서를 청크로 분할하고 메타데이터 유지
        
        Args:
            document: 문서 딕셔너리 (id, text, metadata 포함)
            preserve_metadata: 메타데이터 보존 여부
            
        Returns:
            청크 딕셔너리 리스트
        """
        text = document.get("text", "")
        chunks = self.chunk_text(text)
        
        chunk_documents = []
        for i, chunk_text in enumerate(chunks):
            chunk_doc = {
                "text": chunk_text,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            if preserve_metadata:
                chunk_doc["document_id"] = document.get("id")
                chunk_doc["metadata"] = document.get("metadata", {}).copy()
                chunk_doc["metadata"]["chunk_index"] = i
                chunk_doc["metadata"]["total_chunks"] = len(chunks)
            else:
                chunk_doc["metadata"] = {}
            
            chunk_documents.append(chunk_doc)
        
        return chunk_documents
    
    def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        preserve_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        여러 문서를 청크로 분할
        
        Args:
            documents: 문서 딕셔너리 리스트
            preserve_metadata: 메타데이터 보존 여부
            
        Returns:
            청크 딕셔너리 리스트
        """
        all_chunks = []
        for document in documents:
            chunks = self.chunk_document(document, preserve_metadata)
            all_chunks.extend(chunks)
        
        return all_chunks


