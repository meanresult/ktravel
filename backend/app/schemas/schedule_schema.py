# app/schemas/schedule_schema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ✅ Schedule 수정 요청용
class ScheduleEdit(BaseModel):
    day_title: Optional[str]
    description: Optional[str]

# ✅ Schedule 조회/응답용
class ScheduleResponse(BaseModel):
    id: int
    user_id: int
    day_title: str
    description: Optional[str]
    schedule_date: Optional[datetime]
    day_number: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
