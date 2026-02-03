"""
ODsay API 대중교통 경로 검색
ODsay API를 사용한 출발지-도착지 간 대중교통 경로 검색 및 폴리라인 생성
"""
import requests
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import traceback

# 환경 변수에서 ODSAY_API_KEY를 불러옵니다.
ODSAY_API_KEY = os.getenv("ODSAY_API_KEY") 
ODSAY_URL = "https://api.odsay.com/v1/api/searchPubTransPathT?lang=1"

router = APIRouter(
    prefix="/api",
    tags=["kpath-map"],
)

# ----------------------------------------------------
# Pydantic 모델 정의
# ----------------------------------------------------

class RouteRequest(BaseModel):
    """경로 검색 요청 모델"""
    startLat: float = Field(..., description="출발지 위도")
    startLng: float = Field(..., description="출발지 경도")
    endLat: float = Field(..., description="도착지 위도")
    endLng: float = Field(..., description="도착지 경도")

class PathNode(BaseModel):
    """경로의 한 지점 (좌표)"""
    lat: float
    lng: float

class SegmentPath(BaseModel):
    """구간별 폴리라인 및 타입 정보"""
    trafficType: int                     # 1: 지하철, 2: 버스, 3: 도보
    coordinates: List[PathNode]

class RouteResponse(BaseModel):
    """경로 검색 응답 모델 (프론트엔드로 반환)"""
    segmentedPath: List[SegmentPath] = Field(..., description="구간별 교통수단 타입과 좌표 리스트")
    totalTime: int = Field(..., description="총 소요 시간 (분)")
    fare: int = Field(..., description="요금 (원)")
    subPath: List[Dict[str, Any]] = Field(..., description="경로 단계별 상세 정보")
    fullData: Dict[str, Any] = Field(..., description="ODSAY API 원본 응답 데이터 전체")

# ----------------------------------------------------
# 도보/대중교통 영문 변환 로직
# ----------------------------------------------------

TRAFFIC_MAP = {
    1: "Subway",
    2: "Bus",
    3: "Walk"
}

def convert_to_english(sub_path: Dict[str, Any]) -> None:
    """
    subPath 항목을 영문으로 변환
    - trafficName: Subway / Bus / Walk
    - sectionTimeText: "Walk 4 min" 등
    
    Args:
        sub_path: ODsay API의 subPath 항목 (dict)
    """
    traffic_type = sub_path.get('trafficType', 3)
    sub_path['trafficName'] = TRAFFIC_MAP.get(traffic_type, "Unknown")
    
    # 도보일 경우 안내 문구를 Walk X min 형태로
    time_min = sub_path.get('sectionTime', 0)
    if traffic_type == 3:
        sub_path['sectionTimeText'] = f"Walk {time_min} min"
    else:
        sub_path['sectionTimeText'] = f"{time_min} min"

# ----------------------------------------------------
# 경로 검색 엔드포인트
# ----------------------------------------------------

@router.post("/search/route", response_model=RouteResponse)
async def search_route(request: RouteRequest):
    """
    POST /api/search/route
    
    ODsay API를 호출하고 구간별 폴리라인, 상세 경로 정보를 반환합니다.
    
    Args:
        request: RouteRequest {
            startLat: 출발지 위도,
            startLng: 출발지 경도,
            endLat: 도착지 위도,
            endLng: 도착지 경도
        }
        
    Returns:
        RouteResponse {
            segmentedPath: 구간별 좌표 배열,
            totalTime: 총 소요 시간 (분),
            fare: 요금 (원),
            subPath: 경로 상세 정보,
            fullData: ODsay API 원본 응답
        }
        
    Raises:
        HTTPException 500: ODSAY_API_KEY가 설정되지 않음
        HTTPException 404: 경로를 찾을 수 없음
        HTTPException 503: 외부 API 연결 실패
    """
    
    if not ODSAY_API_KEY:
        print("❌ ODSAY_API_KEY not set")
        raise HTTPException(
            status_code=500, 
            detail="서버 환경 설정 오류: ODSAY_API_KEY가 설정되지 않았습니다."
        )

    params = {
        'apiKey': ODSAY_API_KEY, 
        'SX': request.startLng,
        'SY': request.startLat,
        'EX': request.endLng,
        'EY': request.endLat,
        'CID': 1000,
        'output': 'json'
    }

    try:
        print(f"🚀 ODsay API 호출: start=({request.startLat},{request.startLng}), end=({request.endLat},{request.endLng})")
        
        response = requests.get(ODSAY_URL, params=params, timeout=10)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        
        print(f"📦 ODsay API 응답 status: {response.status_code}")

        # error 체크 (dict 또는 list일 수 있음)
        if data.get('error'):
            error = data['error']
            
            # error의 타입에 따라 다르게 처리
            if isinstance(error, dict):
                error_msg = error.get('message', 'Unknown error')
            elif isinstance(error, list) and len(error) > 0:
                error_msg = str(error[0])
            else:
                error_msg = str(error)
            
            print(f"❌ ODsay API Error: {error_msg}")
            raise HTTPException(
                status_code=404, 
                detail=f"ODsay 경로 검색 실패: {error_msg}"
            )

        # result 및 path 존재 확인
        if not data.get('result') or not data['result'].get('path'):
            print("❌ ODsay: 경로 없음")
            raise HTTPException(
                status_code=404, 
                detail="출발지/도착지 사이의 유효한 경로를 찾을 수 없습니다."
            )

        # 첫 번째 경로 선택
        path_result = data['result']['path'][0]

        # 1. 핵심 정보 추출
        total_time = path_result.get('info', {}).get('totalTime', 0)
        fare = path_result.get('info', {}).get('payment', 0)
        sub_paths = path_result.get('subPath', [])
        
        print(f"✅ 경로 찾음: {len(sub_paths)}개 구간, {total_time}분, {fare}원")

        # 2. subPath 항목 영문 변환
        for sub_path in sub_paths:
            convert_to_english(sub_path)

        # 3. 폴리라인 좌표 추출 및 세그먼트 생성
        segmented_paths: List[SegmentPath] = []
        current_segment_coords: List[PathNode] = [
            PathNode(lat=request.startLat, lng=request.startLng)
        ]

        for idx, sub_path in enumerate(sub_paths):
            traffic_type = sub_path.get('trafficType', 3)
            segment_coords = []

            # 이전 구간의 마지막 좌표를 현재 구간의 시작점으로
            if current_segment_coords:
                segment_coords.append(current_segment_coords[-1])

            # 안전한 stations 접근
            pass_stop_list = sub_path.get('passStopList')
            if pass_stop_list:
                stations = pass_stop_list.get('stations')
                
                # stations가 리스트인 경우 (정상)
                if stations and isinstance(stations, list):
                    for station in stations:
                        if isinstance(station, dict):
                            lat = station.get('y')
                            lng = station.get('x')
                            if lat is not None and lng is not None:
                                segment_coords.append(PathNode(lat=lat, lng=lng))
                        else:
                            print(f"⚠️ 구간 {idx}: station이 dict가 아님 - {type(station)}")
                
                # stations가 딕셔너리인 경우 (예외)
                elif stations and isinstance(stations, dict):
                    print(f"⚠️ 구간 {idx}: stations가 dict임 (list 기대) - keys: {list(stations.keys())}")
                    # 필요시 딕셔너리 처리 로직 추가
                
                # stations가 다른 타입인 경우
                elif stations:
                    print(f"⚠️ 구간 {idx}: stations 타입 불명 - {type(stations)}")

            # 안전한 endX/endY 접근
            end_x = sub_path.get('endX')
            end_y = sub_path.get('endY')
            if end_x is not None and end_y is not None:
                segment_coords.append(PathNode(lat=end_y, lng=end_x))

            # 유효한 세그먼트만 추가 (좌표가 2개 이상)
            if len(segment_coords) > 1:
                segmented_paths.append(SegmentPath(
                    trafficType=traffic_type,
                    coordinates=segment_coords
                ))
                print(f"  ✓ 구간 {idx}: {len(segment_coords)}개 좌표")

            current_segment_coords = segment_coords

        # 4. 최종 응답 반환
        return RouteResponse(
            segmentedPath=segmented_paths,
            totalTime=total_time,
            fare=fare,
            subPath=sub_paths,
            fullData=data
        )

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 에러: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code, 
            detail=f"외부 API 통신 오류: HTTP {e.response.status_code}"
        )
    
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 에러: {e}")
        raise HTTPException(
            status_code=503, 
            detail="외부 경로 API와의 연결에 실패했습니다. (Timeout 등)"
        )
    
    except HTTPException:
        # 이미 발생한 HTTPException은 그대로 재발생
        raise
    
    except Exception as e:
        print(f"❌ 서버 내부 오류: {type(e).__name__} - {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"경로 데이터 처리 중 알 수 없는 서버 오류가 발생했습니다."
        )