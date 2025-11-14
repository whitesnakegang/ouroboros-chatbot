"""
ChromaDB 벡터 스토어 관리
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import os
from app.config import settings

# 텔레메트리 비활성화
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


class ChromaVectorStore:
    """ChromaDB를 사용한 벡터 스토어"""
    
    def __init__(self, collection_name: Optional[str] = None):
        """
        ChromaDB 벡터 스토어 초기화
        
        Args:
            collection_name: 컬렉션 이름 (기본값: settings.collection_name)
        """
        self.collection_name = collection_name or settings.collection_name
        self.db_path = settings.chroma_db_path
        
        # 디렉토리 생성
        os.makedirs(self.db_path, exist_ok=True)
        
        # ChromaDB 클라이언트 초기화
        # 텔레메트리 완전히 비활성화
        chroma_settings = ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True
        )
        
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=chroma_settings
        )
        
        # 컬렉션 가져오기 또는 생성
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """컬렉션 가져오기 또는 생성"""
        try:
            return self.client.get_collection(name=self.collection_name)
        except Exception:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG Chatbot document collection"}
            )
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        문서를 벡터 스토어에 추가
        
        Args:
            texts: 문서 텍스트 리스트
            embeddings: 임베딩 벡터 리스트
            metadatas: 메타데이터 리스트
            ids: 문서 ID 리스트 (없으면 자동 생성)
            
        Returns:
            저장된 문서 ID 리스트
        """
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # ChromaDB에 추가
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        유사한 문서 검색
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            n_results: 반환할 결과 수
            filter_metadata: 메타데이터 필터
            
        Returns:
            검색 결과 딕셔너리 (documents, distances, metadatas, ids)
        """
        where = filter_metadata if filter_metadata else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        모든 문서 조회
        
        Returns:
            문서 리스트
        """
        results = self.collection.get()
        
        documents = []
        for i, doc_id in enumerate(results["ids"]):
            documents.append({
                "id": doc_id,
                "text": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {}
            })
        
        return documents
    
    def delete_documents(self, ids: List[str]) -> bool:
        """
        문서 삭제
        
        Args:
            ids: 삭제할 문서 ID 리스트
            
        Returns:
            성공 여부
        """
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    def count(self) -> int:
        """
        저장된 문서 수 반환
        
        Returns:
            문서 수
        """
        return self.collection.count()


