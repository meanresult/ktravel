# app/schemas/festival.py
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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = Field(None, max_length=500)
    detail_url: Optional[str] = Field(None, max_length=500)
    instagram_address: Optional[str] = Field(None, max_length=200)

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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = Field(None, max_length=500)
    detail_url: Optional[str] = Field(None, max_length=500)
    instagram_address: Optional[str] = Field(None, max_length=200)

# 응답용 스키마 (오타 수정: fastival_id → festival_id)
class FestivalResponse(FestivalBase):
    festival_id: int  # 오타 수정
    
    class Config:
        from_attributes = True

# 목록용 간단한 스키마 (오타 수정: fastival_id → festival_id)
class FestivalSummary(BaseModel):
    festival_id: int  # 오타 수정
    title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filter_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
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

# 채팅용 축제 카드 스키마 (ChatService에서 사용)
class FestivalCard(BaseModel):
    festival_id: int
    title: str
    description: Optional[str] = None
    start_date: Optional[str] = None  # ISO 형식 문자열
    end_date: Optional[str] = None    # ISO 형식 문자열
    filter_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    detail_url: Optional[str] = None
    instagram_address: Optional[str] = None

# 지도 마커용 스키마
class MapMarker(BaseModel):
    id: int
    title: str
    latitude: float
    longitude: float
    description: str
    image_url: Optional[str] = None
    detail_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None