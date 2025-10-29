# models/destination.py (테이블 구조 먼저 수정)
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, SmallInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import Base
from typing import Optional

class Destination(Base):
    __tablename__ = "destinations"
    
    # 기존 필드들
    destination_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    extracted_from_convers_id = Column(Integer, ForeignKey("conversations.convers_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 🎯 새로 추가할 필드들
    place_type = Column(SmallInteger, nullable=False, default=0)  # 0=일반, 1=명소, 2=축제
    reference_id = Column(Integer, nullable=True)  # festival_id 또는 attr_id
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    
    # 관계 설정 (나중에 User, Conversation 모델 생성 후 활성화)
    # user = relationship("User", back_populates="destinations")
    # conversation = relationship("Conversation", back_populates="extracted_destinations")
    
    def __repr__(self):
        return f"<Destination(destination_id={self.destination_id}, name='{self.name}', user_id={self.user_id})>"
    
    # 🎯 메서드들 추가
    @classmethod
    def add_destination(
        cls,
        db: Session,
        user_id: int,
        name: str,
        place_type: int = 0,
        reference_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        extracted_from_convers_id: Optional[int] = None
    ):
        """새로운 목적지 추가"""
        try:
            new_destination = cls(
                user_id=user_id,
                name=name,
                place_type=place_type,
                reference_id=reference_id,
                latitude=latitude,
                longitude=longitude,
                extracted_from_convers_id=extracted_from_convers_id
            )
            
            db.add(new_destination)
            db.commit()
            db.refresh(new_destination)
            
            return new_destination
            
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"목적지 추가 실패: {str(e)}")
    
    @classmethod
    def check_duplicate(
        cls,
        db: Session,
        user_id: int,
        reference_id: int,
        place_type: int
    ) -> bool:
        """중복 목적지 체크"""
        try:
            existing = db.query(cls).filter(
                cls.user_id == user_id,
                cls.reference_id == reference_id,
                cls.place_type == place_type
            ).first()
            
            return existing is not None
            
        except SQLAlchemyError as e:
            raise Exception(f"중복 체크 실패: {str(e)}")
    
    @classmethod
    def get_by_id(cls, db: Session, destination_id: int):
        """ID로 목적지 조회"""
        try:
            return db.query(cls).filter(cls.destination_id == destination_id).first()
            
        except SQLAlchemyError as e:
            raise Exception(f"목적지 조회 실패: {str(e)}")
    
    @classmethod
    def get_user_destinations(cls, db: Session, user_id: int):
        """사용자의 모든 목적지 조회"""
        try:
            return db.query(cls).filter(cls.user_id == user_id).order_by(cls.created_at.desc()).all()
            
        except SQLAlchemyError as e:
            raise Exception(f"사용자 목적지 조회 실패: {str(e)}")
    
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
            "extracted_from_convers_id": self.extracted_from_convers_id,
            "created_at": self.created_at
        }