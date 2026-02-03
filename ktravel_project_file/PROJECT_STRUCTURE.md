# Travel Planner 프로젝트 구조

## 📁 전체 디렉토리 구조

```
travel-planner/
├── docker-compose.yml          # Docker 컨테이너 오케스트레이션
├── .env                         # 환경 변수
├── .env.example                 # 환경 변수 예시
├── README.md                    # 프로젝트 설명서
│
├── backend/                     # FastAPI 백엔드
│   ├── Dockerfile
│   ├── requirements.txt         # Python 의존성
│   ├── app/
│   │   ├── main.py             # FastAPI 앱 진입점
│   │   ├── api/
│   │   │   └── endpoints/      # API 엔드포인트들
│   │   │       ├── auth.py     # Phase 1: 인증 (회원가입/로그인)
│   │   │       ├── chat.py     # Phase 1: GPT 채팅
│   │   │       ├── destinations.py  # Phase 1: 여행지 관리
│   │   │       ├── travel_plan.py   # Phase 2: 여행 계획 생성
│   │   │       ├── map.py           # Phase 2: 지도/경로
│   │   │       └── recommendations.py  # Phase 3: 추천 시스템
│   │   ├── core/               # 핵심 설정
│   │   │   ├── config.py       # 환경 설정
│   │   │   ├── security.py     # 비밀번호 해싱
│   │   │   ├── session.py      # 세션 관리 (Redis)
│   │   │   └── deps.py         # 의존성 (인증 체크)
│   │   ├── database/           # 데이터베이스 레이어
│   │   │   ├── connection.py   # DB 연결
│   │   │   ├── queries/        # Raw SQL 쿼리들
│   │   │   │   ├── user_queries.py
│   │   │   │   ├── conversation_queries.py
│   │   │   │   ├── destination_queries.py
│   │   │   │   ├── travel_plan_queries.py
│   │   │   │   └── recommendation_queries.py
│   │   ├── services/           # 비즈니스 로직
│   │   │   ├── auth_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── destination_service.py
│   │   │   ├── travel_plan_service.py
│   │   │   ├── map_service.py
│   │   │   └── recommendation_service.py
│   │   └── utils/              # 유틸리티
│   │       ├── openai_client.py
│   │       ├── kakao_client.py
│   │       └── prompts.py
│   └── tests/                  # 테스트 코드
│
├── frontend/                   # React 프론트엔드
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.js              # 메인 앱
│       ├── index.js            # 진입점
│       ├── components/         # 컴포넌트들
│       │   ├── auth/           # Phase 1: 인증 컴포넌트
│       │   │   ├── LoginForm.js
│       │   │   └── SignupForm.js
│       │   ├── chat/           # Phase 1: 채팅 컴포넌트
│       │   │   ├── ChatContainer.js
│       │   │   ├── ChatMessage.js
│       │   │   └── ChatInput.js
│       │   ├── destinations/   # Phase 1: 여행지 목록
│       │   │   └── DestinationList.js
│       │   ├── map/            # Phase 2: 지도 컴포넌트
│       │   │   ├── KakaoMap.js
│       │   │   └── RouteDisplay.js
│       │   ├── mypage/         # Phase 3: 마이페이지
│       │   │   ├── MyDestinations.js
│       │   │   ├── MyTravelPlans.js
│       │   │   └── Recommendations.js
│       │   └── common/         # 공통 컴포넌트
│       │       ├── Header.js
│       │       ├── Loading.js
│       │       └── ErrorMessage.js
│       ├── pages/              # 페이지들
│       │   ├── LoginPage.js
│       │   ├── SignupPage.js
│       │   ├── DashboardPage.js    # Phase 1: 채팅 페이지
│       │   ├── TravelPlanPage.js   # Phase 2: 여행 계획
│       │   └── MyPage.js           # Phase 3: 마이페이지
│       ├── services/           # API 호출
│       │   ├── api.js          # Axios 설정
│       │   ├── authService.js
│       │   ├── chatService.js
│       │   ├── destinationService.js
│       │   ├── travelPlanService.js
│       │   └── recommendationService.js
│       ├── utils/              # 유틸리티
│       │   └── helpers.js
│       └── styles/             # CSS 파일들
│           ├── App.css
│           └── components.css
│
├── db/                         # 데이터베이스
│   └── init.sql               # 초기 스키마
│
└── notebooks/                  # Jupyter 노트북 (실험용)
    ├── prompt_engineering.ipynb      # 프롬프트 실험
    ├── kakao_api_test.ipynb          # 카카오 API 테스트
    └── recommendation_prototype.ipynb # 추천 알고리즘 프로토타입
```

## 🎯 Phase별 개발 범위

### Phase 1 (Week 1) - 인증 + 채팅 + 여행지 추출
- **Backend**: auth.py, chat.py, destinations.py
- **Frontend**: auth/, chat/, destinations/
- **Database**: users, conversations, destinations 테이블

### Phase 2 (Week 2-3) - 여행 계획 + 지도
- **Backend**: travel_plan.py, map.py
- **Frontend**: map/, TravelPlanPage.js
- **Database**: travel_plans 테이블 추가
- **Notebook**: 카카오 API 실험

### Phase 3 (Week 4) - 추천 시스템
- **Backend**: recommendations.py
- **Frontend**: mypage/, MyPage.js
- **Database**: ChromaDB 연동
- **Notebook**: 추천 알고리즘 프로토타입

### Phase 4 - 통합 + 최적화
- 전체 테스트
- 성능 최적화
- UI/UX 개선

## 📦 기술 스택

### Backend
- FastAPI (웹 프레임워크)
- PyMySQL (MariaDB 연결)
- Redis (세션 저장소)
- OpenAI API (GPT-4o-mini)
- ChromaDB (벡터 DB)

### Frontend
- React 18 (순수 JavaScript)
- Axios (HTTP 클라이언트)
- React Router (라우팅)
- Kakao Maps API (지도)

### Infrastructure
- Docker + Docker Compose
- MariaDB 10.11
- Redis 7
- Nginx (선택사항)
