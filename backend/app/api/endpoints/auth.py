"""
인증 API 엔드포인트 (Authorization 헤더 방식)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.auth_service import AuthService
from app.schemas import (
    UserCreate,
    UserResponse,
    UserLogin
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse)
def signup(
    request: UserCreate,
    db: Session = Depends(get_db)
):
    """회원가입"""
    try:
        user = AuthService.signup(
            db=db,
            username=request.username,
            email=request.email,
            password=request.password,
            name=request.name,
            address=request.address,
            phone=request.phone,
            gender=request.gender,
            date=request.date
        )
        
        return user
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(
    request: UserLogin,
    db: Session = Depends(get_db)
):
    """로그인 (아이디 기반) - Authorization 헤더 방식"""
    try:
        session_id, user = AuthService.login(
            db=db,
            username=request.username,
            password=request.password
        )
        
        # JSON 응답으로 session_id 반환 (쿠키 대신)
        return {
            "status": "success",
            "message": "로그인 성공",
            "session_id": session_id,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "name": user.name,
                "email": user.email,
                "address": user.address,
                "phone": user.phone,
                "gender": user.gender,
                "permit": user.permit,
                "created_at": user.created_at
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
def logout(
    current_user: dict = Depends(get_current_user)
):
    """로그아웃 - Authorization 헤더 방식"""
    try:
        # get_current_user에서 이미 session_id를 검증했으므로
        # session_id를 직접 가져와서 삭제
        from fastapi import Header
        
        # 실제로는 이 함수를 호출하기 전에 이미 session_id가 검증됨
        # 별도 로직 없이 클라이언트에서 localStorage.removeItem 하도록 안내
        
        return {"status": "success", "message": "로그아웃 되었습니다"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """현재 로그인한 사용자 정보"""
    return current_user

@router.get("/check-session")
async def check_session(
    current_user: dict = Depends(get_current_user)
):
    """세션 상태 확인 (디버깅용)"""
    try:
        return {
            "session": True,
            "user_data": {
                "user_id": current_user.get("user_id"),
                "username": current_user.get("username"),
                "name": current_user.get("name")
            }
        }
    except Exception as e:
        return {"session": False, "error": str(e)}