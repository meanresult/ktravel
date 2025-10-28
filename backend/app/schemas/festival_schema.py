from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# 기본 스키마
class FestivalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filter_type: Optional[str] = Field(None, max_length=100)

# 생성용 스키마
class FestivalCreate(FestivalBase):
    pass

# 수정용 스키마
class FestivalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filter_type: Optional[str] = Field(None, max_length=100)

# 응답용 스키마
class FestivalResponse(FestivalBase):
    fastival_id: int
    
    class Config:
        from_attributes = True

# 목록용 간단한 스키마
class FestivalSummary(BaseModel):
    fastival_id: int
    title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filter_type: Optional[str] = None
    
    class Config:
        from_attributes = True

# 축제 목록 조회용
class FestivalsResponse(BaseModel):
    festivals: List[FestivalResponse]
    total_count: int

# 진행 중/예정된 축제 조회용
class OngoingFestivalsResponse(BaseModel):
    ongoing_festivals: List[FestivalResponse]
    upcoming_festivals: List[FestivalResponse]

# 축제 검색용
class FestivalSearch(BaseModel):
    query: str = Field(..., min_length=1)
    filter_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# 날짜 범위별 축제 조회용
class FestivalDateRange(BaseModel):
    start_date: date
    end_date: date
    filter_type: Optional[str] = None
