# app/core/qdrant_client.py

from qdrant_client import QdrantClient
from typing import Optional

from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

try:
    # 이미 프로젝트에서 쓰고 있는 settings (app.core.config.settings) 우선 사용
    from app.core.config import settings
except ImportError:
    settings = None


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """환경변수 또는 settings에서 값을 가져오는 헬퍼 함수"""
    # 1) settings 객체에 같은 이름의 속성이 있으면 먼저 사용
    if settings is not None and hasattr(settings, name):
        value = getattr(settings, name)
        if value:
            return value

    # 2) 없으면 환경변수에서 읽기
    return os.getenv(name, default)


def get_qdrant_client() -> QdrantClient:
    """
    Qdrant Cloud에 연결된 QdrantClient 인스턴스를 반환하는 함수.

    - URL: QDRANT_HOST
    - API KEY: QDRANT_API_KEY
    """

    # 예: https://xxxxxx.us-west-2-0.aws.cloud.qdrant.io:6333
    qdrant_url = _get_env("QDRANT_URL")
    qdrant_api_key = _get_env("QDRANT_API_KEY")

    #qdrant_url = "https://ed69909d-cb9d-429b-91d2-ba4561747dd5.us-west-2-0.aws.cloud.qdrant.io:6333"
    #qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0._7IYlBzsLmAtoemGjCowUfrUd5rM-3vIxyyJCteGm-Y"
    
    if not qdrant_url:
        raise RuntimeError(
            "QDRANT_URL이 설정되지 않았습니다. .env 또는 환경변수에 QDRANT_URL을 추가해주세요."
        )

    if not qdrant_api_key:
        raise RuntimeError(
            "QDRANT_API_KEY가 설정되지 않았습니다. .env 또는 환경변수에 QDRANT_API_KEY를 추가해주세요."
        )

    # prefer_grpc=False: HTTP로 통신 (Cloud 환경에서 많이 사용)
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        prefer_grpc=False,
    )

    return client

def recommend(
    collection_name: str,
    positive: list[str],
    limit: int = 10,
) -> list:
    """
    Qdrant에서 추천 결과를 가져오는 함수.

    Args:
        collection_name (str): Qdrant 컬렉션 이름
        positive (list[str]): 기준 포인트 ID 리스트
        limit (int): 추천 결과 개수

    Returns:
        list: 추천 결과 리스트
    """
    client = get_qdrant_client()
    results = client.recommend(
        collection_name=collection_name,
        positive=positive,
        limit=limit,
    )
    return results
