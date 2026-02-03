from pydantic import BaseModel, Field, HttpUrl
from datetime import date
from typing import Optional, List, Dict, Any

# 🆕 스케줄 테이블 데이터 스키마
class ScheduleTableRowData(BaseModel):
    destination_id: Optional[int] = None
    visit_order: int
    Location: str = ""
    Notice: Optional[str] = ""
    # 동적 필드들 (Time, Estimated Cost, Memo 등)
    custom_fields: Dict[str, Any] = {}

class UpdateScheduleTableRequest(BaseModel):
    day_title: str
    column_order: List[str]  # ["Time", "Location", "Estimated Cost", "Memo", "Notice"]
    rows: List[Dict[str, Any]]  # 각 행의 데이터

class ScheduleTableDataResponse(BaseModel):
    column_order: List[str]
    rows: List[Dict[str, Any]]
