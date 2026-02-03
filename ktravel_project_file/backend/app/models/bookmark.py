# backend/app/models/bookmark.py

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from app.database.connection import Base


class Bookmark(Base):
    __tablename__ = "bookmark"

    bookmark_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    # 기본 정보
    name = Column(String(255), nullable=False)
    extracted_from_convers_id = Column(Integer, nullable=True, server_default="0")
    place_type = Column(Integer, nullable=False)
    reference_id = Column(Integer, nullable=False)

    # 위치 정보
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)

    # 이미지 & 메모
    image_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # ✅ K-콘텐츠 영어 정보 (DB 테이블과 일치)
    location_name = Column(String(255), nullable=True)  # location_name_en → location_name
    address = Column(String(255), nullable=True)        # address_en → address
    category = Column(String(255), nullable=True)       # category_en → category
    keyword = Column(String(255), nullable=True)        # keyword_en → keyword
    trip_tip = Column(Text, nullable=True)              # trip_tip_en → trip_tip

    # ---------------------------------
    # Helper 메서드들
    # ---------------------------------
    @classmethod
    def add_bookmark(
        cls,
        db: Session,
        user_id: int,
        name: str,
        place_type: int,
        reference_id: int,
        location_name_en: str | None = None,
        address_en: str | None = None,
        category_en: str | None = None,
        keyword_en: str | None = None,
        trip_tip_en: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        image_url: str | None = None,
        notes: str | None = None,
        extracted_from_convers_id: int | None = 0,
    ) -> "Bookmark":
        """
        북마크 생성
        - 파라미터는 _en 형식으로 받지만
        - DB 컬럼에는 _en 없이 저장
        """
        new_bm = cls(
            user_id=user_id,
            name=name,
            place_type=place_type,
            reference_id=reference_id,
            # ✅ 영어 정보를 _en 없는 컬럼에 저장
            location_name=location_name_en,
            address=address_en,
            category=category_en,
            keyword=keyword_en,
            trip_tip=trip_tip_en,
            latitude=latitude,
            longitude=longitude,
            image_url=image_url,
            notes=notes,
            extracted_from_convers_id=extracted_from_convers_id,
        )
        db.add(new_bm)
        db.commit()
        db.refresh(new_bm)
        return new_bm

    @classmethod
    def delete_bookmark(cls, db: Session, bookmark_id: int, user_id: int) -> None:
        """
        북마크 삭제 (user_id 체크)
        """
        q = db.query(cls).filter(
            cls.bookmark_id == bookmark_id,
            cls.user_id == user_id
        )
        obj = q.first()
        if not obj:
            raise ValueError("Bookmark not found or not owned by this user")

        db.delete(obj)
        db.commit()

    def to_dict(self):
        """
        딕셔너리 변환
        - API 응답에서 _en 형식으로 반환
        """
        return {
            "bookmark_id": self.bookmark_id,
            "user_id": self.user_id,
            "name": self.name,
            "place_type": self.place_type,
            "reference_id": self.reference_id,
            # ✅ DB 컬럼(_en 없음) → API 응답(_en 있음)
            "location_name_en": self.location_name,
            "address_en": self.address,
            "category_en": self.category,
            "keyword_en": self.keyword,
            "trip_tip_en": self.trip_tip,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "image_url": self.image_url,
            "notes": self.notes,
            "extracted_from_convers_id": self.extracted_from_convers_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }