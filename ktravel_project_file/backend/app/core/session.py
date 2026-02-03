import redis
import json
import secrets
from datetime import datetime
from app.core.config import settings

# Redis 클라이언트
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class SessionManager:
    """세션 관리 클래스"""
    
    @staticmethod
    def create_session(user_id: int, user_data: dict) -> str:
        """
        세션 생성 및 세션 ID 반환
        
        Args:
            user_id: 사용자 ID
            user_data: 저장할 사용자 정보 (email, name 등)
        
        Returns:
            생성된 세션 ID
        """
        session_id = secrets.token_urlsafe(32)
        session_key = f"session:{session_id}"
        
        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.now().isoformat()
        }
        
        # Redis에 세션 저장 (만료 시간 설정)
        expire_seconds = settings.SESSION_EXPIRE_HOURS * 3600
        redis_client.setex(
            session_key,
            expire_seconds,
            json.dumps(session_data)
        )
        
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> dict:
        """
        세션 ID로 세션 데이터 가져오기
        
        Args:
            session_id: 세션 ID
        
        Returns:
            세션 데이터 딕셔너리 또는 None
        """
        session_key = f"session:{session_id}"
        session_data = redis_client.get(session_key)
        
        if session_data:
            return json.loads(session_data)
        return None
    
    @staticmethod
    def delete_session(session_id: str):
        """
        세션 삭제 (로그아웃)
        
        Args:
            session_id: 삭제할 세션 ID
        """
        session_key = f"session:{session_id}"
        redis_client.delete(session_key)
    
    @staticmethod
    def refresh_session(session_id: str):
        """
        세션 만료 시간 갱신
        
        Args:
            session_id: 갱신할 세션 ID
        """
        session_key = f"session:{session_id}"
        expire_seconds = settings.SESSION_EXPIRE_HOURS * 3600
        redis_client.expire(session_key, expire_seconds)

# 세션 매니저 인스턴스
session_manager = SessionManager()
