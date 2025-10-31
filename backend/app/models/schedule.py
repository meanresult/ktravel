# backend/app/models/schedule.py
from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import Base

class Schedule(Base):
    __tablename__ = "schedules"
    
    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    day_title = Column(String(255), nullable=True)
    schedule_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Schedule(schedule_id={self.schedule_id}, day_number={self.day_number}, user_id={self.user_id})>"
    
    @classmethod
    def get_or_create_schedule(
        cls,
        db: Session,
        user_id: int,
        day_number: int
    ):
        """일정 조회 또는 생성"""
        try:
            # 기존 일정 찾기
            schedule = db.query(cls).filter(
                cls.user_id == user_id,
                cls.day_number == day_number
            ).first()
            
            if schedule:
                return schedule
            
            # 없으면 새로 생성
            new_schedule = cls(
                user_id=user_id,
                day_number=day_number,
                day_title=f"{day_number}days"
            )
            
            db.add(new_schedule)
            db.commit()
            db.refresh(new_schedule)
            
            return new_schedule
            
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"일정 생성/조회 실패: {str(e)}")
    
    @classmethod
    def get_user_schedules(cls, db: Session, user_id: int):
        """사용자의 모든 일정 조회"""
        try:
            return db.query(cls).filter(
                cls.user_id == user_id
            ).order_by(cls.day_number).all()
            
        except SQLAlchemyError as e:
            raise Exception(f"일정 조회 실패: {str(e)}")
    
    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            "schedule_id": self.schedule_id,
            "user_id": self.user_id,
            "day_number": self.day_number,
            "day_title": self.day_title,
            "schedule_date": self.schedule_date.isoformat() if self.schedule_date else None,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }