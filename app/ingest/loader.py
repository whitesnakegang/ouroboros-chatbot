"""
문서 로더 모듈
"""
from typing import List, Dict, Any, Optional
import uuid
import os
from bs4 import BeautifulSoup
from pathlib import Path


class DocumentLoader:
    """문서 로딩 및 전처리"""
    
    @staticmethod
    def load_text(text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        텍스트를 문서 형식으로 로드
        
        Args:
            text: 문서 텍스트
            metadata: 문서 메타데이터
            
        Returns:
            문서 딕셔너리
        """
        if metadata is None:
            metadata = {}
        
        return {
            "id": metadata.get("document_id") or str(uuid.uuid4()),
            "text": text.strip(),
            "metadata": metadata
        }
    
    @staticmethod
    def load_from_file(file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        파일에서 문서 로드
        
        Args:
            file_path: 파일 경로
            metadata: 문서 메타데이터
            
        Returns:
            문서 딕셔너리
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            if metadata is None:
                metadata = {}
            
            metadata["source"] = file_path
            metadata["document_id"] = metadata.get("document_id") or str(uuid.uuid4())
            
            return DocumentLoader.load_text(text, metadata)
        except Exception as e:
            raise ValueError(f"Error loading file {file_path}: {e}")
    
    @staticmethod
    def load_multiple_texts(
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        여러 텍스트를 문서 형식으로 로드
        
        Args:
            texts: 텍스트 리스트
            metadatas: 메타데이터 리스트
            
        Returns:
            문서 딕셔너리 리스트
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        documents = []
        for text, metadata in zip(texts, metadatas):
            documents.append(DocumentLoader.load_text(text, metadata))
        
        return documents
    
    @staticmethod
    def load_html(html_content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        HTML 콘텐츠에서 텍스트 추출
        
        Args:
            html_content: HTML 문자열
            metadata: 문서 메타데이터
            
        Returns:
            문서 딕셔너리
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 스크립트와 스타일 태그 제거
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # 메타데이터 추출
            title = ""
            if soup.title:
                title = soup.title.get_text().strip()
            elif soup.find("meta", property="og:title"):
                title = soup.find("meta", property="og:title").get("content", "")
            
            # 메인 콘텐츠 추출 (main, article, 또는 body)
            content_selectors = ["main", "article", "[role='main']", "body"]
            text_content = ""
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    text_content = element.get_text(separator="\n", strip=True)
                    break
            
            # 선택자가 없으면 body 전체 사용
            if not text_content:
                text_content = soup.get_text(separator="\n", strip=True)
            
            # 텍스트 정리 (여러 공백/줄바꿈 정리)
            lines = [line.strip() for line in text_content.split("\n") if line.strip()]
            cleaned_text = "\n".join(lines)
            
            if metadata is None:
                metadata = {}
            
            # 메타데이터에 HTML 정보 추가
            metadata["source_type"] = "html"
            if title:
                metadata["title"] = title
            if soup.find("meta", property="og:url"):
                metadata["url"] = soup.find("meta", property="og:url").get("content", "")
            
            return DocumentLoader.load_text(cleaned_text, metadata)
        except Exception as e:
            raise ValueError(f"Error parsing HTML: {e}")
    
    @staticmethod
    def load_html_file(file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        HTML 파일에서 텍스트 추출
        
        Args:
            file_path: HTML 파일 경로
            metadata: 문서 메타데이터
            
        Returns:
            문서 딕셔너리
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            if metadata is None:
                metadata = {}
            
            metadata["source"] = file_path
            metadata["filename"] = os.path.basename(file_path)
            
            return DocumentLoader.load_html(html_content, metadata)
        except Exception as e:
            raise ValueError(f"Error loading HTML file {file_path}: {e}")
    
    @staticmethod
    def load_html_from_bytes(
        file_bytes: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        바이트 데이터에서 HTML 파싱
        
        Args:
            file_bytes: HTML 파일 바이트
            filename: 파일명
            metadata: 문서 메타데이터
            
        Returns:
            문서 딕셔너리
        """
        try:
            html_content = file_bytes.decode("utf-8")
            
            if metadata is None:
                metadata = {}
            
            metadata["filename"] = filename
            metadata["source"] = f"uploaded:{filename}"
            
            return DocumentLoader.load_html(html_content, metadata)
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            try:
                html_content = file_bytes.decode("latin-1")
                if metadata is None:
                    metadata = {}
                metadata["filename"] = filename
                metadata["source"] = f"uploaded:{filename}"
                return DocumentLoader.load_html(html_content, metadata)
            except Exception as e:
                raise ValueError(f"Error decoding HTML file {filename}: {e}")
        except Exception as e:
            raise ValueError(f"Error processing HTML file {filename}: {e}")
    
    @staticmethod
    def load_html_directory(
        directory_path: str,
        pattern: str = "*.html",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        디렉토리에서 모든 HTML 파일 로드
        
        Args:
            directory_path: 디렉토리 경로
            pattern: 파일 패턴 (기본값: *.html)
            metadata: 기본 메타데이터
            
        Returns:
            문서 딕셔너리 리스트
        """
        documents = []
        path = Path(directory_path)
        
        if not path.exists():
            raise ValueError(f"Directory not found: {directory_path}")
        
        html_files = list(path.rglob(pattern))
        
        if not html_files:
            raise ValueError(f"No HTML files found in {directory_path}")
        
        for html_file in html_files:
            file_metadata = metadata.copy() if metadata else {}
            file_metadata["relative_path"] = str(html_file.relative_to(path))
            
            try:
                doc = DocumentLoader.load_html_file(str(html_file), file_metadata)
                documents.append(doc)
            except Exception as e:
                print(f"Warning: Failed to load {html_file}: {e}")
                continue
        
        return documents
    
    @staticmethod
    def load_markdown_file(file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        마크다운 파일에서 문서 로드
        
        Args:
            file_path: 마크다운 파일 경로
            metadata: 문서 메타데이터
            
        Returns:
            문서 딕셔너리
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            if metadata is None:
                metadata = {}
            
            metadata["source"] = file_path
            metadata["filename"] = os.path.basename(file_path)
            metadata["source_type"] = "markdown"
            metadata["document_id"] = metadata.get("document_id") or str(uuid.uuid4())
            
            return DocumentLoader.load_text(text, metadata)
        except Exception as e:
            raise ValueError(f"Error loading markdown file {file_path}: {e}")
    
    @staticmethod
    def load_markdown_from_bytes(
        file_bytes: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        바이트 데이터에서 마크다운 파싱
        
        Args:
            file_bytes: 마크다운 파일 바이트
            filename: 파일명
            metadata: 문서 메타데이터
            
        Returns:
            문서 딕셔너리
        """
        try:
            text = file_bytes.decode("utf-8")
            
            if metadata is None:
                metadata = {}
            
            metadata["filename"] = filename
            metadata["source"] = f"uploaded:{filename}"
            metadata["source_type"] = "markdown"
            
            return DocumentLoader.load_text(text, metadata)
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            try:
                text = file_bytes.decode("latin-1")
                if metadata is None:
                    metadata = {}
                metadata["filename"] = filename
                metadata["source"] = f"uploaded:{filename}"
                metadata["source_type"] = "markdown"
                return DocumentLoader.load_text(text, metadata)
            except Exception as e:
                raise ValueError(f"Error decoding markdown file {filename}: {e}")
        except Exception as e:
            raise ValueError(f"Error processing markdown file {filename}: {e}")
    
    @staticmethod
    def load_markdown_directory(
        directory_path: str,
        pattern: str = "*.md",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        디렉토리에서 모든 마크다운 파일 로드
        
        Args:
            directory_path: 디렉토리 경로
            pattern: 파일 패턴 (기본값: *.md)
            metadata: 기본 메타데이터
            
        Returns:
            문서 딕셔너리 리스트
        """
        documents = []
        path = Path(directory_path)
        
        if not path.exists():
            raise ValueError(f"Directory not found: {directory_path}")
        
        md_files = list(path.rglob(pattern))
        
        if not md_files:
            raise ValueError(f"No markdown files found in {directory_path}")
        
        for md_file in md_files:
            file_metadata = metadata.copy() if metadata else {}
            file_metadata["relative_path"] = str(md_file.relative_to(path))
            
            try:
                doc = DocumentLoader.load_markdown_file(str(md_file), file_metadata)
                documents.append(doc)
            except Exception as e:
                print(f"Warning: Failed to load {md_file}: {e}")
                continue
        
        return documents

