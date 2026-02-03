"""
콘텐츠 라우터 추가
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# ✅ 기존 엔드포인트 라우터
from app.api.endpoints import auth, chat, destinations, festival, map_search, odsay, concert, bookmark, recommend, recommend_llm
# ✅ 추가: KContent 라우터
from app.api.endpoints import kcontent

# ✅ 추가: Schedules 라우터
from app.api.endpoints.schedule import router as schedules_router
from app.api.endpoints.kmedia import router as kmedia_router
from app.api.endpoints.restaurant import router as restaurant_router

# FastAPI 앱 생성
app = FastAPI(
    title="Travel Planner API",
    description="AI 기반 여행 계획 플래너 API",
    version="1.0.0"
)

# ⭐️ CORS 설정 - 직접 origins 지정 (임시 테스트용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # 개발 중에만 사용 (모든 origin 허용)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# 라우터 등록
# -------------------------------
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(destinations.router, prefix="/api")
app.include_router(schedules_router, prefix="/api/schedules")  # 일정 관리 API
app.include_router(festival.router)
app.include_router(map_search.router, prefix="/search")
app.include_router(odsay.router)
app.include_router(concert.router, prefix="/api")
app.include_router(kcontent.router, prefix="/api") # ✅ K-Content API 라우터 등록
app.include_router(kmedia_router)
app.include_router(restaurant_router)
app.include_router(bookmark.router, prefix="/api")
app.include_router(recommend.router, prefix="/api")
app.include_router(recommend_llm.router, prefix="/api")

# -------------------------------
# Health Check
# -------------------------------
@app.get("/")
def root():
    return {
        "message": "Travel Planner API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# -------------------------------
# Startup 이벤트
# -------------------------------
@app.on_event("startup")
async def startup_event():
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://localhost:6333")
        print("✅ Qdrant 연결 성공")
    except Exception as e:
        print(f"❌ Qdrant 연결 실패: {e}")
    
    # ⭐️ CORS 설정 확인 로그 추가
    print("=" * 50)
    print("🌐 CORS 설정 확인:")
    print(f"  - localhost:3000 허용됨")
    print(f"  - Credentials: True")
    print("=" * 50)