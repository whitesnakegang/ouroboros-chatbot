# RAG Chatbot

FastAPI 기반의 간단한 RAG (Retrieval-Augmented Generation) 시스템 챗봇입니다.

## 기능

- 문서 임베딩 및 벡터 데이터베이스 저장
- 사용자 쿼리 기반 문서 검색
- 검색된 문서를 컨텍스트로 활용한 LLM 응답 생성

## 설치 및 실행

### Docker를 사용한 실행 (권장)

1. 환경 변수 파일 생성:
```bash
# .env 파일을 생성하고 필요한 API 키 등을 설정하세요
# 예: OPENAI_API_KEY=your_key_here
```

2. Docker Compose로 실행:
```bash
docker-compose up --build
```

또는 백그라운드 실행:
```bash
docker-compose up -d --build
```

3. 컨테이너 중지:
```bash
docker-compose down
```

**참고**: CPU 전용 PyTorch를 사용하여 GPU 패키지 없이 빌드하므로 빌드 시간이 단축됩니다.

### 로컬 환경에서 실행

1. 가상환경 생성 및 활성화:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. 패키지 설치:
```bash
# CPU 전용 PyTorch 설치 (GPU 패키지 제외)
pip install torch==2.2.0+cpu --index-url https://download.pytorch.org/whl/cpu

# 나머지 패키지 설치
pip install -r requirements.txt
```

3. 환경 변수 설정:
```bash
# .env 파일을 생성하고 필요한 API 키 등을 설정하세요
```

4. 서버 실행:
```bash
python main.py
```

또는

```bash
uvicorn app.main:app --reload
```

서버가 실행되면 http://localhost:8000 에서 API를 사용할 수 있습니다.

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 엔드포인트

- `GET /`: API 상태 확인
- `GET /health`: 헬스 체크
- `POST /chat`: 채팅 메시지 전송
- `POST /documents`: 텍스트 문서 추가 (Ingest 파이프라인 실행)
- `POST /documents/upload-html`: HTML 파일 업로드 (React 정적 웹 파일 지원)
- `POST /documents/upload-directory`: 디렉토리 경로로 HTML 파일 일괄 처리
- `GET /documents`: 문서 목록 조회
- `DELETE /documents/{document_id}`: 문서 삭제

## 프로젝트 구조

```
ouro_chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── config.py            # 설정 관리
│   ├── models.py             # Pydantic 모델
│   ├── ingest/               # 문서 처리 파이프라인
│   │   ├── __init__.py
│   │   ├── loader.py         # 문서 로더
│   │   ├── chunker.py        # 문서 청킹
│   │   ├── embedder.py       # 임베딩 생성
│   │   └── pipeline.py       # Ingest 파이프라인
│   └── vectorstore/          # 벡터 스토어
│       ├── __init__.py
│       └── chroma.py         # ChromaDB 관리
├── main.py                   # 애플리케이션 엔트리 포인트
├── requirements.txt          # Python 패키지 의존성
├── Dockerfile                # Docker 이미지 빌드 설정
├── docker-compose.yml        # Docker Compose 설정
├── .dockerignore             # Docker 빌드 시 제외 파일
├── .env                      # 환경 변수 (생성 필요)
└── README.md                 # 프로젝트 설명
```

## Ingest 파이프라인

문서를 벡터 데이터베이스에 저장하는 파이프라인이 구현되어 있습니다:

1. **문서 로딩** (`app/ingest/loader.py`): 텍스트/HTML을 문서 형식으로 변환
2. **문서 청킹** (`app/ingest/chunker.py`): 문서를 작은 청크로 분할
3. **임베딩 생성** (`app/ingest/embedder.py`): multilingual-e5-base 모델 사용 (100개 이상 언어 지원)
4. **벡터 저장** (`app/vectorstore/chroma.py`): ChromaDB에 저장

### 임베딩 모델

현재 사용 중인 모델: **multilingual-e5-base** (`intfloat/multilingual-e5-base`)
- **차원**: 768
- **언어 지원**: 100개 이상의 언어 (한국어 포함)
- **특징**: instruction prefix 자동 적용 (문서: "passage: ", 쿼리: "query: ")
- **장점**: 다국어 환경에서 우수한 성능, 검색 및 의미적 유사도 계산에 최적화

다른 모델로 변경하려면 `.env` 파일에서 설정:
```bash
EMBEDDING_MODEL=intfloat/multilingual-e5-large  

EMBEDDING_MODEL=intfloat/multilingual-e5-small  
```

### React 정적 웹 파일 업로드

React로 빌드된 정적 웹 파일(HTML)을 벡터 DB에 저장할 수 있습니다:

#### 방법 1: 파일 업로드 (multipart/form-data)

```bash
curl -X POST "http://localhost:8000/documents/upload-html" \
  -F "files=@index.html" \
  -F "files=@about.html" \
  -F 'base_metadata={"source": "react-docs", "version": "1.0.0"}'
```

#### 방법 2: 디렉토리 경로 제공

```bash
curl -X POST "http://localhost:8000/documents/upload-directory" \
  -F "directory_path=/path/to/build" \
  -F "pattern=*.html" \
  -F 'base_metadata={"source": "react-docs"}'
```

#### 방법 3: Python 코드 사용

```python
from app.ingest.pipeline import IngestPipeline
from app.ingest.loader import DocumentLoader

# HTML 파일 로드
document = DocumentLoader.load_html_file("index.html")

# 파이프라인 실행
pipeline = IngestPipeline()
result = pipeline.ingest_text(
    text=document["text"],
    metadata=document["metadata"]
)
```

### HTML 파싱 기능

- 스크립트/스타일 태그 자동 제거
- 메인 콘텐츠 영역 자동 감지 (main, article, body)
- 메타데이터 추출 (title, og:url 등)
- 텍스트 정리 및 정규화

### 일반 텍스트 문서 추가

```python
from app.ingest.pipeline import IngestPipeline

# 파이프라인 초기화
pipeline = IngestPipeline()

# 문서 추가
result = pipeline.ingest_text(
    text="문서 내용...",
    metadata={"source": "example.txt"},
    document_id="doc-001"
)

print(f"문서 ID: {result['document_id']}")
print(f"생성된 청크 수: {result['chunks_count']}")
```

## 테스트 방법

### 방법 1: Swagger UI (가장 쉬움)

1. 서버 실행 후 브라우저에서 http://localhost:8000/docs 접속
2. 각 엔드포인트를 클릭하여 "Try it out" 버튼 클릭
3. 파라미터 입력 후 "Execute" 버튼으로 테스트

### 방법 2: Python 테스트 스크립트

```bash
# requests 라이브러리 설치 (이미 requirements.txt에 포함되어 있음)
pip install requests

# 테스트 실행
python test_api.py
```

테스트 스크립트는 다음을 테스트합니다:
- 헬스 체크
- 텍스트 문서 추가
- 문서 목록 조회
- HTML 파일 업로드
- 채팅 기능

### 방법 3: curl 명령어

**Windows:**
```bash
test_commands.bat
```

**Linux/Mac:**
```bash
chmod +x test_commands.sh
./test_commands.sh
```

### 방법 4: 개별 curl 명령어

```bash
# 1. 헬스 체크
curl http://localhost:8000/health

# 2. 텍스트 문서 추가
curl -X POST "http://localhost:8000/documents" \
  -H "Content-Type: application/json" \
  -d '{"text": "테스트 문서 내용", "metadata": {"source": "test"}}'

# 3. HTML 파일 업로드
curl -X POST "http://localhost:8000/documents/upload-html" \
  -F "files=@test_example.html"

# 4. 문서 목록 조회
curl http://localhost:8000/documents

# 5. 채팅 테스트
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

### 방법 5: Postman 또는 Insomnia

1. Postman/Insomnia에서 새 요청 생성
2. URL: `http://localhost:8000/docs` 에서 OpenAPI 스펙 다운로드
3. 또는 각 엔드포인트를 수동으로 추가하여 테스트

## 문제 해결

### PyTorch 호환성 오류

만약 다음과 같은 오류가 발생하면:
```
AttributeError: module 'torch.utils._pytree' has no attribute 'register_pytree_node'
```

**해결 방법:**

1. **Docker 환경:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

2. **로컬 환경:**
   ```bash
   pip install --upgrade torch==2.2.0+cpu --index-url https://download.pytorch.org/whl/cpu
   ```

자세한 내용은 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)를 참고하세요.

### HuggingFace Hub 호환성 오류

만약 다음과 같은 오류가 발생하면:
```
ImportError: cannot import name 'cached_download' from 'huggingface_hub'
```

**해결 방법:**

1. **Docker 환경:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

2. **로컬 환경:**
   ```bash
   pip install huggingface_hub==0.20.2
   ```

자세한 내용은 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)를 참고하세요.

### CPU 전용 빌드

이 프로젝트는 **CPU 전용 PyTorch**를 사용하도록 설정되어 있습니다:
- GPU 패키지(nvidia_cudnn_cu12 등) 설치 제외
- 빌드 시간 단축
- 이미지 크기 감소

GPU가 필요한 경우 Dockerfile과 requirements.txt를 수정하세요.

## 다음 단계

1. RAG 로직 구현 (벡터 검색, LLM 통합)
2. 다양한 문서 형식 지원 (PDF, DOCX 등)
3. 대화 기록 관리 기능 추가
4. 검색 결과 개선 (하이브리드 검색 등)
