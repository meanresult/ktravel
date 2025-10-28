from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Destination(Base):
    __tablename__ = "destinations"
    
    # 실제 테이블 구조에 맞춘 필드들
    destination_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    extracted_from_convers_id = Column(Integer, ForeignKey("conversations.convers_id"), nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정 (나중에 User, Conversation 모델 생성 후 활성화)
    # user = relationship("User", back_populates="destinations")
    # conversation = relationship("Conversation", back_populates="extracted_destinations")
    
    def __repr__(self):
        return f"<Destination(destination_id={self.destination_id}, name='{self.name}', user_id={self.user_id})>"