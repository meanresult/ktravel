from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 기본 스키마
class ConversationBase(BaseModel):
    question: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    fullconverse: Optional[str] = None

# 생성용 스키마 (새 대화 생성)
class ConversationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    question: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    fullconverse: Optional[str] = None

# 수정용 스키마 (거의 사용하지 않을 것 같지만)
class ConversationUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1)
    response: Optional[str] = Field(None, min_length=1)
    fullconverse: Optional[str] = None

# 응답용 스키마
class ConversationResponse(ConversationBase):
    convers_id: int
    user_id: int
    datetime: datetime
    
    class Config:
        from_attributes = True

# 목록용 간단한 스키마
class ConversationSummary(BaseModel):
    convers_id: int
    question: str = Field(..., max_length=100)  # 질문 일부만
    datetime: datetime
    
    class Config:
        from_attributes = True

# 사용자별 대화 목록 조회용
class UserConversationsResponse(BaseModel):
    conversations: List[ConversationSummary]
    total_count: int

# 채팅 메시지 스키마 (실시간 채팅용)
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None

# 채팅 응답 스키마
class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    extracted_destinations: Optional[List[str]] = None

# 대화 히스토리 조회용
class ConversationHistory(BaseModel):
    conversations: List[ConversationResponse]
    total_count: int
    page: int
    page_size: int
