# app/models/schedule_table_metadata.py (새 파일 생성)
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database.connection import Base

class ScheduleTableMetadata(Base):
    __tablename__ = "schedule_table_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.schedule_id"), nullable=False)
    column_order = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ScheduleTableMetadata(schedule_id={self.schedule_id})>"