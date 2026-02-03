from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# --------------------------------
# 기본 스키마 (공통 필드)
# --------------------------------
class RestaurantBase(BaseModel):
    restaurant_name: str = Field(..., min_length=1, max_length=255)
    place: Optional[str] = Field(None, max_length=255)
    image_path: Optional[HttpUrl] = None
    Latitude: Optional[float] = None
    Longitude: Optional[float] = None
    near_subway: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=255)
    description_clean: Optional[str] = None

    restaurant_name_en: Optional[str] = Field(None, max_length=255)
    place_en: Optional[str] = Field(None, max_length=255)
    near_subway_en: Optional[str] = Field(None, max_length=255)
    type_en: Optional[str] = Field(None, max_length=255)
    description_clean_en: Optional[str] = None


# --------------------------------
# 생성(Create) 요청 스키마
# --------------------------------
class RestaurantCreate(RestaurantBase):
    pass  # restaurant_name etc. required fields inherited


# --------------------------------
# 수정(Update) 요청 스키마
# --------------------------------
class RestaurantUpdate(BaseModel):
    restaurant_name: Optional[str] = Field(None, max_length=255)
    place: Optional[str] = Field(None, max_length=255)
    image_path: Optional[HttpUrl] = None
    Latitude: Optional[float] = None
    Longitude: Optional[float] = None
    near_subway: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=255)
    description_clean: Optional[str] = None

    restaurant_name_en: Optional[str] = Field(None, max_length=255)
    place_en: Optional[str] = Field(None, max_length=255)
    near_subway_en: Optional[str] = Field(None, max_length=255)
    type_en: Optional[str] = Field(None, max_length=255)
    description_clean_en: Optional[str] = None


# --------------------------------
# 응답(Response) 스키마
# --------------------------------
class RestaurantResponse(RestaurantBase):
    restaurant_id: int

    model_config = {
        "from_attributes": True
    }


# --------------------------------
# 목록용 간단한 정보
# --------------------------------
class RestaurantSummary(BaseModel):
    restaurant_id: int
    restaurant_name: str
    place: Optional[str] = None
    type: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# --------------------------------
# 전체 목록 조회
# --------------------------------
class RestaurantsResponse(BaseModel):
    restaurants: List[RestaurantResponse]
    total_count: int


# --------------------------------
# 검색 요청 스키마
# --------------------------------
class RestaurantSearch(BaseModel):
    query: str = Field(..., min_length=1)


# --------------------------------
# 좌표 기반 검색 스키마 (옵션)
# --------------------------------
class RestaurantNear(BaseModel):
    latitude: float
    longitude: float
    radius: float = Field(..., description="Search radius in km")
