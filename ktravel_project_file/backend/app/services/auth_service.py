"""
인증 서비스 (ORM 버전 - username 전용)
"""
from app.core.security import verify_password, get_password_hash
from app.core.session import session_manager
from app.models.users import User
from sqlalchemy.orm import Session

class AuthService:
    """인증 관련 비즈니스 로직 (ORM 버전)"""
    
    @staticmethod
    def signup(db: Session, username: str, email: str, password: str, name: str, **kwargs):
        """회원가입 (ORM 버전)"""
        # 아이디 중복 체크
        if db.query(User).filter(User.username == username).first():
            raise Exception("이미 사용 중인 아이디입니다")
        
        # 이메일 중복 체크
        if db.query(User).filter(User.email == email).first():
            raise Exception("이미 사용 중인 이메일입니다")
        
        # 비밀번호 해싱
        hashed_password = get_password_hash(password)
        
        # 사용자 생성
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            name=name,
            address=kwargs.get('address'),
            phone=kwargs.get('phone'),
            gender=kwargs.get('gender'),
            date=kwargs.get('date')
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def login(db: Session, username: str, password: str):
        """로그인 (username 전용)"""
        # 사용자 찾기 (username으로만)
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise Exception("아이디 또는 비밀번호가 올바르지 않습니다")
        
        # 비밀번호 확인
        if not verify_password(password, user.password):
            raise Exception("아이디 또는 비밀번호가 올바르지 않습니다")
        
        # 세션 생성
        session_id = session_manager.create_session(
            user_id=user.user_id,
            user_data={
                'username': user.username,
                'email': user.email,
                'name': user.name
            }
        )
        
        return session_id, user
    
    @staticmethod
    def logout(session_id: str):
        """로그아웃"""
        session_manager.delete_session(session_id)