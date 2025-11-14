# Jenkins CI/CD 설정 가이드 (EC2 Ubuntu)

## 사전 요구사항

### 1. EC2 Ubuntu 인스턴스 설정

```bash
# 시스템 업데이트
sudo apt-get update
sudo apt-get upgrade -y

# 필수 패키지 설치
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget
```

### 2. Docker 설치

```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가 (sudo 없이 docker 실행)
sudo usermod -aG docker $USER
# 또는 Jenkins 사용자 추가
sudo usermod -aG docker jenkins

# 재로그인 또는 그룹 적용
newgrp docker
```

### 3. Jenkins 설치

```bash
# Java 설치 (Jenkins 요구사항)
sudo apt-get install -y openjdk-17-jdk

# Jenkins 저장소 추가
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Jenkins 설치
sudo apt-get update
sudo apt-get install -y jenkins

# Jenkins 서비스 시작
sudo systemctl start jenkins
sudo systemctl enable jenkins

# Jenkins 초기 비밀번호 확인
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### 4. Jenkins 사용자 권한 설정

```bash
# Jenkins 사용자를 docker 그룹에 추가
sudo usermod -aG docker jenkins

# Jenkins 서비스 재시작
sudo systemctl restart jenkins

# 권한 확인
sudo -u jenkins docker ps
```

## Jenkins 파이프라인 설정

### 1. Jenkins 플러그인 설치

Jenkins 웹 UI에서:
- Manage Jenkins → Manage Plugins
- 다음 플러그인 설치:
  - Git
  - Docker Pipeline
  - Docker
  - Pipeline

### 2. 파이프라인 생성

1. Jenkins 대시보드 → "New Item"
2. Pipeline 선택
3. Pipeline 설정:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `https://github.com/your-username/ouroboros-chatbot.git`
   - **Branch Specifier**: `*/develop` 또는 `*/main`
   - **Script Path**: `Jenkinsfile`

### 3. 환경 변수 설정 (선택적)

Jenkins 관리 → 시스템 설정 → Global properties:
- `DOCKER_IMAGE_NAME`: `rag-chatbot` (기본값 사용 가능)

## 보안 그룹 설정 (EC2)

Jenkins 웹 UI 접근을 위해:
- 인바운드 규칙 추가:
  - Type: Custom TCP
  - Port: 8080 (Jenkins 기본 포트)
  - Source: 허용할 IP 주소

## 트러블슈팅

### Docker 권한 오류

```bash
# Jenkins 사용자가 docker 명령어를 실행할 수 있는지 확인
sudo -u jenkins docker ps

# 권한이 없다면
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### Python 가상환경 오류

```bash
# python3-venv 패키지 설치 확인
sudo apt-get install -y python3-venv
```

### Docker Compose 명령어를 찾을 수 없음

```bash
# docker-compose 경로 확인
which docker-compose

# 심볼릭 링크 생성 (필요 시)
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

## 파이프라인 실행 확인

1. Jenkins 대시보드에서 파이프라인 선택
2. "Build Now" 클릭
3. 빌드 로그 확인:
   - 각 스테이지별 실행 상태 확인
   - 오류 발생 시 로그 확인

## 참고사항

- 첫 빌드는 Docker 이미지 다운로드로 인해 시간이 걸릴 수 있습니다
- EC2 인스턴스의 디스크 공간을 충분히 확보하세요 (최소 20GB 권장)
- Docker 이미지가 누적되면 정기적으로 정리하세요:
  ```bash
  docker system prune -a
  ```

