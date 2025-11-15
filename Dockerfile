# Python 베이스 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (lxml, chromadb 등에 필요)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# pip 업그레이드
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# requirements.txt 복사
COPY requirements.txt .

# PyTorch CPU 버전을 먼저 설치 (별도 인덱스 사용)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.2.0

# constraints 파일 생성 (torch 버전 고정)
RUN echo "torch==2.2.0" > /tmp/constraints.txt

# 나머지 패키지 설치 (torch 버전 제약 조건 적용)
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -c /tmp/constraints.txt \
    -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 벡터 DB 디렉토리 생성
RUN mkdir -p /app/vector_db

# 포트 노출
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

