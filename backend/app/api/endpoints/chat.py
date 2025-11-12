# app/api/endpoints/chat.py
"""
채팅 API 엔드포인트 (ORM 버전) - 축제 검색 기능 포함
🌊 Streaming 지원 추가!
✅ 질문 타입별 처리 추가 (비교, 조언, 랜덤, 장소검색)
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.services.chat_service import ChatService
from app.schemas import ChatMessage
from app.core.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/send")
async def send_message(
    request: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GPT에게 메시지 전송 - 일반 방식 (기존)
    
    응답 형식:
    {
        "response": "GPT 응답",
        "convers_id": 123,
        "extracted_destinations": [],
        "results": [...],
        "festivals": [...],
        "attractions": [...],
        "has_festivals": true,
        "has_attractions": true,
        "map_markers": [...]
    }
    """
    try:
        result = ChatService.send_message(
            db=db,
            user_id=current_user['user_id'],
            message=request.message
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 오류: {str(e)}")


@router.post("/send/stream")
async def send_message_streaming(
    request: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🌊 GPT에게 메시지 전송 - Streaming 방식 (NEW!)
    
    실시간으로 응답이 타이핑되는 것처럼 보임!
    체감 속도: 0.5초로 느껴짐
    
    응답 형식 (Server-Sent Events):
    data: {"type": "searching", "message": "검색 중..."}
    data: {"type": "found", "title": "남산타워"}
    data: {"type": "generating", "message": "Lumi 응답 생성 중..."}
    data: {"type": "chunk", "content": "Hey "}
    data: {"type": "chunk", "content": "Hunters! "}
    data: {"type": "done", "full_response": "...", "result": {...}}
    """
    try:
        # 🎯 서비스 레이어로 완전히 위임
        stream_generator = ChatService.send_message_streaming(
            db=db,
            user_id=current_user['user_id'],
            message=request.message
        )
        
        return StreamingResponse(
            stream_generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트리밍 오류: {str(e)}")
    
    
    
