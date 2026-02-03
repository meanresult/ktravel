from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Any

from app.schemas.kcontent_schema import KContentCreate, KContentEdit, KContentResponse
from app.models.kcontent import KContent
from app.database.connection import get_db
from app.services.kcontent_data_transform import get_frontend_data_list, transform_kcontent_to_frontend_schema

router = APIRouter(
    prefix="/kcontents",
    tags=["KContent"]
)

# =========================
# CRUD - READ (전체/단일)
# =========================
@router.get("/", response_model=List[Dict[str, Any]])
def read_kcontents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    전체 K-콘텐츠 목록 조회 및 프론트엔드 카드 형식으로 반환
    """
    try:
        contents_orm = db.query(KContent)\
            .order_by(KContent.content_id.desc())\
            .offset(skip).limit(limit).all()
        return get_frontend_data_list(contents_orm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"K-Content 조회 오류: {str(e)}")


@router.get("/{content_id}", response_model=Dict[str, Any])
def read_kcontent(content_id: int, db: Session = Depends(get_db)):
    """
    특정 K-콘텐츠 항목 조회 및 프론트엔드 형식으로 반환
    """
    try:
        content_orm = db.query(KContent).filter(KContent.content_id == content_id).first()
        if not content_orm:
            raise HTTPException(status_code=404, detail="K-Content not found")
        return transform_kcontent_to_frontend_schema(content_orm)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"K-Content 조회 오류: {str(e)}")


# =========================
# 검색/필터링
# =========================
@router.get("/search/query", response_model=List[Dict[str, Any]])
def search_kcontents(q: str = Query(..., description="검색어 (2글자 이상)", min_length=2),
                     db: Session = Depends(get_db)):
    """
    드라마 이름, 지역 이름, 키워드, trip_tip, drama_desc 검색
    """
    try:
        search_term = f"%{q}%"
        contents_orm = db.query(KContent).filter(
            or_(
                KContent.drama_name.like(search_term),
                KContent.drama_name_en.like(search_term),
                KContent.location_name.like(search_term),
                KContent.location_name_en.like(search_term),
                KContent.keyword.like(search_term),
                KContent.trip_tip.like(search_term),
                KContent.trip_tip_en.like(search_term),
                KContent.drama_desc.like(search_term)
            )
        ).order_by(KContent.content_id.desc()).limit(100).all()
        return get_frontend_data_list(contents_orm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"K-Content 검색 오류: {str(e)}")


@router.get("/search/category", response_model=List[Dict[str, Any]])
def filter_by_category(category: str = Query(..., description="검색할 카테고리"),
                       db: Session = Depends(get_db)):
    """
    카테고리 필드를 기준으로 K-콘텐츠 목록 필터링
    """
    try:
        contents_orm = db.query(KContent).filter(
            or_(
                KContent.category == category,
                KContent.category_en == category
            )
        ).order_by(KContent.content_id.desc()).all()
        return get_frontend_data_list(contents_orm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카테고리 필터링 오류: {str(e)}")


# =========================
# CRUD - CREATE / UPDATE / DELETE
# =========================
@router.post("/", response_model=KContentResponse)
def create_kcontent(item: KContentCreate, db: Session = Depends(get_db)):
    new_content = KContent(**item.dict())
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    return new_content


@router.put("/{content_id}", response_model=KContentResponse)
def update_kcontent(content_id: int, item: KContentEdit, db: Session = Depends(get_db)):
    content = db.query(KContent).filter(KContent.content_id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="K-Content not found")
    for key, value in item.dict(exclude_unset=True).items():
        setattr(content, key, value)
    db.commit()
    db.refresh(content)
    return content


@router.delete("/{content_id}", status_code=204)
def delete_kcontent(content_id: int, db: Session = Depends(get_db)):
    content = db.query(KContent).filter(KContent.content_id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="K-Content not found")
    db.delete(content)
    db.commit()
    return None


