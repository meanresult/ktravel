"""
여행지 API 엔드포인트 - 일정별 목적지 조회 추가
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.destination import Destination
from app.models.schedule import Schedule
from app.models.schedule_table_metadata import ScheduleTableMetadata  # 🆕 추가!
from app.schemas import (
    DestinationResponse, 
    DestinationAddRequest,
    DestinationAddResponse
)
from app.core.deps import get_current_user
from app.schemas import (
    ScheduleTableRowData, 
    UpdateScheduleTableRequest,
    ScheduleTableDataResponse
)
router = APIRouter(prefix="/destinations", tags=["destinations"])


# 📥 테이블 데이터 조회 (컬럼 순서 + 행 데이터)
@router.get("/schedule-table-data", response_model=ScheduleTableDataResponse)
async def get_schedule_table_data(
    day_title: str = Query(..., description="조회할 일정의 day_title"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 일정의 테이블 데이터를 조회합니다.
    - 컬럼 순서
    - 각 행의 데이터 (Location, Notice, custom_fields)
    """
    try:
        # 1. schedule 찾기
        schedule = db.query(Schedule).filter(
            Schedule.user_id == current_user['user_id'],
            Schedule.day_title == day_title
        ).first()
        
        if not schedule:
            return ScheduleTableDataResponse(
                column_order=["Time", "Location", "Estimated Cost", "Memo", "Notice"],
                rows=[]
            )
        
        # 2. 컬럼 순서 조회
        metadata = db.query(ScheduleTableMetadata).filter(
            ScheduleTableMetadata.schedule_id == schedule.schedule_id
        ).first()
        
        column_order = metadata.column_order if metadata else ["Time", "Location", "Estimated Cost", "Memo", "Notice"]
        
        # 3. destinations 조회
        destinations = db.query(Destination).filter(
            Destination.schedule_id == schedule.schedule_id
        ).order_by(Destination.visit_order).all()
        
        # 4. 행 데이터 구성
        rows = []
        for dest in destinations:
            row_data = {
                "destination_id": dest.destination_id,
                "visit_order": dest.visit_order,
                "Location": dest.name or "",
                "Notice": dest.notes or ""
            }
            
            # custom_fields 병합
            if dest.custom_fields:
                row_data.update(dest.custom_fields)
            
            rows.append(row_data)
        
        return ScheduleTableDataResponse(
            column_order=column_order,
            rows=rows
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"테이블 데이터 조회 오류: {str(e)}"
        )

# 💾 테이블 데이터 저장 (컬럼 순서 + 행 데이터)
@router.put("/update-schedule-data")
async def update_schedule_data(
    request: UpdateScheduleTableRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    일정 테이블의 전체 데이터를 저장합니다.
    - 컬럼 순서 저장
    - 기존 데이터 삭제 후 새로 생성 (화면에 보이는 것만)
    """
    try:
        # 1. schedule 찾기
        schedule = db.query(Schedule).filter(
            Schedule.user_id == current_user['user_id'],
            Schedule.day_title == request.day_title
        ).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
        
        # 2. 컬럼 순서 저장
        metadata = db.query(ScheduleTableMetadata).filter(
            ScheduleTableMetadata.schedule_id == schedule.schedule_id
        ).first()
        
        if not metadata:
            metadata = ScheduleTableMetadata(
                user_id=current_user['user_id'],
                schedule_id=schedule.schedule_id,
                column_order=request.column_order
            )
            db.add(metadata)
        else:
            metadata.column_order = request.column_order
        
        # ✨✨✨ 3. 기존 destination 데이터 모두 삭제 (핵심!) ✨✨✨
        deleted_count = db.query(Destination).filter(
            Destination.schedule_id == schedule.schedule_id,
            Destination.user_id == current_user['user_id']
        ).delete(synchronize_session=False)
        
        # 4. 새로운 행 데이터 생성
        created_count = 0
        
        for row_data in request.rows:
            location = row_data.get('Location', '').strip()
            
            # Location이 비어있으면 스킵
            if not location:
                continue
            
            # custom_fields 추출 (Location, Notice, destination_id, visit_order 제외)
            custom_fields = {}
            for key, value in row_data.items():
                if key not in ['destination_id', 'visit_order', 'Location', 'Notice']:
                    custom_fields[key] = value
            
            # 항상 새 destination 생성 (destination_id는 무시)
            new_destination = Destination(
                user_id=current_user['user_id'],
                schedule_id=schedule.schedule_id,
                name=location,
                notes=row_data.get('Notice', ''),
                visit_order=row_data.get('visit_order', 0),
                place_type=0,
                custom_fields=custom_fields if custom_fields else None
            )
            db.add(new_destination)
            created_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"저장 완료 - 삭제: {deleted_count}개, 생성: {created_count}개",
            "deleted": deleted_count,
            "created": created_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"저장 실패: {str(e)}")
    
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