"""
Map Search & Geocoding API
Google Geocoding API를 사용한 장소 좌표 검색
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    tags=["Map Search & Geocoding"],
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"


async def get_coordinates_from_google(query: str) -> Dict[str, float]:
    """
    Google Geocoding API로 좌표를 조회하는 함수
    
    Args:
        query: 검색할 장소 이름 또는 주소
        
    Returns:
        Dict[str, float]: {"latitude": float, "longitude": float} 또는 None
    """
    params = {
        "address": query,
        "key": GOOGLE_API_KEY,
        "language": "ko"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(GEOCODING_URL, params=params, timeout=10)
            data = response.json()

            print(f"🔍 Google API Status: {data.get('status')}")
            
            # 상태 체크
            if data.get("status") != "OK":
                print(f"❌ Google API Error: {data.get('status')} - {data.get('error_message', 'No message')}")
                return None

            # results 존재 확인
            results = data.get("results", [])
            if not results:
                print(f"❌ No results for: {query}")
                return None

            # 안전한 접근
            location = results[0].get("geometry", {}).get("location", {})
            
            if not location or "lat" not in location or "lng" not in location:
                print(f"❌ Invalid location data: {query}")
                return None

            print(f"✅ Found coords: lat={location['lat']}, lng={location['lng']}")
            return {
                "latitude": location["lat"],
                "longitude": location["lng"]
            }
    
    except httpx.TimeoutException:
        print(f"❌ Google API Timeout for: {query}")
        return None
    except Exception as e:
        print(f"❌ Google API Exception: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        return None


@router.get("/location", response_model=Dict[str, Any])
async def search_location_endpoint(
    query: str = Query(..., description="검색할 장소 이름 또는 주소")
):
    """
    GET /search/location
    
    구글 Geocoding API를 호출하여 장소의 좌표를 반환합니다.
    
    Args:
        query: 검색할 장소 이름 (예: "서울대학교", "강남역")
        
    Returns:
        {
            "query": "서울대학교",
            "latitude": 37.4601,
            "longitude": 126.9520,
            "message": "'서울대학교' 좌표 조회 성공"
        }
        
    Raises:
        HTTPException 500: GOOGLE_API_KEY가 설정되지 않음
        HTTPException 404: 좌표를 찾을 수 없음
    """
    
    print(f"📍 Location search request: {query}")
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY not set") 
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY가 설정되지 않았습니다. 환경변수를 확인해주세요."
        )

    coords = await get_coordinates_from_google(query)

    if not coords:
        raise HTTPException(
            status_code=404,
            detail=f"'{query}'에 대한 좌표를 찾을 수 없습니다. 검색어를 확인해주세요."
        )

    return {
        "query": query,
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "message": f"'{query}' 좌표 조회 성공"
    }