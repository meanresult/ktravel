"""
일정(Schedule) API 엔드포인트 (ORM 버전)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from app.database.connection import get_db
from app.models.schedule import Schedule
from app.schemas import ScheduleResponse, ScheduleEdit
from app.api.endpoints.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(tags=["Schedules"])

# ✅ 간단 Response 모델
class SimpleResponse(BaseModel):
    status: str
    day_title: str
    description: str

# ------------------------
# Schedule Detail 조회
# ------------------------
@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule_detail(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    schedule = db.query(Schedule).filter(
        Schedule.schedule_id == schedule_id,
        Schedule.user_id == user_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return ScheduleResponse.model_validate(schedule)

# ------------------------
# Schedule 수정
# ------------------------
@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    payload: ScheduleEdit,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    schedule = db.query(Schedule).filter(
        Schedule.schedule_id == schedule_id,
        Schedule.user_id == user_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if payload.day_title is not None:
        schedule.day_title = payload.day_title
    if payload.description is not None:
        schedule.description = payload.description

    db.commit()
    db.refresh(schedule)

    return ScheduleResponse.model_validate(schedule)

# ------------------------
# Day Title 목록 조회
# ------------------------
@router.get("/day_titles", response_model=List[Dict[str, str]])
def get_day_titles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    schedules = db.query(Schedule.schedule_id, Schedule.day_title).filter(
        Schedule.user_id == user_id
    ).all()

    # day_title 중복 제거
    seen_titles = set()
    result = []
    for s_id, title in schedules:
        if title not in seen_titles:
            seen_titles.add(title)
            result.append({"id": s_id, "day_title": title})

    return result

# ------------------------
# 선택된 day_title의 description 조회
# ------------------------
@router.get("/description", response_model=Dict[str, str])
def get_description(
    day_title: str = Query(..., description="조회할 day_title"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    schedule = db.query(Schedule).filter(
        Schedule.user_id == user_id,
        Schedule.day_title == day_title
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {"description": schedule.description or ""}

# ------------------------
# description 수정
# ------------------------
@router.put("/update_description", response_model=SimpleResponse)
def update_description(
    day_title: str = Query(..., description="수정할 day_title"),
    description: str = Query(..., description="새로운 description"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    schedule = db.query(Schedule).filter(
        Schedule.user_id == user_id,
        Schedule.day_title == day_title
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.description = description
    db.commit()
    db.refresh(schedule)

    return SimpleResponse(status="success", day_title=day_title, description=description)
