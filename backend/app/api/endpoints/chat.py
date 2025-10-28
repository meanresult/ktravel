"""
채팅 API 엔드포인트 (ORM 버전)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.services.chat_service import ChatService
from app.schemas import (
    ChatMessage,
    ChatResponse,
    ConversationSummary
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GPT에게 메시지 전송
    - 메시지 전송
    - GPT 응답 받기
    - 여행지 자동 추출 및 저장
    """
    try:
        result = ChatService.send_message(
            db=db,
            user_id=current_user['user_id'],
            message=request.message
        )
        
        return ChatResponse(
            response=result['response'],
            conversation_id=result['convers_id'],
            extracted_destinations=result['extracted_destinations']
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 오류: {str(e)}")

@router.get("/history", response_model=List[ConversationSummary])
async def get_chat_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    대화 히스토리 조회
    """
    try:
        conversations = ChatService.get_conversation_history(
            db=db,
            user_id=current_user['user_id'],
            limit=limit
        )
        
        return conversations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"히스토리 조회 오류: {str(e)}")