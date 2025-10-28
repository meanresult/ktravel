"""
FastAPI 메인 애플리케이션
"""
from app.api.endpoints import festival
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import auth, chat, destinations

# FastAPI 앱 생성
app = FastAPI(
    title="Travel Planner API",
    description="AI 기반 여행 계획 플래너 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(destinations.router, prefix="/api")
app.include_router(festival.router)
# Health Check
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
