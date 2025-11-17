"""
세션 관리 모듈
대화 히스토리를 메모리에 저장하고 관리
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """세션별 대화 히스토리 관리"""
    
    def __init__(self, max_history: int = 10):
        """
        세션 매니저 초기화
        
        Args:
            max_history: 세션당 최대 대화 수 (기본값: 10)
        """
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        self.summaries: Dict[str, str] = {}  # 세션별 요약된 컨텍스트
        self.max_history = max_history
    
    def create_session(self) -> str:
        """
        새 세션 생성
        
        Returns:
            세션 ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        self.summaries[session_id] = ""
        logger.info(f"[SessionManager] 새 세션 생성: {session_id}")
        return session_id
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        세션의 대화 히스토리 반환
        
        Args:
            session_id: 세션 ID
            
        Returns:
            대화 히스토리 리스트
        """
        return self.sessions.get(session_id, [])
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """
        세션에 메시지 추가
        
        Args:
            session_id: 세션 ID
            role: 메시지 역할 ("user" 또는 "assistant")
            content: 메시지 내용
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.sessions[session_id].append(message)
        
        # 최대 대화 수 제한 (오래된 대화 삭제)
        if len(self.sessions[session_id]) > self.max_history * 2:  # user + assistant = 2개씩
            # 최근 max_history * 2개만 유지
            self.sessions[session_id] = self.sessions[session_id][-self.max_history * 2:]
        
        logger.debug(f"[SessionManager] 메시지 추가 - 세션: {session_id}, 역할: {role}")
    
    def clear_session(self, session_id: str) -> bool:
        """
        세션 초기화
        
        Args:
            session_id: 세션 ID
            
        Returns:
            성공 여부
        """
        if session_id in self.sessions:
            self.sessions[session_id] = []
            if session_id in self.summaries:
                del self.summaries[session_id]
            logger.info(f"[SessionManager] 세션 초기화: {session_id}")
            return True
        return False
    
    def get_summary(self, session_id: str) -> Optional[str]:
        """
        세션의 요약된 컨텍스트 반환
        
        Args:
            session_id: 세션 ID
            
        Returns:
            요약된 컨텍스트 또는 None
        """
        return self.summaries.get(session_id)
    
    def set_summary(self, session_id: str, summary: str) -> None:
        """
        세션의 요약된 컨텍스트 설정
        
        Args:
            session_id: 세션 ID
            summary: 요약된 컨텍스트
        """
        self.summaries[session_id] = summary
        logger.debug(f"[SessionManager] 세션 요약 업데이트: {session_id}")
    
    def clear_summary(self, session_id: str) -> None:
        """
        세션의 요약된 컨텍스트 삭제
        
        Args:
            session_id: 세션 ID
        """
        if session_id in self.summaries:
            del self.summaries[session_id]
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """
        세션 ID가 있으면 반환, 없으면 새로 생성
        제공된 session_id가 있지만 세션에 없으면 해당 ID로 새 세션 생성
        
        Args:
            session_id: 세션 ID (선택적)
            
        Returns:
            세션 ID
        """
        if session_id:
            if session_id in self.sessions:
                return session_id
            else:
                # 제공된 session_id로 새 세션 생성
                self.sessions[session_id] = []
                self.summaries[session_id] = ""
                logger.info(f"[SessionManager] 제공된 세션 ID로 새 세션 생성: {session_id}")
                return session_id
        return self.create_session()


