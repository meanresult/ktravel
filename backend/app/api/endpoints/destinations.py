"""
여행지 API 엔드포인트 (ORM 버전)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.destination import Destination
from app.schemas import (
    DestinationResponse, 
    DestinationSummary
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/destinations", tags=["destinations"])

@router.get("", response_model=List[DestinationResponse])
async def get_destinations(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 여행지 목록 조회 (ORM 버전)
    """
    try:
        destinations = db.query(Destination).filter(
            Destination.user_id == current_user['user_id']
        ).order_by(
            Destination.created_at.desc()
        ).limit(limit).all()
        
        return destinations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"여행지 조회 오류: {str(e)}")

@router.get("/stats", response_model=dict)
async def get_destination_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    여행지 통계 조회 (ORM 버전)
    """
    try:
        # 총 개수
        total_count = db.query(Destination).filter(
            Destination.user_id == current_user['user_id']
        ).count()
        
        # 최근 10개
        destinations = db.query(Destination).filter(
            Destination.user_id == current_user['user_id']
        ).order_by(
            Destination.created_at.desc()
        ).limit(10).all()
        
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
    db: Session = Depends(get_db)
):
    """
    여행지 삭제 (ORM 버전)
    """
    try:
        # 여행지 조회 (본인 것만)
        destination = db.query(Destination).filter(
            Destination.destination_id == destination_id,
            Destination.user_id == current_user['user_id']
        ).first()
        
        if not destination:
            raise HTTPException(status_code=404, detail="여행지를 찾을 수 없습니다")
        
        # 삭제
        db.delete(destination)
        db.commit()
        
        return {"message": "여행지가 삭제되었습니다"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"삭제 오류: {str(e)}")

@router.get("/{destination_id}", response_model=DestinationResponse)
async def get_destination(
    destination_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 여행지 조회 (ORM 버전)
    """
    try:
        destination = db.query(Destination).filter(
            Destination.destination_id == destination_id,
            Destination.user_id == current_user['user_id']
        ).first()
        
        if not destination:
            raise HTTPException(status_code=404, detail="여행지를 찾을 수 없습니다")
        
        return destination
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 오류: {str(e)}")