from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Union
from datetime import datetime

# 기본 스키마
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[str] = Field(None, max_length=10)
    date: Optional[str] = Field(None, max_length=20)  # 생년월일
    permit: Optional[str] = Field(None, max_length=50)  # 권한

# 생성용 스키마 (회원가입)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255)

# 수정용 스키마 (모든 필드 선택적)
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[str] = Field(None, max_length=10)
    date: Optional[str] = Field(None, max_length=20)
    permit: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=255)

# 응답용 스키마 (비밀번호 제외)
class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 로그인용 스키마 (수정됨 - username 또는 email 모두 허용)
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)  # username으로 변경
    password: str

# 이메일 로그인용 별도 스키마 (필요시)
class UserEmailLogin(BaseModel):
    email: EmailStr
    password: str

# 토큰 스키마
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

# 간단한 사용자 정보 (목록용)
class UserSummary(BaseModel):
    user_id: int
    username: str
    name: str
    
    class Config:
        from_attributes = True