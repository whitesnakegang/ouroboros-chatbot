# 디렉토리 Ingest 가이드

## 경로 설명

`/upload-directory` 엔드포인트를 사용할 때, **디렉토리 경로는 서버(컨테이너) 내부 경로**여야 합니다.

## Docker 환경에서 사용하기

### 방법 1: 볼륨 마운트 사용 (권장)

#### 1. docker-compose.yml 수정

```yaml
volumes:
  - .:/app
  - vector_db_data:/app/vector_db
  # 문서 디렉토리 마운트 추가
  - /host/path/to/documents:/app/documents
```

예시:
```yaml
volumes:
  - ./docs:/app/documents  # 호스트의 ./docs를 컨테이너의 /app/documents에 마운트
```

#### 2. 컨테이너 재시작

```bash
docker-compose down
docker-compose up -d
```

#### 3. API 호출

```bash
curl -X POST "http://localhost:8000/documents/upload-directory" \
  -F "directory_path=/app/documents" \
  -F "pattern=*.md"
```

### 방법 2: 컨테이너 내부에 파일 복사

#### 1. 파일을 컨테이너에 복사

```bash
docker cp /host/path/to/documents rag-chatbot:/app/documents
```

#### 2. API 호출

```bash
curl -X POST "http://localhost:8000/documents/upload-directory" \
  -F "directory_path=/app/documents" \
  -F "pattern=*.md"
```

### 방법 3: 파일 업로드 사용 (가장 간단)

디렉토리 경로 대신 파일을 직접 업로드:

```bash
curl -X POST "http://localhost:8000/documents/upload-markdown" \
  -F "files=@file1.md" \
  -F "files=@file2.md" \
  -F "files=@file3.md"
```

## 경로 확인 방법

### 컨테이너 내부 경로 확인

```bash
# 컨테이너 내부 접속
docker exec -it rag-chatbot bash

# 현재 작업 디렉토리 확인
pwd

# 파일 목록 확인
ls -la /app

# 마운트된 디렉토리 확인
ls -la /app/documents
```

### 호스트에서 컨테이너 경로 확인

```bash
# 컨테이너의 볼륨 마운트 정보 확인
docker inspect rag-chatbot | grep -A 10 Mounts
```

## 예시 시나리오

### 시나리오 1: 로컬 개발 환경

호스트에 문서가 있는 경우:
```bash
# 호스트 경로: /home/user/my-docs
# docker-compose.yml에 추가:
volumes:
  - /home/user/my-docs:/app/documents

# API 호출:
directory_path=/app/documents
```

### 시나리오 2: 프로덕션 환경

EC2 서버에 문서가 있는 경우:
```bash
# EC2 경로: /var/www/documents
# docker-compose.yml에 추가:
volumes:
  - /var/www/documents:/app/documents

# API 호출:
directory_path=/app/documents
```

### 시나리오 3: Git 저장소에서 문서 가져오기

```bash
# 컨테이너 내부에서
docker exec -it rag-chatbot bash
cd /app
git clone https://github.com/user/docs.git documents

# API 호출:
directory_path=/app/documents
```

## 주의사항

1. **경로는 컨테이너 내부 경로여야 함**
   - ❌ `/home/user/documents` (호스트 경로)
   - ✅ `/app/documents` (컨테이너 내부 경로)

2. **볼륨 마운트가 필요**
   - 호스트의 파일을 사용하려면 반드시 볼륨 마운트 필요
   - 마운트하지 않으면 컨테이너 내부에 파일이 없음

3. **권한 확인**
   - 컨테이너가 파일을 읽을 수 있는 권한이 있는지 확인
   - 필요시 `chmod` 또는 `chown` 사용

4. **상대 경로 vs 절대 경로**
   - 상대 경로: `/app/documents` (컨테이너 내부 기준)
   - 절대 경로도 가능하지만 컨테이너 내부 경로여야 함

## 트러블슈팅

### "Directory not found" 오류

```bash
# 1. 컨테이너 내부에서 경로 확인
docker exec -it rag-chatbot ls -la /app/documents

# 2. 볼륨 마운트 확인
docker inspect rag-chatbot | grep Mounts

# 3. docker-compose.yml 확인
cat docker-compose.yml | grep volumes
```

### 파일을 찾을 수 없음

```bash
# 1. 파일이 실제로 존재하는지 확인
docker exec -it rag-chatbot find /app -name "*.md"

# 2. 패턴 확인
# pattern=*.md (기본값)
# pattern=*.markdown
```

## 권장 방법

**가장 간단하고 안전한 방법:**
1. `docker-compose.yml`에 문서 디렉토리 볼륨 마운트 추가
2. 호스트의 문서를 마운트된 경로에 배치
3. 컨테이너 내부 경로로 API 호출

또는

**파일 업로드 방식 사용:**
- `/upload-markdown` 엔드포인트 사용
- 경로 문제 없이 직접 파일 업로드

