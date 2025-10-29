# app/api/endpoints/chat.py
"""
채팅 API 엔드포인트 (ORM 버전) - 축제 검색 기능 포함
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.services.chat_service import ChatService
from app.schemas import (
    ChatMessage,
    ConversationSummary
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/send")  # response_model 제거하여 동적 응답 지원
async def send_message(
    request: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GPT에게 메시지 전송 - 축제 검색 기능 포함
    - 메시지 전송
    - GPT가 축제 검색 필요 여부 판단
    - DB LIKE 검색으로 축제 찾기
    - GPT 응답 받기
    - 축제 카드 및 지도 마커 정보 포함
    
    응답 형식:
    {
        "response": "GPT 응답",
        "convers_id": 123,
        "extracted_destinations": [],
        "festivals": [...],      # 축제 카드 데이터
        "has_festivals": true,   # 축제 데이터 존재 여부
        "map_markers": [...]     # 지도 마커 데이터
    }
    """
    try:
        result = ChatService.send_message(
            db=db,
            user_id=current_user['user_id'],
            message=request.message
        )
        
        # ChatService의 전체 응답을 그대로 반환
        # festivals, has_festivals, map_markers 필드 포함
        return result
    
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