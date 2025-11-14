"""
문서 청킹 모듈
"""
import re
from typing import List, Dict, Any, Tuple
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
    
    def chunk_markdown(
        self,
        text: str,
        preserve_headers: bool = True
    ) -> List[Dict[str, Any]]:
        """
        마크다운 텍스트를 헤더 기반으로 청킹
        
        Args:
            text: 마크다운 텍스트
            preserve_headers: 헤더를 각 청크에 포함할지 여부
            
        Returns:
            청크 딕셔너리 리스트 (text, header, level 포함)
        """
        if not text.strip():
            return []
        
        # 헤더 패턴 찾기 (#으로 시작하는 줄)
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        # 헤더 위치 찾기
        headers = []
        for match in header_pattern.finditer(text):
            level = len(match.group(1))
            header_text = match.group(2).strip()
            position = match.start()
            headers.append((position, level, header_text))
        
        # 헤더가 없으면 일반 텍스트 청킹
        if not headers:
            chunks = self.chunk_text(text)
            return [
                {
                    "text": chunk,
                    "header": None,
                    "level": None,
                    "is_code_block": False
                }
                for chunk in chunks
            ]
        
        chunks = []
        header_stack = []  # 현재 헤더 경로 추적
        
        # 첫 번째 헤더 이전의 텍스트 처리
        if headers and headers[0][0] > 0:
            intro_text = text[:headers[0][0]].strip()
            if intro_text:
                intro_chunks = self.chunk_text(intro_text)
                for chunk in intro_chunks:
                    chunks.append({
                        "text": chunk,
                        "header": None,
                        "level": None,
                        "header_path": None,
                        "is_code_block": False
                    })
        
        for i, (pos, level, header_text) in enumerate(headers):
            # 현재 섹션의 시작 위치
            start_pos = pos
            
            # 다음 헤더 또는 문서 끝까지가 현재 섹션
            if i + 1 < len(headers):
                end_pos = headers[i + 1][0]
            else:
                end_pos = len(text)
            
            # 헤더 스택 업데이트 (같은 레벨 이하의 헤더 제거)
            header_stack = [h for h in header_stack if h[1] < level]
            header_stack.append((header_text, level))
            
            # 섹션 텍스트 추출
            section_text = text[start_pos:end_pos].strip()
            
            # 코드 블록 처리
            code_blocks = self._extract_code_blocks(section_text)
            
            if code_blocks:
                # 코드 블록과 일반 텍스트를 분리
                parts = self._split_code_and_text(section_text, code_blocks)
                
                for part_type, part_text in parts:
                    if part_type == "code":
                        # 코드 블록은 하나의 청크로 유지
                        chunk_text = part_text
                        if preserve_headers and header_stack:
                            header_path = " > ".join([h[0] for h in header_stack])
                            chunk_text = f"## {header_path}\n\n{chunk_text}"
                        
                        chunks.append({
                            "text": chunk_text,
                            "header": header_stack[-1][0] if header_stack else None,
                            "level": level,
                            "header_path": " > ".join([h[0] for h in header_stack]) if header_stack else None,
                            "is_code_block": True
                        })
                    else:
                        # 일반 텍스트는 크기에 따라 분할
                        if len(part_text) <= self.chunk_size:
                            chunk_text = part_text
                            if preserve_headers and header_stack:
                                header_path = " > ".join([h[0] for h in header_stack])
                                chunk_text = f"## {header_path}\n\n{chunk_text}"
                            
                            chunks.append({
                                "text": chunk_text,
                                "header": header_stack[-1][0] if header_stack else None,
                                "level": level,
                                "header_path": " > ".join([h[0] for h in header_stack]) if header_stack else None,
                                "is_code_block": False
                            })
                        else:
                            # 큰 텍스트는 하위 청킹
                            sub_chunks = self.chunk_text(part_text)
                            for sub_chunk in sub_chunks:
                                chunk_text = sub_chunk
                                if preserve_headers and header_stack:
                                    header_path = " > ".join([h[0] for h in header_stack])
                                    chunk_text = f"## {header_path}\n\n{chunk_text}"
                                
                                chunks.append({
                                    "text": chunk_text,
                                    "header": header_stack[-1][0] if header_stack else None,
                                    "level": level,
                                    "header_path": " > ".join([h[0] for h in header_stack]) if header_stack else None,
                                    "is_code_block": False
                                })
            else:
                # 코드 블록이 없는 경우
                if len(section_text) <= self.chunk_size:
                    chunk_text = section_text
                    chunks.append({
                        "text": chunk_text,
                        "header": header_stack[-1][0] if header_stack else None,
                        "level": level,
                        "header_path": " > ".join([h[0] for h in header_stack]) if header_stack else None,
                        "is_code_block": False
                    })
                else:
                    # 큰 섹션은 하위 청킹
                    sub_chunks = self.chunk_text(section_text)
                    for sub_chunk in sub_chunks:
                        chunk_text = sub_chunk
                        if preserve_headers and header_stack:
                            header_path = " > ".join([h[0] for h in header_stack])
                            chunk_text = f"## {header_path}\n\n{chunk_text}"
                        
                        chunks.append({
                            "text": chunk_text,
                            "header": header_stack[-1][0] if header_stack else None,
                            "level": level,
                            "header_path": " > ".join([h[0] for h in header_stack]) if header_stack else None,
                            "is_code_block": False
                        })
        
        return chunks
    
    def _extract_code_blocks(self, text: str) -> List[Tuple[int, int, str]]:
        """
        텍스트에서 코드 블록 위치 추출
        
        Returns:
            (시작 위치, 끝 위치, 코드 블록 텍스트) 튜플 리스트
        """
        code_blocks = []
        pattern = re.compile(r'```[\s\S]*?```', re.MULTILINE)
        
        for match in pattern.finditer(text):
            code_blocks.append((match.start(), match.end(), match.group(0)))
        
        return code_blocks
    
    def _split_code_and_text(
        self,
        text: str,
        code_blocks: List[Tuple[int, int, str]]
    ) -> List[Tuple[str, str]]:
        """
        텍스트를 코드 블록과 일반 텍스트로 분리
        
        Returns:
            ("code" 또는 "text", 텍스트) 튜플 리스트
        """
        parts = []
        last_pos = 0
        
        for start, end, code_text in code_blocks:
            # 코드 블록 이전의 일반 텍스트
            if start > last_pos:
                text_part = text[last_pos:start].strip()
                if text_part:
                    parts.append(("text", text_part))
            
            # 코드 블록
            parts.append(("code", code_text))
            last_pos = end
        
        # 마지막 코드 블록 이후의 일반 텍스트
        if last_pos < len(text):
            text_part = text[last_pos:].strip()
            if text_part:
                parts.append(("text", text_part))
        
        return parts
    
    def chunk_markdown_document(
        self,
        document: Dict[str, Any],
        preserve_metadata: bool = True,
        preserve_headers: bool = True
    ) -> List[Dict[str, Any]]:
        """
        마크다운 문서를 청크로 분할하고 메타데이터 유지
        
        Args:
            document: 문서 딕셔너리 (id, text, metadata 포함)
            preserve_metadata: 메타데이터 보존 여부
            preserve_headers: 헤더를 각 청크에 포함할지 여부
            
        Returns:
            청크 딕셔너리 리스트
        """
        text = document.get("text", "")
        chunks = self.chunk_markdown(text, preserve_headers=preserve_headers)
        
        chunk_documents = []
        for i, chunk_info in enumerate(chunks):
            chunk_doc = {
                "text": chunk_info["text"],
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            if preserve_metadata:
                chunk_doc["document_id"] = document.get("id")
                chunk_doc["metadata"] = document.get("metadata", {}).copy()
                chunk_doc["metadata"]["chunk_index"] = i
                chunk_doc["metadata"]["total_chunks"] = len(chunks)
                chunk_doc["metadata"]["header"] = chunk_info.get("header")
                chunk_doc["metadata"]["header_level"] = chunk_info.get("level")
                chunk_doc["metadata"]["header_path"] = chunk_info.get("header_path")
                chunk_doc["metadata"]["is_code_block"] = chunk_info.get("is_code_block", False)
            else:
                chunk_doc["metadata"] = {}
            
            chunk_documents.append(chunk_doc)
        
        return chunk_documents


