from pydantic import BaseModel
from typing import Optional, List

# ✅ K-Content 생성 요청용
class KContentCreate(BaseModel):
    drama_name: str  # 필수
    location_name: Optional[str] = None
    address: Optional[str] = None
    trip_tip: Optional[str] = None
    keyword: Optional[str] = None
    category: Optional[str] = None
    
    location_name_en: Optional[str] = None
    drama_name_en: Optional[str] = None
    address_en: Optional[str] = None
    category_en: Optional[str] = None
    keyword_en: Optional[str] = None
    trip_tip_en: Optional[str] = None
    
    image_url: Optional[str] = None
    image_url_list: Optional[str] = None  # 리스트는 TEXT로 저장
    thumbnail: Optional[str] = None
    second_image: Optional[str] = None
    third_image: Optional[str] = None
    
    drama_desc: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ✅ K-Content 수정 요청용
class KContentEdit(BaseModel):
    drama_name: Optional[str] = None
    location_name: Optional[str] = None
    address: Optional[str] = None
    trip_tip: Optional[str] = None
    keyword: Optional[str] = None
    category: Optional[str] = None
    
    location_name_en: Optional[str] = None
    drama_name_en: Optional[str] = None
    address_en: Optional[str] = None
    category_en: Optional[str] = None
    keyword_en: Optional[str] = None
    trip_tip_en: Optional[str] = None
    
    image_url: Optional[str] = None
    image_url_list: Optional[str] = None
    thumbnail: Optional[str] = None
    second_image: Optional[str] = None
    third_image: Optional[str] = None
    
    drama_desc: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ✅ K-Content 조회/응답용
class KContentResponse(BaseModel):
    id: int  # content_id
    
    drama_name: Optional[str] = None
    location_name: Optional[str] = None
    address: Optional[str] = None
    trip_tip: Optional[str] = None
    keyword: Optional[str] = None
    category: Optional[str] = None
    
    location_name_en: Optional[str] = None
    drama_name_en: Optional[str] = None
    address_en: Optional[str] = None
    category_en: Optional[str] = None
    keyword_en: Optional[str] = None
    trip_tip_en: Optional[str] = None
    
    image_url: Optional[str] = None
    image_url_list: Optional[str] = None
    thumbnail: Optional[str] = None
    second_image: Optional[str] = None
    third_image: Optional[str] = None
    
    drama_desc: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        orm_mode = True
