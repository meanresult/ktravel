# backend/app/api/endpoints/recommend.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.bookmark import Bookmark
from app.core.qdrant_client import get_qdrant_client
from app.schemas.recommend_schema import (
    BookmarkBasedRecommendRequest,
    BookmarkBasedRecommendResponse,
    RecommendedItem,
)
from app.schemas.bookmarkschema import PlaceType

# ✅ 원본 테이블 모델 import
from app.models.kcontent import KContent
from app.models.restaurant import Restaurant
# from app.models.attraction import Attraction  # 필요시 주석 해제
from app.models.festival import Festival

router = APIRouter(prefix="/recommand", tags=["recommand"])

PLACE_TYPE_COLLECTION_MAP = {
    PlaceType.RESTAURANT: "seoul-restaurant",
    PlaceType.FESTIVAL: "seoul-festival",
    # PlaceType.ATTRACTION: "seoul-attraction",
    PlaceType.KCONTENT: "seoul-kcontents",
}


############################################################
# 🔧 Helper Function: 원본 테이블에서 데이터 가져오기
############################################################
def fetch_original_data(db: Session, place_type: int, reference_id: int):
    """
    place_type과 reference_id로 원본 테이블에서 완전한 데이터 조회
    
    Returns:
        dict: 원본 데이터 (name, address, image_url, latitude, longitude 등)
    """
    try:
        if place_type == PlaceType.KCONTENT:
            # ✅ K-콘텐츠 테이블 (정확한 컬럼명 사용)
            item = db.query(KContent).filter(KContent.content_id == reference_id).first()
            if item:
                # ✅ 실제 컬럼명 확인
                # drama_name_en, location_name_en, address_en, category_en, keyword_en, trip_tip_en
                
                # 이미지 URL 처리
                image_url = None
                if hasattr(item, 'thumbnail') and item.thumbnail:
                    image_url = item.thumbnail
                elif hasattr(item, 'image_url') and item.image_url:
                    image_url = item.image_url
                elif hasattr(item, 'image_url_list') and item.image_url_list:
                    # image_url_list가 리스트나 JSON 형태인 경우
                    if isinstance(item.image_url_list, list) and len(item.image_url_list) > 0:
                        image_url = item.image_url_list[0]
                    elif isinstance(item.image_url_list, str):
                        # JSON 문자열인 경우 파싱 시도
                        import json
                        try:
                            url_list = json.loads(item.image_url_list)
                            if url_list and len(url_list) > 0:
                                image_url = url_list[0]
                        except:
                            pass
                
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
                        "latitude": float(item.latitude) if item.latitude else None,
                        "longitude": float(item.longitude) if item.longitude else None,
                    }
                }
        
        elif place_type == PlaceType.RESTAURANT:
            # ✅ 음식점 테이블
            item = db.query(Restaurant).filter(Restaurant.restaurant_id == reference_id).first()
            if item:
                return {
                    "name": item.restaurant_name or item.name or "Unknown",
                    "address": item.address or "",
                    "image_url": item.image_url,
                    "latitude": float(item.latitude) if item.latitude else None,
                    "longitude": float(item.longitude) if item.longitude else None,
                    "category": getattr(item, 'category', None) or "",
                    "extra": {
                        "restaurant_id": item.restaurant_id,
                        "restaurant_name": item.restaurant_name,
                        "cuisine_type": getattr(item, 'cuisine_type', None),
                        "address": item.address,
                    }
                }
        
        # elif place_type == PlaceType.ATTRACTION:
        #     # ✅ 명소 테이블 (필요시 활성화)
        #     item = db.query(Attraction).filter(Attraction.attraction_id == reference_id).first()
        #     if item:
        #         return {
        #             "name": item.name or item.title or "Unknown",
        #             "address": item.address or "",
        #             "image_url": item.image_url,
        #             "latitude": float(item.latitude) if item.latitude else None,
        #             "longitude": float(item.longitude) if item.longitude else None,
        #             "category": getattr(item, 'category', None) or "",
        #             "extra": {
        #                 "attraction_id": item.attraction_id,
        #                 "name": item.name,
        #             }
        #         }
        
        elif place_type == PlaceType.FESTIVAL:
            # ✅ 축제 테이블
            item = db.query(Festival).filter(Festival.festival_id == reference_id).first()
            if item:
                return {
                    "name": item.festival_name or getattr(item, 'title', None) or "Unknown",
                    "address": getattr(item, 'address', None) or "",
                    "image_url": getattr(item, 'image_url', None),
                    "latitude": float(item.latitude) if hasattr(item, 'latitude') and item.latitude else None,
                    "longitude": float(item.longitude) if hasattr(item, 'longitude') and item.longitude else None,
                    "category": "festival",
                    "extra": {
                        "festival_id": item.festival_id,
                        "festival_name": item.festival_name,
                        "start_date": str(item.start_date) if hasattr(item, 'start_date') and item.start_date else None,
                        "end_date": str(item.end_date) if hasattr(item, 'end_date') and item.end_date else None,
                    }
                }
        
        return None
    
    except Exception as e:
        print(f"❌ 원본 데이터 조회 실패 (place_type={place_type}, reference_id={reference_id}): {e}")
        import traceback
        traceback.print_exc()
        return None


############################################################
# 1️⃣ 취향 추천 (원본 테이블 데이터 포함)
############################################################
@router.post("/from-bookmarks", response_model=BookmarkBasedRecommendResponse)
def recommend_from_bookmarks(
    req: BookmarkBasedRecommendRequest,
    db: Session = Depends(get_db),
):
    """
    북마크 기반 추천
    - Qdrant로 유사 콘텐츠 찾기
    - 원본 테이블에서 완전한 데이터 가져오기
    """
    # 1) 유저 북마크 가져오기
    query = db.query(Bookmark).filter(Bookmark.user_id == req.user_id)
    if req.place_type is not None:
        query = query.filter(Bookmark.place_type == req.place_type)

    bookmarks = (
        query
        .order_by(Bookmark.created_at.desc())
        .limit(10)
        .all()
    )

    if not bookmarks:
        raise HTTPException(status_code=404, detail="해당 사용자의 북마크가 없습니다.")

    client = get_qdrant_client()
    recommended_items: list[RecommendedItem] = []
    seen_ids = set()  # 중복 제거용

    for b in bookmarks:
        collection_name = PLACE_TYPE_COLLECTION_MAP.get(b.place_type)
        if not collection_name:
            continue

        # 2) Qdrant에서 유사 콘텐츠 추천
        try:
            results = client.recommend(
                collection_name=collection_name,
                positive=[b.reference_id],
                limit=req.top_k_per_bookmark,
            )
        except Exception as e:
            print(f"Qdrant recommend 실패 (bookmark_id={b.bookmark_id}): {e}")
            continue

        # 3) 각 추천 결과에 대해 원본 테이블에서 데이터 가져오기
        for r in results:
            payload = r.payload or {}
            rec_reference_id = payload.get("content_id") or payload.get("id") or r.id
            
            # 중복 체크
            unique_key = f"{b.place_type}_{rec_reference_id}"
            if unique_key in seen_ids:
                continue
            seen_ids.add(unique_key)
            
            # ✅ 원본 테이블에서 완전한 데이터 조회
            original_data = fetch_original_data(db, b.place_type, rec_reference_id)
            
            if original_data:
                # ✅ 원본 데이터 사용 (모든 필드 포함)
                item = RecommendedItem(
                    place_type=b.place_type,
                    reference_id=rec_reference_id,
                    name=original_data["name"],
                    address=original_data.get("address"),
                    image_url=original_data.get("image_url"),
                    latitude=original_data.get("latitude"),
                    longitude=original_data.get("longitude"),
                    score=r.score,
                    extra=original_data.get("extra", {}),  # ✅ 모든 영어 필드 포함!
                )
                print(f"✅ 원본 데이터 사용: {original_data['name']} (extra 필드 개수: {len(original_data.get('extra', {}))})")
            else:
                # 원본 데이터 없으면 Qdrant payload 사용
                item = RecommendedItem(
                    place_type=b.place_type,
                    reference_id=rec_reference_id,
                    name=payload.get("location_name_en") or payload.get("location_name") or payload.get("name") or "Unknown",
                    address=payload.get("address_en") or payload.get("address"),
                    image_url=payload.get("image_url") or payload.get("thumbnail") or payload.get("image"),
                    latitude=payload.get("latitude"),
                    longitude=payload.get("longitude"),
                    score=r.score,
                    extra=payload,
                )
                print(f"⚠️ Qdrant payload 사용: {item.name}")
            
            recommended_items.append(item)

    if not recommended_items:
        raise HTTPException(status_code=404, detail="추천 결과를 찾지 못했습니다.")

    # 점수순 정렬
    recommended_items.sort(key=lambda x: x.score, reverse=True)

    print(f"✅ 총 추천 개수: {len(recommended_items)}")
    return BookmarkBasedRecommendResponse(
        user_id=req.user_id,
        total_count=len(recommended_items),
        items=recommended_items,
    )


############################################################
# 2️⃣ 최근 북마크 기반 추천 (원본 테이블 데이터 포함)
############################################################
@router.post("/from-bookmarks_atleast", response_model=BookmarkBasedRecommendResponse)
def recommend_from_bookmarks_atleast(
    req: BookmarkBasedRecommendRequest,
    db: Session = Depends(get_db),
):
    """
    최근 5개 북마크 기반 추천
    - 원본 테이블에서 완전한 데이터 가져오기
    """
    # 1) 최근 5개 북마크 가져오기
    query = db.query(Bookmark).filter(Bookmark.user_id == req.user_id)
    if req.place_type is not None:
        query = query.filter(Bookmark.place_type == req.place_type)

    bookmarks = (
        query
        .order_by(Bookmark.created_at.desc())
        .limit(5)
        .all()
    )

    if not bookmarks:
        raise HTTPException(status_code=404, detail="해당 사용자의 북마크가 없습니다.")

    client = get_qdrant_client()
    recommended_items: list[RecommendedItem] = []
    seen_ids = set()

    for b in bookmarks:
        collection_name = PLACE_TYPE_COLLECTION_MAP.get(b.place_type)
        if not collection_name:
            continue

        try:
            results = client.recommend(
                collection_name=collection_name,
                positive=[b.reference_id],
                limit=req.top_k_per_bookmark,
            )
        except Exception as e:
            print(f"Qdrant recommend 실패 (bookmark_id={b.bookmark_id}): {e}")
            continue

        for r in results:
            payload = r.payload or {}
            rec_reference_id = payload.get("content_id") or payload.get("id") or r.id
            
            unique_key = f"{b.place_type}_{rec_reference_id}"
            if unique_key in seen_ids:
                continue
            seen_ids.add(unique_key)
            
            # ✅ 원본 테이블에서 데이터 조회
            original_data = fetch_original_data(db, b.place_type, rec_reference_id)
            
            if original_data:
                item = RecommendedItem(
                    place_type=b.place_type,
                    reference_id=rec_reference_id,
                    name=original_data["name"],
                    address=original_data.get("address"),
                    image_url=original_data.get("image_url"),
                    latitude=original_data.get("latitude"),
                    longitude=original_data.get("longitude"),
                    score=r.score,
                    extra=original_data.get("extra", {}),
                )
            else:
                item = RecommendedItem(
                    place_type=b.place_type,
                    reference_id=rec_reference_id,
                    name=payload.get("location_name_en") or payload.get("name") or "Unknown",
                    address=payload.get("address_en") or payload.get("address"),
                    image_url=payload.get("image_url") or payload.get("thumbnail"),
                    latitude=payload.get("latitude"),
                    longitude=payload.get("longitude"),
                    score=r.score,
                    extra=payload,
                )
            
            recommended_items.append(item)

    if not recommended_items:
        raise HTTPException(status_code=404, detail="추천 결과를 찾지 못했습니다.")

    recommended_items.sort(key=lambda x: x.score, reverse=True)

    return BookmarkBasedRecommendResponse(
        user_id=req.user_id,
        total_count=len(recommended_items),
        items=recommended_items,
    )