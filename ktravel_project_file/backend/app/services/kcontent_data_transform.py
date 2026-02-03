from typing import Dict, Any, List
from app.models.kcontent import KContent

def transform_kcontent_to_frontend_schema(content: KContent) -> dict:
    # =========================
    # 제목 생성 (영문/한글)
    # =========================
    title_ko = content.drama_name or ""
    title_en = content.drama_name_en or ""

    if title_en and title_ko and title_en != title_ko:
        drama_title = f"{title_en} ({title_ko})"
    elif title_en:
        drama_title = title_en
    else:
        drama_title = title_ko

    # =========================
    # 위치, 설명, 주소
    # =========================
    location_name = content.location_name_en or content.location_name
    description_text = content.trip_tip_en or content.trip_tip
    address_text = content.address_en or content.address

    # =========================
    # 이미지 처리
    # =========================
    thumbnail_url = content.thumbnail or None
    second_url = content.second_image or thumbnail_url  # 두 번째 없으면 썸네일
    third_url = content.third_image or None  # 세 번째 없으면 None

    # =========================
    # 좌표 처리
    # =========================
    latitude = content.latitude or 0
    longitude = content.longitude or 0

    # =========================
    # 최종 반환
    # =========================
    return {
        "id": content.content_id,
        "title": drama_title,        # 영문+한글 조합
        "title_ko": title_ko,       # 한국어
        "title_en": title_en,       # 영어
        "location": location_name,
        "thumbnail": thumbnail_url,
        "image_second": second_url,
        "image_third": third_url,
        "description": description_text,
        "address": address_text,
        "latitude": latitude,       # 위도
        "longitude": longitude,     # 경도
        "liked": False,             # 프론트 기본값
    }



def get_frontend_data_list(kcontents_orm: List[KContent]) -> List[Dict[str, Any]]:
    """
    KContent ORM 객체 리스트를 프론트엔드용 dict 리스트로 변환
    """
    return [transform_kcontent_to_frontend_schema(content) for content in kcontents_orm]
