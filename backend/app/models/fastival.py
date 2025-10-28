from sqlalchemy import Column, Integer, String, Text, Date
from sqlalchemy.sql import func
from app.database.connection import Base

class Festival(Base):
    __tablename__ = "fastival"  # 실제 테이블명 사용
    
    # 실제 테이블 구조에 맞춘 기본 필드들
    fastival_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 날짜 정보
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # 축제 유형
    filter_type = Column(String(100), nullable=True)
    
    # 추가 필드들은 실제 테이블 구조에 맞춰 나중에 추가 가능
    # location, organizer, image_url 등이 있을 수 있음
    
    def __repr__(self):
        return f"<Festival(fastival_id={self.fastival_id}, title='{self.title}', start_date='{self.start_date}')>"