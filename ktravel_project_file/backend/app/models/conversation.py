from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    # 실제 테이블 구조에 맞춘 필드들
    convers_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    fullconverse = Column(Text, nullable=True)  # 전체 대화 내용
    
    # 시간 정보 (datetime 컬럼명 그대로 사용)
    datetime = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정 (나중에 User 모델 생성 후 활성화)
    # user = relationship("User", back_populates="conversations")
    # extracted_destinations = relationship("Destination", back_populates="conversation")
    
    def __repr__(self):
        return f"<Conversation(convers_id={self.convers_id}, user_id={self.user_id}, question='{self.question[:50]}...')>"