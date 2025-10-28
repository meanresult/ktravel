from fastapi import Cookie, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.session import session_manager
from app.database.connection import get_db
from app.models.users import User

async def get_current_user(
    session_id: str = Cookie(None, alias="session_id"),
    db: Session = Depends(get_db)
) -> dict:
    """
    현재 로그인한 사용자 정보 가져오기 (ORM 버전)
    
    Args:
        session_id: 쿠키에서 가져온 세션 ID
        db: ORM Session
    
    Returns:
        사용자 정보 딕셔너리
    
    Raises:
        HTTPException: 인증 실패 시
    """
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다"
        )
    
    # 세션 데이터 가져오기
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션이 만료되었습니다. 다시 로그인해주세요"
        )
    
    # 세션 갱신
    session_manager.refresh_session(session_id)
    
    # ORM으로 사용자 정보 가져오기
    user_id = session_data.get("user_id")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # User 객체를 딕셔너리로 변환 (UserResponse 스키마 호환)
    return {
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email,
        'name': user.name,
        'address': user.address,
        'phone': user.phone,
        'gender': user.gender,
        'permit': user.permit,
        'created_at': user.created_at
    }

# 선택적: 관리자 권한 체크
async def get_current_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """관리자 권한 확인"""
    if not current_user.get("permit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user