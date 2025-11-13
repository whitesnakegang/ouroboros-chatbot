"""
임베딩 모듈
"""
from typing import List
from sentence_transformers import SentenceTransformer
import torch
from app.config import settings


class Embedder:
    """문서 임베딩 생성"""
    
    def __init__(
        self,
        model_name: str = None,
        device: str = None
    ):
        """
        임베딩 모델 초기화
        
        Args:
            model_name: 임베딩 모델 이름 (기본값: settings.embedding_model)
            device: 사용할 디바이스 (기본값: settings.embedding_device)
        """
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        
        # GPU 사용 가능 여부 확인
        if self.device == "cuda" and not torch.cuda.is_available():
            print("CUDA not available, using CPU")
            self.device = "cpu"
        
        print(f"Loading embedding model: {self.model_name} on {self.device}")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        print("Embedding model loaded successfully")
    
    def embed_text(self, text: str, instruction: str = None) -> List[float]:
        """
        단일 텍스트 임베딩
        
        Args:
            text: 임베딩할 텍스트
            instruction: instruction prefix (multilingual-e5 모델의 경우 "passage: " 또는 "query: " 사용)
            
        Returns:
            임베딩 벡터
        """
        # multilingual-e5 모델의 경우 instruction prefix 추가
        if instruction and "multilingual-e5" in self.model_name.lower():
            text = f"{instruction} {text}"
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str], instruction: str = None) -> List[List[float]]:
        """
        여러 텍스트 임베딩 (배치 처리)
        
        Args:
            texts: 임베딩할 텍스트 리스트
            instruction: instruction prefix (multilingual-e5 모델의 경우 "passage: " 또는 "query: " 사용)
            
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []
        
        # multilingual-e5 모델의 경우 instruction prefix 추가
        if instruction and "multilingual-e5" in self.model_name.lower():
            texts = [f"{instruction} {text}" for text in texts]
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 10
        )
        
        return embeddings.tolist()
    
    def embed_documents(self, documents: List[dict], instruction: str = "passage: ") -> List[List[float]]:
        """
        문서 리스트 임베딩
        
        Args:
            documents: 문서 딕셔너리 리스트 (text 키 포함)
            instruction: instruction prefix (multilingual-e5 모델의 경우 "passage: " 사용)
            
        Returns:
            임베딩 벡터 리스트
        """
        texts = [doc.get("text", "") for doc in documents]
        return self.embed_texts(texts, instruction=instruction)

