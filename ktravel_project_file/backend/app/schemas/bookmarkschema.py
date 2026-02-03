# backend/app/schemas/bookmarkschema.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import IntEnum


# ✅ PlaceType Enum 정의 (recommend.py에서 import)
class PlaceType(IntEnum):
    """
    장소 타입 상수
    - 0: 음식점 (RESTAURANT)
    - 1: 축제 (FESTIVAL)
    - 2: 명소 (ATTRACTION)
    - 3: K-콘텐츠 (KCONTENT)
    """
    RESTAURANT = 0
    FESTIVAL = 1
    ATTRACTION = 2
    KCONTENT = 3


class BookmarkCreate(BaseModel):
    """
    POST /api/bookmark 요청 바디
    - K-Media 페이지에서 북마크 추가 시 사용
    """
    user_id: int
    name: str
    place_type: int
    reference_id: int

    # ✅ K-콘텐츠 영어 정보 (DB 컬럼과 일치)
    location_name: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    keyword: Optional[str] = None
    trip_tip_en: Optional[str] = None

    # 위치 정보
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # 이미지 & 메모
    image_url: Optional[str] = None
    notes: Optional[str] = None

    # 대화 추출 여부
    extracted_from_convers_id: Optional[int] = 0


class BookmarkListResponse(BaseModel):
    """
    GET /api/bookmark/{user_id} 응답용
    - 북마크 목록 조회 시 사용
    """
    bookmark_id: int
    user_id: int
    
    name: str
    place_type: int
    reference_id: int

    # ✅ 조인해서 가져올 수 있는 필드들 (Optional)
    location_name_en: Optional[str] = None
    address_en: Optional[str] = None
    category_en: Optional[str] = None
    keyword_en: Optional[str] = None
    trip_tip_en: Optional[str] = None
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None
    
    extracted_from_convers_id: Optional[int] = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookmarkForRecommend(BaseModel):
    """
    추천 API(recommend.py)에서 사용할 수 있는 스키마
    - 유저의 북마크들 기반으로 추천 로직 돌릴 때 사용 가능
    """
    user_id: int
    bookmark_ids: Optional[List[int]] = None

    model_config = ConfigDict(from_attributes=True)


class BaseResponse(BaseModel):
    """
    공통 응답형으로 쓸 수 있는 베이스
    """
    detail: str = "success"