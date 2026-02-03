# backend/app/api/endpoints/bookmark.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.bookmark import Bookmark
from app.schemas.bookmarkschema import BookmarkCreate, BookmarkListResponse

router = APIRouter(prefix="/bookmark", tags=["bookmark"])


# 1️⃣ 북마크 생성
@router.post("", response_model=BookmarkListResponse)
def add_bookmark(data: BookmarkCreate, db: Session = Depends(get_db)):
    """
    북마크 생성
    - KMediaPage에서 보내는 데이터를 그대로 저장
    - reference_id = K-콘텐츠의 원본 ID
    """
    try:
        print(f"📥 북마크 생성 요청: user_id={data.user_id}, name={data.name}")
        
        new_bookmark = Bookmark.add_bookmark(
            db=db,
            user_id=data.user_id,
            name=data.name,
            place_type=data.place_type,
            reference_id=data.reference_id,
            location_name_en=data.location_name,  # API는 location_name, DB는 location_name
            address_en=data.address,
            category_en=data.category,
            keyword_en=data.keyword,
            trip_tip_en=data.trip_tip_en,
            latitude=data.latitude,
            longitude=data.longitude,
            image_url=data.image_url,
            notes=data.notes,
            extracted_from_convers_id=data.extracted_from_convers_id or 0,
        )

        print(f"✅ 북마크 생성 성공: bookmark_id={new_bookmark.bookmark_id}")

        # to_dict()를 사용하여 응답 생성
        bookmark_dict = new_bookmark.to_dict()
        
        return BookmarkListResponse(
            bookmark_id=bookmark_dict["bookmark_id"],
            user_id=bookmark_dict["user_id"],
            name=bookmark_dict["name"],
            place_type=bookmark_dict["place_type"],
            reference_id=bookmark_dict["reference_id"],
            location_name_en=bookmark_dict.get("location_name_en"),
            address_en=bookmark_dict.get("address_en"),
            category_en=bookmark_dict.get("category_en"),
            keyword_en=bookmark_dict.get("keyword_en"),
            trip_tip_en=bookmark_dict.get("trip_tip_en"),
            latitude=bookmark_dict.get("latitude"),
            longitude=bookmark_dict.get("longitude"),
            image_url=bookmark_dict.get("image_url"),
            notes=bookmark_dict.get("notes"),
            extracted_from_convers_id=bookmark_dict.get("extracted_from_convers_id", 0),
            created_at=new_bookmark.created_at,
        )
    except Exception as e:
        print(f"❌ 북마크 생성 실패: {e}")
        raise HTTPException(status_code=400, detail=f"북마크 생성 실패: {str(e)}")


# 2️⃣ 북마크 목록 조회
@router.get("/{user_id}", response_model=list[BookmarkListResponse])
def list_bookmarks(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 모든 북마크 조회
    - reference_id를 그대로 반환 (추천 시스템에서 사용)
    """
    try:
        print(f"📥 북마크 조회 요청: user_id={user_id}")
        
        bookmarks = db.query(Bookmark).filter(Bookmark.user_id == user_id).all()
        
        print(f"✅ 북마크 조회 성공: {len(bookmarks)}개")

        results = []
        for bm in bookmarks:
            bm_dict = bm.to_dict()
            results.append(
                BookmarkListResponse(
                    bookmark_id=bm_dict["bookmark_id"],
                    user_id=bm_dict["user_id"],
                    name=bm_dict["name"],
                    place_type=bm_dict["place_type"],
                    reference_id=bm_dict["reference_id"],
                    location_name_en=bm_dict.get("location_name_en"),
                    address_en=bm_dict.get("address_en"),
                    category_en=bm_dict.get("category_en"),
                    keyword_en=bm_dict.get("keyword_en"),
                    trip_tip_en=bm_dict.get("trip_tip_en"),
                    latitude=bm_dict.get("latitude"),
                    longitude=bm_dict.get("longitude"),
                    image_url=bm_dict.get("image_url"),
                    notes=bm_dict.get("notes"),
                    extracted_from_convers_id=bm_dict.get("extracted_from_convers_id", 0),
                    created_at=bm.created_at,
                )
            )

        return results
    except Exception as e:
        print(f"❌ 북마크 조회 실패: {e}")
        raise HTTPException(status_code=400, detail=f"북마크 조회 실패: {str(e)}")


# 3️⃣ 북마크 삭제
@router.delete("/{bookmark_id}/{user_id}")
def delete_bookmarks(bookmark_id: int, user_id: int, db: Session = Depends(get_db)):
    """
    북마크 삭제
    - bookmark_id와 user_id를 모두 확인
    """
    try:
        print(f"📥 북마크 삭제 요청: bookmark_id={bookmark_id}, user_id={user_id}")
        
        Bookmark.delete_bookmark(
            db=db,
            bookmark_id=bookmark_id,
            user_id=user_id,
        )
        
        print(f"✅ 북마크 삭제 성공")
        return {"detail": "Bookmark deleted successfully"}
    except ValueError as e:
        print(f"❌ 북마크 삭제 실패 (Not Found): {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ 북마크 삭제 실패: {e}")
        raise HTTPException(status_code=400, detail=f"북마크 삭제 실패: {str(e)}")


# 4️⃣ 추천을 위한 reference_id 목록 조회
@router.get("/{user_id}/reference-ids")
def get_reference_ids(user_id: int, place_type: int = None, db: Session = Depends(get_db)):
    """
    추천 시스템을 위한 reference_id 목록 반환
    
    Args:
        user_id: 사용자 ID
        place_type: 필터링할 place_type (선택)
    
    Returns:
        { "reference_ids": [123, 456, 789] }
    """
    try:
        query = db.query(Bookmark.reference_id).filter(Bookmark.user_id == user_id)
        
        if place_type is not None:
            query = query.filter(Bookmark.place_type == place_type)
        
        bookmarks = query.all()
        reference_ids = [bm.reference_id for bm in bookmarks]
        
        print(f"✅ reference_id 조회 성공: {len(reference_ids)}개")
        return {"reference_ids": reference_ids}
    except Exception as e:
        print(f"❌ reference_id 조회 실패: {e}")
        raise HTTPException(status_code=400, detail=f"reference_id 조회 실패: {str(e)}")