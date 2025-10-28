from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# 기본 스키마
class DestinationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

# 생성용 스키마
class DestinationCreate(DestinationBase):
    user_id: int = Field(..., gt=0)
    extracted_from_convers_id: Optional[int] = Field(None, gt=0)

# 수정용 스키마
class DestinationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

# 응답용 스키마
class DestinationResponse(DestinationBase):
    destination_id: int
    user_id: int
    extracted_from_convers_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# 목록용 간단한 스키마
class DestinationSummary(BaseModel):
    destination_id: int
    name: str
    
    class Config:
        from_attributes = True

# 사용자별 여행지 목록 조회용
class UserDestinationsResponse(BaseModel):
    destinations: list[DestinationResponse]
    total_count: int

# 대화에서 추출된 여행지 생성용
class DestinationFromConversation(BaseModel):
    names: list[str] = Field(..., min_items=1)
    conversation_id: int = Field(..., gt=0)
