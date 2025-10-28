import hashlib

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 해시된 비밀번호 비교"""
    # SHA256 해싱으로 비교
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    # SHA256을 사용한 간단한 해싱
    return hashlib.sha256(password.encode()).hexdigest()