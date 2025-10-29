# app/models/festival.py
from sqlalchemy import Column, Integer, String, Text, Date, Float
from sqlalchemy.sql import func
from app.database.connection import Base

class Festival(Base):
    __tablename__ = "festival"  # 실제 테이블명 사용
    
    # 기본 필드들
    festival_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 날짜 정보
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # 축제 유형
    filter_type = Column(String(100), nullable=True)
    
    # 위치 정보 (지도 마커용)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # 추가 정보 필드들
    image_url = Column(String(500), nullable=True)
    detail_url = Column(String(500), nullable=True)
    instagram_address = Column(String(200), nullable=True)
    
    def to_dict(self):
        """
        딕셔너리 변환 메서드
        ChatService에서 사용
        """
        return {
            'festival_id': self.festival_id,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'filter_type': self.filter_type,
            'latitude': float(self.latitude) if self.latitude is not None else None,
            'longitude': float(self.longitude) if self.longitude is not None else None,
            'image_url': self.image_url,
            'detail_url': self.detail_url,
            'instagram_address': self.instagram_address
        }
    
    def __repr__(self):
        return f"<Festival(festival_id={self.festival_id}, title='{self.title}', start_date='{self.start_date}')>"