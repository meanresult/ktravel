"""
축제 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.database.connection import get_db
from app.database.queries.festival_queries import FestivalQueries

router = APIRouter(
    prefix="/api/festivals",
    tags=["festivals"]
)

# Response 모델
class FestivalResponse(BaseModel):
    fastival_id: int
    filter_type: Optional[str]
    title: str
    start_date: Optional[date]
    end_date: Optional[date]
    image_url: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    description: Optional[str]
    detail_url: Optional[str]

    class Config:
        from_attributes = True

# 모든 축제 조회
@router.get("/", response_model=List[FestivalResponse])
async def get_all_festivals(
    filter_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """모든 축제 목록 조회"""
    with get_db() as (conn, cursor):
        result = FestivalQueries.get_all_festivals_with_error_handling(
            cursor, filter_type, skip, limit
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result["data"]

# 특정 축제 조회
@router.get("/{festival_id}", response_model=FestivalResponse)
async def get_festival_by_id(festival_id: int):
    """특정 축제 상세 정보"""
    with get_db() as (conn, cursor):
        result = FestivalQueries.get_festival_by_id_with_validation(cursor, festival_id)
        
        if not result["success"]:
            status_code = result.get("status_code", 500)
            raise HTTPException(status_code=status_code, detail=result["error"])
        
        return result["data"]

# 진행 중인 축제
@router.get("/status/ongoing", response_model=List[FestivalResponse])
async def get_ongoing_festivals():
    """현재 진행 중인 축제"""
    with get_db() as (conn, cursor):
        result = FestivalQueries.get_ongoing_festivals_with_error_handling(cursor)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result["data"]

# 예정된 축제
@router.get("/status/upcoming", response_model=List[FestivalResponse])
async def get_upcoming_festivals():
    """예정된 축제"""
    with get_db() as (conn, cursor):
        result = FestivalQueries.get_upcoming_festivals_with_error_handling(cursor)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result["data"]

# 검색
@router.get("/search/query", response_model=List[FestivalResponse])
async def search_festivals(q: str):
    """축제 검색"""
    with get_db() as (conn, cursor):
        result = FestivalQueries.search_festivals_with_error_handling(cursor, q)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result["data"]