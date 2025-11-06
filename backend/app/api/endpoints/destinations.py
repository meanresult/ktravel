"""
여행지 API 엔드포인트 - 일정별 목적지 조회 추가
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.destination import Destination
from app.models.schedule import Schedule
from app.schemas import (
    DestinationResponse, 
    DestinationAddRequest,
    DestinationAddResponse
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/destinations", tags=["destinations"])

# ✅ 기존 엔드포인트
@router.get("", response_model=List[DestinationResponse])
async def get_destinations(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """내 여행지 목록 조회"""
    try:
        destinations = db.query(Destination).filter(
            Destination.user_id == current_user['user_id']
        ).order_by(
            Destination.created_at.desc()
        ).limit(limit).all()
        
        return destinations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"여행지 조회 오류: {str(e)}")

# ⭐ 새로 추가: 특정 일정(day_title)의 목적지 조회
@router.get("/by-schedule", response_model=List[DestinationResponse])
async def get_destinations_by_schedule(
    day_title: str = Query(..., description="조회할 일정의 day_title"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 day_title의 목적지들을 조회합니다.
    지도에 마커로 표시하기 위해 위도/경도 정보 포함
    """
    try:
        # 1. day_title로 schedule_id 찾기
        schedule = db.query(Schedule).filter(
            Schedule.user_id == current_user['user_id'],
            Schedule.day_title == day_title
        ).first()
        
        if not schedule:
            # 일정이 없으면 빈 배열 반환 (에러 대신)
            return []
        
        # 2. schedule_id로 목적지들 조회
        destinations = db.query(Destination).filter(
            Destination.schedule_id == schedule.schedule_id
        ).order_by(
            Destination.visit_order
        ).all()
        
        return destinations
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"일정별 목적지 조회 오류: {str(e)}"
        )

@router.post("/add", response_model=DestinationAddResponse)
async def add_destination(
    request: DestinationAddRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """목적지를 destinations 테이블에 추가 (일정 포함)"""
    
    try:
        schedule = Schedule.get_or_create_schedule(
            db=db,
            user_id=current_user['user_id'],
            day_number=request.day_number
        )
        
        new_destination = Destination.add_destination(
            db,
            user_id=current_user['user_id'],
            name=request.name,
            schedule_id=schedule.schedule_id,
            place_type=request.place_type,
            reference_id=request.reference_id,
            latitude=request.latitude,
            longitude=request.longitude,
            visit_order=request.visit_order,
            notes=request.notes
        )
        
        return DestinationAddResponse(
            success=True,
            message=f"'{request.name}'이(가) {request.day_number}일차에 추가되었습니다!",
            destination_id=new_destination.destination_id,
            schedule_id=schedule.schedule_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"목적지 추가 실패: {str(e)}"
        )