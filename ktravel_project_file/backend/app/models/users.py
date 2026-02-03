from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"
    
    # 실제 테이블 구조에 맞춘 필드들
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # 해시된 비밀번호
    
    # 개인정보
    name = Column(String(255), nullable=False)  # 실명
    address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)
    date = Column(String(20), nullable=True)  # 생년월일 (문자열로 저장되는 듯)
    
    # 권한 관련
    permit = Column(String(50), nullable=True)  # 권한 정보
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정 (나중에 활성화)
    # conversations = relationship("Conversation", back_populates="user")
    # destinations = relationship("Destination", back_populates="user")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', email='{self.email}')>"