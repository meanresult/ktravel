"""
여행지 API 엔드포인트 (ORM 버전)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.destination import Destination
from app.models.schedule import Schedule  # 🎯 Schedule 모델 import 추가
from app.schemas import (
    DestinationResponse, 
    #DestinationSummary,
    DestinationAddRequest,  # 새로 추가
    DestinationAddResponse  # 새로 추가
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

@router.post("/add", response_model=DestinationAddResponse)
async def add_destination(
    request: DestinationAddRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """목적지를 destinations 테이블에 추가 (일정 포함)"""
    
    try:
        # 🎯 day_number로 schedule을 찾거나 생성
        schedule = Schedule.get_or_create_schedule(
            db=db,
            user_id=current_user['user_id'],
            day_number=request.day_number
        )
        
        # destinations 테이블에 추가
        new_destination = Destination.add_destination(
            db,
            user_id=current_user['user_id'],
            name=request.name,
            schedule_id=schedule.schedule_id,  # 🎯 실제 schedule_id 사용
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
            schedule_id=schedule.schedule_id  # 🎯 실제 schedule_id 반환
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"목적지 추가 실패: {str(e)}"
        )

################################################
# 아래는 현재 사용하지 않는 엔드포인트들

# @router.get("/stats", response_model=dict)
# async def get_destination_stats(
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     여행지 통계 조회 (ORM 버전)
#     """
#     try:
#         # 총 개수
#         total_count = db.query(Destination).filter(
#             Destination.user_id == current_user['user_id']
#         ).count()
        
#         # 최근 10개
#         destinations = db.query(Destination).filter(
#             Destination.user_id == current_user['user_id']
#         ).order_by(
#             Destination.created_at.desc()
#         ).limit(10).all()
        
#         return {
#             'total_count': total_count,
#             'destinations': destinations
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"통계 조회 오류: {str(e)}")

# @router.delete("/{destination_id}")
# async def delete_destination(
#     destination_id: int,
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     여행지 삭제 (ORM 버전)
#     """
#     try:
#         # 여행지 조회 (본인 것만)
#         destination = db.query(Destination).filter(
#             Destination.destination_id == destination_id,
#             Destination.user_id == current_user['user_id']
#         ).first()
        
#         if not destination:
#             raise HTTPException(status_code=404, detail="여행지를 찾을 수 없습니다")
        
#         # 삭제
#         db.delete(destination)
#         db.commit()
        
#         return {"message": "여행지가 삭제되었습니다"}
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"삭제 오류: {str(e)}")

# @router.get("/{destination_id}", response_model=DestinationResponse)
# async def get_destination(
#     destination_id: int,
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     특정 여행지 조회 (ORM 버전)
#     """
#     try:
#         destination = db.query(Destination).filter(
#             Destination.destination_id == destination_id,
#             Destination.user_id == current_user['user_id']
#         ).first()
        
#         if not destination:
#             raise HTTPException(status_code=404, detail="여행지를 찾을 수 없습니다")
        
#         return destination
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"조회 오류: {str(e)}")