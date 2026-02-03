FROM node:18-alpine

WORKDIR /app

# 빌드 시 환경변수 받기 (중요!)
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# package.json 및 lock 파일 복사
COPY package*.json ./

# npm 설정 및 캐시 클리어
# npm install을 시도하기 전에 설정을 먼저 적용합니다.
RUN npm config set fetch-retry-maxtimeout 120000 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm cache clean --force

# 🚀 모든 종속성 및 명시적 패키지 설치 블록 통합 🚀
# 1. package.json에 정의된 기본 패키지 설치
# 2. 누락되었거나 명시적으로 필요한 패키지들을 모두 한 줄에 설치
RUN npm install --loglevel verbose && \
    npm install \
    @hello-pangea/dnd@^18.0.1 \
    framer-motion@^12.23.24 \
    react-icons@^4.12.0 \
    react-calendar@^4.6.1 \
    @mui/material@^5.15.13 \
    @mui/icons-material@^5.15.13 \
    @emotion/react@^11.11.4 \
    @emotion/styled@^11.11.0 \
    lucide-react@^0.548.0

# 설치 확인 (이 부분은 디버깅용으로 유지)
RUN echo "=== Checking installed packages ===" && \
    ls -la node_modules/framer-motion && \
    ls -la node_modules/react-icons && \
    ls -la node_modules/react-calendar && \
    ls -la node_modules/@mui/icons-material && \
    ls -la node_modules/@emotion

COPY . .

EXPOSE 3000

CMD ["npm", "start"]