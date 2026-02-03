# Travel Planner Phase 1 - 설치 및 실행 가이드 🚀

## 📦 Phase 1 완성 내용

### ✅ Backend (FastAPI)
- 회원가입 / 로그인 / 로그아웃 (세션 기반)
- GPT-4o-mini 채팅
- 대화에서 여행지 자동 추출 및 저장
- 여행지 목록 조회 / 삭제
- Raw SQL 쿼리 방식

### ✅ Frontend (React)
- 로그인 / 회원가입 페이지
- 채팅 인터페이스
- 실시간 GPT 응답
- 여행지 목록 사이드바
- 여행지 삭제 기능

### ✅ Infrastructure
- Docker Compose
- MariaDB 10.11
- Redis 7 (세션 저장소)

---

## 🔧 설치 방법

### 1️⃣ 압축 파일 해제

```bash
cd ~/kcult
tar -xzf travel-planner-phase1-complete.tar.gz
cd travel-planner
```

### 2️⃣ 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**.env 파일 내용:**
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**중요:** 실제 OpenAI API 키를 입력해야 합니다!

### 3️⃣ Docker 실행

```bash
docker-compose up -d
```

### 4️⃣ 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# Backend 로그만
docker-compose logs -f backend

# Frontend 로그만
docker-compose logs -f frontend
```

---

## 🌐 접속 URL

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📋 사용 방법

### 1. 회원가입
1. http://localhost:3000 접속
2. "회원가입" 클릭
3. 정보 입력 후 가입

### 2. 로그인
1. 이메일과 비밀번호로 로그인

### 3. 채팅
1. 대시보드에서 채팅창에 메시지 입력
2. 예시: "제주도랑 부산 가고 싶어요!"
3. GPT가 응답하고 자동으로 여행지가 오른쪽에 추가됨

### 4. 여행지 관리
- 오른쪽 사이드바에서 여행지 목록 확인
- ✕ 버튼으로 삭제 가능

---

## 🛠️ Docker 명령어

### 컨테이너 중지
```bash
docker-compose stop
```

### 컨테이너 시작
```bash
docker-compose start
```

### 컨테이너 재시작
```bash
docker-compose restart
```

### 컨테이너 완전 삭제 (DB 데이터 유지)
```bash
docker-compose down
```

### 컨테이너 + 데이터 완전 삭제
```bash
docker-compose down -v
```

### 이미지 재빌드
```bash
docker-compose up -d --build
```

---

## 🐛 문제 해결

### 포트 충돌 (3306, 6379, 3000, 8000)
```bash
# 사용 중인 포트 확인
sudo lsof -i :3306
sudo lsof -i :6379
sudo lsof -i :3000
sudo lsof -i :8000

# 기존 프로세스 종료
sudo kill -9 [PID]

# 또는 docker-compose.yml에서 포트 변경
```

### Backend 오류
```bash
# 로그 확인
docker-compose logs backend

# 컨테이너 재시작
docker-compose restart backend

# 컨테이너 접속
docker exec -it travel_backend bash
```

### Frontend 오류
```bash
# 로그 확인
docker-compose logs frontend

# 컨테이너 재시작
docker-compose restart frontend

# node_modules 재설치
docker-compose exec frontend npm install
```

### DB 연결 오류
```bash
# DB 상태 확인
docker-compose exec db mysql -u travel_user -ptravel_password travel_planner

# DB 재시작
docker-compose restart db
```

---

## 📁 프로젝트 구조

```
travel-planner/
├── docker-compose.yml
├── .env
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── api/endpoints/
│       │   ├── auth.py
│       │   ├── chat.py
│       │   └── destinations.py
│       ├── core/
│       ├── database/
│       ├── services/
│       └── utils/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.js
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── styles/
└── db/
    └── init.sql
```

---

## 🔑 API 엔드포인트

### 인증
- `POST /api/auth/signup` - 회원가입
- `POST /api/auth/login` - 로그인
- `POST /api/auth/logout` - 로그아웃
- `GET /api/auth/me` - 내 정보

### 채팅
- `POST /api/chat/send` - 메시지 전송
- `GET /api/chat/history` - 대화 히스토리

### 여행지
- `GET /api/destinations` - 여행지 목록
- `GET /api/destinations/stats` - 통계
- `DELETE /api/destinations/{id}` - 여행지 삭제

---

## 🚀 다음 단계 (Phase 2)

Phase 1 완료 후:
- 여행 계획 생성 (GPT)
- 카카오 지도 연동
- 경로 표시
- 대중교통 안내

---

## 📞 지원

문제가 발생하면:
1. 로그 확인 (`docker-compose logs`)
2. .env 파일 확인 (OPENAI_API_KEY)
3. 포트 충돌 확인
4. Docker 재시작

**성공적인 Phase 1 완료를 축하합니다!** 🎉
