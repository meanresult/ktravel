# backend/app/api/endpoints/recommend_llm.py
"""
LLM 강화 추천 엔드포인트

기존 recommend.py의 벡터 추천에 LLM 분석을 추가
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.models.bookmark import Bookmark
from app.core.qdrant_client import get_qdrant_client
from app.services.llm_recommend_service import LLMRecommendService, generate_simple_reason
from app.schemas.recommend_schema import (
    BookmarkBasedRecommendRequest,
    RecommendedItem,
)
from app.schemas.bookmarkschema import PlaceType

# ✅ 원본 테이블
from app.models.kcontent import KContent
from app.models.restaurant import Restaurant
from app.models.festival import Festival

from pydantic import BaseModel

router = APIRouter(prefix="/recommend-llm", tags=["recommend-llm"])

# ============================================================
# 응답 스키마
# ============================================================

class LLMRecommendedItem(BaseModel):
    """LLM 추천 아이템 (추천 이유 포함)"""
    place_type: int
    reference_id: int
    name: str
    address: Optional[str] = None
    image_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None
    
    # 점수
    vector_score: float  # Qdrant 유사도 점수
    llm_rank: Optional[int] = None  # LLM이 매긴 순위
    llm_match_score: Optional[float] = None  # LLM 매칭 점수
    
    # 추천 이유
    llm_reason: Optional[str] = None  # LLM이 생성한 이유
    
    # 추가 정보
    extra: Optional[dict] = None


class LLMRecommendResponse(BaseModel):
    """LLM 추천 응답"""
    user_id: int
    total_count: int
    user_taste_summary: Optional[str] = None  # 사용자 취향 분석
    recommendations: list[LLMRecommendedItem]


# ============================================================
# Helper: 원본 데이터 조회
# ============================================================

def fetch_original_data(db: Session, place_type: int, reference_id: int):
    """원본 테이블에서 데이터 조회 (recommend.py와 동일)"""
    try:
        if place_type == PlaceType.KCONTENT:
            item = db.query(KContent).filter(KContent.content_id == reference_id).first()
            if not item:
                return None
            
            image_url = None
            if hasattr(item, 'thumbnail') and item.thumbnail:
                image_url = item.thumbnail
            elif hasattr(item, 'image_url') and item.image_url:
                image_url = item.image_url
            
            return {
                "name": item.location_name_en or item.location_name or item.drama_name_en or "Unknown",
                "address": item.address_en or item.address or "",
                "image_url": image_url,
                "latitude": float(item.latitude) if item.latitude else None,
                "longitude": float(item.longitude) if item.longitude else None,
                "category": item.category_en or item.category or "",
                "extra": {
                    "content_id": item.content_id,
                    "drama_name_en": item.drama_name_en,
                    "location_name_en": item.location_name_en,
                    "address_en": item.address_en,
                    "category_en": item.category_en,
                    "keyword_en": item.keyword_en,
                    "trip_tip_en": item.trip_tip_en,
                }
            }
        
        elif place_type == PlaceType.RESTAURANT:
            item = db.query(Restaurant).filter(Restaurant.restaurant_id == reference_id).first()
            if not item:
                return None
            
            return {
                "name": item.restaurant_name or "Unknown",
                "address": item.address or "",
                "image_url": item.image_url,
                "latitude": float(item.latitude) if item.latitude else None,
                "longitude": float(item.longitude) if item.longitude else None,
                "category": getattr(item, 'category', None) or "",
                "extra": {
                    "restaurant_id": item.restaurant_id,
                    "restaurant_name": item.restaurant_name,
                }
            }
        
        elif place_type == PlaceType.FESTIVAL:
            item = db.query(Festival).filter(Festival.festival_id == reference_id).first()
            if not item:
                return None
            
            return {
                "name": item.festival_name or "Unknown",
                "address": getattr(item, 'address', None) or "",
                "image_url": getattr(item, 'image_url', None),
                "latitude": float(item.latitude) if hasattr(item, 'latitude') and item.latitude else None,
                "longitude": float(item.longitude) if hasattr(item, 'longitude') and item.longitude else None,
                "category": "festival",
                "extra": {
                    "festival_id": item.festival_id,
                    "festival_name": item.festival_name,
                }
            }
        
        return None
    
    except Exception as e:
        print(f"❌ 원본 데이터 조회 실패: {e}")
        return None


PLACE_TYPE_COLLECTION_MAP = {
    PlaceType.RESTAURANT: "seoul-restaurant",
    PlaceType.FESTIVAL: "seoul-festival",
    PlaceType.KCONTENT: "seoul-kcontent",
}


# ============================================================
# 1️⃣ LLM 강화 추천 (벡터 + LLM)
# ============================================================

@router.post("/enhanced", response_model=LLMRecommendResponse)
def get_llm_enhanced_recommendations(
    req: BookmarkBasedRecommendRequest,
    use_llm: bool = True,  # LLM 사용 여부 (비용 절약 옵션)
    db: Session = Depends(get_db),
):
    """
    LLM 강화 추천
    
    1. Qdrant로 벡터 기반 유사 콘텐츠 추천 (기존 방식)
    2. LLM으로 사용자 취향 분석 및 재정렬
    3. 각 추천에 개인화된 이유 추가
    
    Query Parameters:
        use_llm (bool): LLM 사용 여부 (기본값: True)
                        False면 간단한 규칙 기반 이유만 생성
    """
    
    # 1️⃣ 사용자 북마크 가져오기
    query = db.query(Bookmark).filter(Bookmark.user_id == req.user_id)
    if req.place_type is not None:
        query = query.filter(Bookmark.place_type == req.place_type)
    
    bookmarks = query.order_by(Bookmark.created_at.desc()).limit(10).all()
    
    if not bookmarks:
        raise HTTPException(status_code=404, detail="해당 사용자의 북마크가 없습니다.")
    
    # 북마크 상세 정보 조회 (LLM에 전달용)
    bookmark_details = []
    for bm in bookmarks:
        details = fetch_original_data(db, bm.place_type, bm.reference_id)
        if details:
            bookmark_details.append({
                "bookmark_id": bm.bookmark_id,
                "place_type": bm.place_type,
                "reference_id": bm.reference_id,
                **details
            })
    
    # 2️⃣ Qdrant로 벡터 기반 추천
    client = get_qdrant_client()
    qdrant_recommendations = []
    seen_ids = set()
    
    for bm in bookmarks:
        collection_name = PLACE_TYPE_COLLECTION_MAP.get(bm.place_type)
        if not collection_name:
            continue
            
          
        try:
          
            # 2. 실제 포인트 몇 개 가져와서 ID 형식 확인
            points = client.scroll(collection_name=collection_name, limit=3)
            print(f"🔍 실제 포인트 ID들: {[p.id for p in points[0]]}")
            print(f"🔍 북마크 reference_id: {bm.reference_id} (타입: {type(bm.reference_id)})")
            
            # 3. 기존 recommend 코드
            results = client.recommend(
                collection_name=collection_name,
                positive=[bm.reference_id],
                limit=req.top_k_per_bookmark,
            )
        except Exception as e:
            print(f"Qdrant 추천 실패: {e}")
            continue
        
        try:
            results = client.recommend(
                collection_name=collection_name,
                positive=[bm.reference_id],
                limit=req.top_k_per_bookmark,
            )
        except Exception as e:
            print(f"Qdrant 추천 실패: {e}")
            continue
        
        for r in results:
            payload = r.payload or {}
            rec_reference_id = payload.get("content_id") or payload.get("id") or r.id
            
            unique_key = f"{bm.place_type}_{rec_reference_id}"
            if unique_key in seen_ids:
                continue
            seen_ids.add(unique_key)
            
            # 원본 데이터 조회
            original_data = fetch_original_data(db, bm.place_type, rec_reference_id)
            
            if original_data:
                qdrant_recommendations.append({
                    "place_type": bm.place_type,
                    "reference_id": rec_reference_id,
                    "name": original_data["name"],
                    "address": original_data.get("address"),
                    "image_url": original_data.get("image_url"),
                    "latitude": original_data.get("latitude"),
                    "longitude": original_data.get("longitude"),
                    "category": original_data.get("category"),
                    "score": r.score,
                    "extra": original_data.get("extra", {}),
                })
            else:
                # ✅ recommend.py와 동일한 fallback 추가
                qdrant_recommendations.append({
                    "place_type": bm.place_type,
                    "reference_id": rec_reference_id,
                    "name": (
                        payload.get("location_name_en")
                        or payload.get("location_name")
                        or payload.get("name")
                        or "Unknown"
                    ),
                    "address": payload.get("address_en") or payload.get("address"),
                    "image_url": (
                        payload.get("image_url")
                        or payload.get("thumbnail")
                        or payload.get("image")
                    ),
                    "latitude": payload.get("latitude"),
                    "longitude": payload.get("longitude"),
                    "category": payload.get("category_en") or payload.get("category"),
                    "score": r.score,
                    "extra": payload,
                })
    if not qdrant_recommendations:
        raise HTTPException(status_code=404, detail="추천 결과를 찾지 못했습니다.")
    
    # 3️⃣ LLM으로 강화 (선택적)
    if use_llm:
        try:
            llm_service = LLMRecommendService()
            enhanced_result = llm_service.enhance_recommendations(
                user_bookmarks=bookmark_details,
                recommended_items=qdrant_recommendations,
                top_n=10
            )
            
            # 응답 변환
            recommendations = [
                LLMRecommendedItem(
                    place_type=item["place_type"],
                    reference_id=item["reference_id"],
                    name=item["name"],
                    address=item.get("address"),
                    image_url=item.get("image_url"),
                    latitude=item.get("latitude"),
                    longitude=item.get("longitude"),
                    category=item.get("category"),
                    vector_score=item.get("original_score", 0),
                    llm_rank=item.get("llm_rank"),
                    llm_match_score=item.get("llm_match_score"),
                    llm_reason=item.get("llm_reason"),
                    extra=item.get("extra"),
                )
                for item in enhanced_result["recommendations"]
            ]
            
            return LLMRecommendResponse(
                user_id=req.user_id,
                total_count=len(recommendations),
                user_taste_summary=enhanced_result.get("user_taste_summary"),
                recommendations=recommendations
            )
            
        except Exception as e:
            print(f"⚠️ LLM 강화 실패, 기본 추천으로 fallback: {e}")
            use_llm = False  # fallback to simple reasons
    
    # 4️⃣ 간단한 이유 생성 (LLM 없이)
    if not use_llm:
        recommendations = []
        for item in qdrant_recommendations[:10]:
            simple_reason = generate_simple_reason(bookmark_details, item)
            
            recommendations.append(
                LLMRecommendedItem(
                    place_type=item["place_type"],
                    reference_id=item["reference_id"],
                    name=item["name"],
                    address=item.get("address"),
                    image_url=item.get("image_url"),
                    latitude=item.get("latitude"),
                    longitude=item.get("longitude"),
                    category=item.get("category"),
                    vector_score=item.get("score", 0),
                    llm_reason=simple_reason,
                    extra=item.get("extra"),
                )
            )
        
        return LLMRecommendResponse(
            user_id=req.user_id,
            total_count=len(recommendations),
            user_taste_summary="Based on your bookmarked places",
            recommendations=recommendations
        )