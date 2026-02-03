from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.sql import func
from app.database.connection import Base  # Base 정의되어 있다고 가정

class KContent(Base):
    __tablename__ = "k_contents_trans"  # 실제 테이블명

    # 기본 식별자
    content_id = Column(Integer, primary_key=True, index=True)
    
    # 한국어 주요 필드 (VARCHAR 255)
    drama_name = Column(String(255), nullable=True, index=True) 
    location_name = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    keyword = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)

    # 한국어 TEXT 필드
    trip_tip = Column(Text, nullable=True)
    drama_desc = Column(Text, nullable=True)

    # 영어 필드 (VARCHAR 255)
    location_name_en = Column(String(255), nullable=True)
    drama_name_en = Column(String(255), nullable=True)
    address_en = Column(String(255), nullable=True)
    category_en = Column(String(255), nullable=True)
    keyword_en = Column(String(255), nullable=True)

    # 영어 TEXT 필드
    trip_tip_en = Column(Text, nullable=True)
    
    # 미디어/위치 정보
    image_url = Column(Text, nullable=True) 
    image_url_list = Column(Text, nullable=True)  # 리스트를 TEXT로 저장
    thumbnail = Column(Text, nullable=True)
    second_image = Column(Text, nullable=True)
    third_image = Column(Text, nullable=True)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    def to_dict(self):
        """
        딕셔너리 변환 메서드 (ChatService 등에서 사용 가능)
        """
        return {
            'content_id': self.content_id,
            'drama_name': self.drama_name,
            'location_name': self.location_name,
            'address': self.address,
            'trip_tip': self.trip_tip,
            'keyword': self.keyword,
            'category': self.category,
            'location_name_en': self.location_name_en,
            'drama_name_en': self.drama_name_en,
            'address_en': self.address_en,
            'category_en': self.category_en,
            'keyword_en': self.keyword_en,
            'trip_tip_en': self.trip_tip_en,
            'image_url': self.image_url,
            'image_url_list': self.image_url_list,
            'thumbnail': self.thumbnail,
            'second_image': self.second_image,
            'third_image': self.third_image,
            'drama_desc': self.drama_desc,
            'latitude': float(self.latitude) if self.latitude is not None else None,
            'longitude': float(self.longitude) if self.longitude is not None else None,
        }
    
    def __repr__(self):
        return f"<KContent(content_id={self.content_id}, drama_name='{self.drama_name}')>"
