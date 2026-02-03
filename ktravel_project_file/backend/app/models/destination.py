# models/destination.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, SmallInteger, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import Base
from typing import Optional
from sqlalchemy import Column, JSON

class Destination(Base):
    __tablename__ = "destinations"
    
    # 기존 필드들
    destination_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    extracted_from_convers_id = Column(Integer, ForeignKey("conversations.convers_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 장소 정보
    place_type = Column(SmallInteger, nullable=False, default=0)
    reference_id = Column(Integer, nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    
    # 🎯 스케줄 관련 필드들 (DB에 있는 컬럼들)
    schedule_id = Column(Integer, ForeignKey("schedules.schedule_id"), nullable=False)
    visit_order = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    custom_fields = Column(JSON, nullable=True)  # 🆕 추가
    
    def __repr__(self):
        return f"<Destination(destination_id={self.destination_id}, name='{self.name}', user_id={self.user_id})>"
    
    @classmethod
    def add_destination(
        cls,
        db: Session,
        user_id: int,
        name: str,
        schedule_id: int,  # 🎯 day_number 대신 schedule_id
        place_type: int = 0,
        reference_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        visit_order: Optional[int] = None,
        notes: Optional[str] = None,
        extracted_from_convers_id: Optional[int] = None
    ):
        """새로운 목적지 추가"""
        try:
            new_destination = cls(
                user_id=user_id,
                name=name,
                schedule_id=schedule_id,  # 🎯 변경
                place_type=place_type,
                reference_id=reference_id,
                latitude=latitude,
                longitude=longitude,
                visit_order=visit_order,  # 🎯 추가
                notes=notes,  # 🎯 추가
                extracted_from_convers_id=extracted_from_convers_id
            )
            
            db.add(new_destination)
            db.commit()
            db.refresh(new_destination)
            
            return new_destination
            
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"목적지 추가 실패: {str(e)}")
    
    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            "destination_id": self.destination_id,
            "user_id": self.user_id,
            "name": self.name,
            "place_type": self.place_type,
            "reference_id": self.reference_id,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "schedule_id": self.schedule_id,  # 🎯 추가
            "visit_order": self.visit_order,  # 🎯 추가
            "notes": self.notes,  # 🎯 추가
            "extracted_from_convers_id": self.extracted_from_convers_id,
            "created_at": self.created_at
        }