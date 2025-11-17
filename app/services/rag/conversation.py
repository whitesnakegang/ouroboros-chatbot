"""
대화 및 히스토리 관리 모듈
대화 히스토리 요약 및 메시지 구성
"""
import logging
from typing import List, Dict, Any, Optional
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class HistorySummarizer:
    """대화 히스토리 요약기"""
    
    def __init__(self, llm: Any):
        """
        히스토리 요약기 초기화
        
        Args:
            llm: LangChain LLM 인스턴스
        """
        self.llm = llm
    
    def summarize(
        self,
        history: List[Dict[str, Any]],
        recent_count: int = 2
    ) -> str:
        """
        대화 히스토리를 요약
        
        Args:
            history: 대화 히스토리 리스트
            recent_count: 최근 몇 개의 대화는 제외하고 요약할지 (기본값: 2)
            
        Returns:
            요약된 텍스트
        """
        logger.info(f"[HistorySummarizer.summarize] 호출됨 - history 개수: {len(history) if history else 0}, recent_count: {recent_count}")
        
        if not history or len(history) <= recent_count * 2:
            logger.warning(f"[HistorySummarizer.summarize] 요약 불필요 - history: {len(history) if history else 0}개, recent_count*2: {recent_count * 2}")
            return ""
        
        # 최근 대화는 제외하고 요약할 부분만 추출
        to_summarize = history[:-(recent_count * 2)] if recent_count > 0 else history
        logger.info(f"[HistorySummarizer.summarize] 요약 대상 추출 - to_summarize: {len(to_summarize)}개 메시지")
        
        # 대화를 텍스트로 변환
        conversation_text = ""
        for i, msg in enumerate(to_summarize):
            role = msg.get("role", "")
            content = msg.get("content", "")
            logger.debug(f"[HistorySummarizer.summarize] 메시지 {i+1}: role={role}, content 길이={len(content) if content else 0}")
            
            if role == "user":
                conversation_text += f"사용자: {content}\n"
            elif role == "assistant":
                conversation_text += f"챗봇: {content}\n"
            else:
                # system 메시지 등은 그대로 추가
                conversation_text += f"{role}: {content}\n"
        
        logger.info(f"[HistorySummarizer.summarize] conversation_text 생성 완료 - 길이: {len(conversation_text)} 문자")
        
        if not conversation_text.strip():
            logger.warning(f"[HistorySummarizer.summarize] conversation_text가 비어있음 - 원본 메시지: {to_summarize}")
            return ""
        
        # LLM을 사용하여 요약
        try:
            summary_prompt = f"""다음 대화 히스토리를 간결하게 요약해주세요. 
중요한 정보(사용자 이름, 설정, 선호사항, 언급된 주요 내용 등)는 반드시 포함해주세요.

대화 히스토리:
{conversation_text}

요약:"""
            
            summary_messages = [
                SystemMessage(content="당신은 대화 히스토리를 요약하는 역할입니다. 핵심 정보만 간결하게 요약해주세요."),
                HumanMessage(content=summary_prompt)
            ]
            
            logger.info(f"[HistorySummarizer] 요약 LLM 호출 시작 - 대상: {len(to_summarize)}개 메시지, 텍스트 길이: {len(conversation_text)} 문자")
            result = self.llm.invoke(summary_messages)
            
            logger.info(f"[HistorySummarizer] 요약 LLM 호출 완료 - result 타입: {type(result)}")
            
            if isinstance(result, AIMessage):
                summary = result.content
            elif hasattr(result, 'content'):
                summary = result.content
            else:
                summary = str(result)
            
            logger.info(f"[HistorySummarizer] 요약 추출 - summary 길이: {len(summary) if summary else 0} 문자, summary: '{summary[:100] if summary else ''}...'")
            
            if summary and summary.strip():
                logger.info(
                    f"[HistorySummarizer] ✅ 히스토리 요약 성공 - "
                    f"원본: {len(to_summarize)}개 메시지, "
                    f"요약 길이: {len(summary)} 문자, "
                    f"요약 미리보기: {summary[:100]}..."
                )
                return summary.strip()
            else:
                logger.warning(f"[HistorySummarizer] ⚠️ 빈 요약 반환 - 원본: {len(to_summarize)}개 메시지, summary: '{summary}'")
                
                # 빈 요약인 경우 상세 디버깅
                if isinstance(result, AIMessage):
                    logger.warning(f"[HistorySummarizer]   - result.content: '{result.content}'")
                    logger.warning(f"[HistorySummarizer]   - result.content 타입: {type(result.content)}")
                    logger.warning(f"[HistorySummarizer]   - result.content 길이: {len(result.content) if result.content else 0}")
                    
                    # response_metadata 확인
                    if hasattr(result, 'response_metadata'):
                        metadata = result.response_metadata
                        logger.warning(f"[HistorySummarizer]   - response_metadata: {metadata}")
                    else:
                        logger.warning(f"[HistorySummarizer]   - response_metadata 속성 없음")
                
                return ""
        except Exception as e:
            logger.error(f"[HistorySummarizer] ❌ 요약 실패: {str(e)}", exc_info=True)
            return ""
    
    def build_history_messages(
        self,
        conversation_history: Optional[List[Dict[str, Any]]],
        recent_count: int = 1
    ) -> List[Any]:
        """
        대화 히스토리에서 LangChain 메시지 리스트 구성
        
        Args:
            conversation_history: 대화 히스토리 (dict 또는 list)
            recent_count: 최근 몇 개의 대화는 전체 포함할지 (기본값: 1, 즉 1쌍 2개 메시지)
            
        Returns:
            LangChain 메시지 리스트
        """
        messages = []
        
        if not conversation_history:
            return messages
        
        # conversation_history가 dict 형태인 경우 (요약 포함)
        if isinstance(conversation_history, dict):
            summary = conversation_history.get("summary")
            recent_history = conversation_history.get("recent", [])
        else:
            # 리스트 형태인 경우: 요약 로직 적용
            history_list = conversation_history
            recent_count = 1  # 최근 1쌍(2개 메시지)만 포함
            
            if len(history_list) > recent_count * 2:
                # 요약이 필요한 경우
                to_summarize = history_list[:-(recent_count * 2)]
                summary = self.summarize(to_summarize, recent_count=0)
                recent_history = history_list[-(recent_count * 2):]
            else:
                # 요약 불필요 (전체 포함)
                summary = None
                recent_history = history_list
        
        # 요약 추가
        if summary:
            messages.append(HumanMessage(content=f"[이전 대화 요약]\n{summary}"))
        
        # 최근 대화 추가
        if recent_history:
            for msg in recent_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
        return messages


def update_summary_background(
    session_id: str,
    full_history: List[Dict[str, Any]],
    existing_summary: str,
    session_manager: SessionManager,
    history_summarizer: HistorySummarizer
) -> None:
    """
    백그라운드에서 세션의 대화 히스토리 요약을 업데이트합니다.
    
    Args:
        session_id: 세션 ID
        full_history: 전체 대화 히스토리
        existing_summary: 기존 요약
        session_manager: 세션 매니저 인스턴스
        history_summarizer: 히스토리 요약기 인스턴스
    """
    try:
        recent_count = 1  # 최근 1쌍(2개 메시지)만 전체 포함
        
        if len(full_history) <= recent_count * 2:
            # 요약 불필요
            logger.debug(f"[update_summary_background] 요약 불필요 - 세션 {session_id}, 히스토리 개수: {len(full_history)}")
            return
        
        to_summarize = full_history[:-(recent_count * 2)]
        logger.info(f"[update_summary_background] 요약 시작 - 세션 {session_id}, 요약 대상: {len(to_summarize)}개 메시지, 기존 요약 길이: {len(existing_summary) if existing_summary else 0} 문자")
        
        # 기존 요약과 새로운 대화를 합쳐서 요약 업데이트
        if existing_summary and to_summarize:
            # 기존 요약과 새 대화를 함께 요약
            combined_history = [
                {"role": "system", "content": f"[요약]\n{existing_summary}"},
                *to_summarize
            ]
            new_summary = history_summarizer.summarize(combined_history, recent_count=0)
        elif to_summarize:
            # 새로운 요약 생성
            new_summary = history_summarizer.summarize(to_summarize, recent_count=0)
        else:
            new_summary = existing_summary
        
        # 요약 성공 여부 확인
        if new_summary and new_summary.strip():
            session_manager.set_summary(session_id, new_summary)
            logger.info(
                f"[update_summary_background] ✅ 요약 업데이트 성공 - 세션 {session_id}, "
                f"새 요약 길이: {len(new_summary)} 문자, "
                f"요약 미리보기: {new_summary[:100]}..."
            )
        else:
            logger.warning(
                f"[update_summary_background] ⚠️ 요약 생성 실패 또는 빈 요약 - 세션 {session_id}, "
                f"기존 요약 유지 (길이: {len(existing_summary) if existing_summary else 0} 문자)"
            )
    except Exception as e:
        logger.error(
            f"[update_summary_background] ❌ 요약 업데이트 실패 - 세션 {session_id}: {str(e)}",
            exc_info=True
        )

