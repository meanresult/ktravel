
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
# ===== 요청 스키마 ===== 기존 정보 고객의 요청 
class BookmarkBasedRecommendRequest(BaseModel):
    user_id: int
    place_type: Optional[int] = None
    top_k_per_bookmark: int = 5


# ===== 추천 아이템 스키마 ===== 추천 아이템 정보
class RecommendedItem(BaseModel):
    place_type: int
    reference_id: int
    name: str
    address: Optional[str] = None
    image_url: Optional[str] = None
    score: float
    extra: Optional[dict] = None
# ===== 응답 스키마 ===== 총 추천 아이템 수 포함
class BookmarkBasedRecommendResponse(BaseModel):
    user_id: int
    total_count: int
    items: List[RecommendedItem]
    
    

