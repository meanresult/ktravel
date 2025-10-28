"""
여행지 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.database.connection import get_db_dependency
from app.database.queries.destination_queries import DestinationService  # ← 호환성 클래스 사용
from app.core.deps import get_current_user

router = APIRouter(prefix="/destinations", tags=["destinations"])

# Response 모델
class DestinationResponse(BaseModel):
    destination_id: int
    name: str
    created_at: datetime

class DestinationStatsResponse(BaseModel):
    total_count: int
    destinations: List[DestinationResponse]

@router.get("", response_model=List[DestinationResponse])
async def get_destinations(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_dependency)
):
    """
    내 여행지 목록 조회
    """
    conn, cursor = db
    
    try:
        destinations = DestinationService.get_user_destinations(
            cursor,
            user_id=current_user['user_id'],
            limit=limit
        )
        
        return destinations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"여행지 조회 오류: {str(e)}")

@router.get("/stats", response_model=DestinationStatsResponse)
async def get_destination_stats(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_dependency)
):
    """
    여행지 통계 조회
    """
    conn, cursor = db
    
    try:
        total_count = DestinationService.get_destinations_count(
            cursor,
            user_id=current_user['user_id']
        )
        
        destinations = DestinationService.get_user_destinations(
            cursor,
            user_id=current_user['user_id'],
            limit=10
        )
        
        return {
            'total_count': total_count,
            'destinations': destinations
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 오류: {str(e)}")

@router.delete("/{destination_id}")
async def delete_destination(
    destination_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db_dependency)
):
    """
    여행지 삭제
    """
    conn, cursor = db
    
    try:
        success = DestinationService.delete_destination(
            conn, cursor,
            destination_id=destination_id,
            user_id=current_user['user_id']
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="여행지를 찾을 수 없습니다")
        
        return {"message": "여행지가 삭제되었습니다"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 오류: {str(e)}")