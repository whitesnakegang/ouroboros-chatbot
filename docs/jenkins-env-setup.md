# Jenkins CI/CD 환경 변수 설정 가이드

Jenkins 파이프라인에서 `.env` 파일의 설정을 적용하는 방법을 설명합니다.

## 방법 1: Jenkins 환경 변수 사용 (권장 - 보안)

### 1. Jenkins Global 환경 변수 설정

**Jenkins 관리 → 시스템 설정 → Global properties**

1. "Environment variables" 체크
2. "Add" 버튼 클릭하여 환경 변수 추가:

```
OPENAI_API_KEY=your-api-key
USE_GMS=true
GMS_BASE_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1
GMS_API_KEY=your-gms-key
LLM_MODEL=gpt-4o-mini
```

### 2. 파이프라인별 환경 변수 설정

**파이프라인 설정 → Build Environment**

1. "Use secret text(s) or file(s)" 체크
2. Bindings에서 "Environment variables" 선택
3. Credentials에서 Secret text 선택

### 3. Jenkins Credentials 사용 (가장 안전)

**Jenkins 관리 → Credentials → System → Global credentials**

1. "Add Credentials" 클릭
2. Kind: "Secret text" 선택
3. Secret: API 키 입력
4. ID: `OPENAI_API_KEY` (또는 원하는 ID)
5. Description: 설명 입력

**Jenkinsfile에서 사용:**

```groovy
environment {
    OPENAI_API_KEY = credentials('OPENAI_API_KEY')
    GMS_API_KEY = credentials('GMS_API_KEY')
}
```

## 방법 2: Jenkins 서버에 .env 파일 배치

### 1. .env 파일 생성

Jenkins 서버에 `.env` 파일 생성:

```bash
# EC2 Ubuntu에서
sudo nano /var/lib/jenkins/.env
```

내용:
```env
OPENAI_API_KEY=your-api-key
USE_GMS=true
GMS_BASE_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1
GMS_API_KEY=your-gms-key
LLM_MODEL=gpt-4o-mini
```

### 2. 권한 설정

```bash
# Jenkins 사용자가 읽을 수 있도록 권한 설정
sudo chown jenkins:jenkins /var/lib/jenkins/.env
sudo chmod 600 /var/lib/jenkins/.env
```

### 3. Jenkinsfile 자동 적용

현재 Jenkinsfile은 `/var/jenkins_home/.env` 경로에서 자동으로 찾아서 복사합니다.

## 방법 3: Git 저장소에 .env.example 포함

### 1. .env.example 파일 생성

```bash
# 프로젝트 루트에 .env.example 생성
cp .env .env.example
# 민감한 정보 제거
```

### 2. Jenkinsfile에서 .env 생성

Jenkinsfile이 자동으로 환경 변수로부터 .env 파일을 생성합니다.

## 방법 4: 파이프라인 파라미터 사용

### Jenkinsfile에 파라미터 추가

```groovy
pipeline {
    agent any
    
    parameters {
        string(name: 'OPENAI_API_KEY', defaultValue: '', description: 'OpenAI API Key')
        booleanParam(name: 'USE_GMS', defaultValue: false, description: 'Use GMS')
        string(name: 'GMS_BASE_URL', defaultValue: '', description: 'GMS Base URL')
        string(name: 'GMS_API_KEY', defaultValue: '', description: 'GMS API Key')
    }
    
    environment {
        OPENAI_API_KEY = "${params.OPENAI_API_KEY}"
        USE_GMS = "${params.USE_GMS}"
        GMS_BASE_URL = "${params.GMS_BASE_URL}"
        GMS_API_KEY = "${params.GMS_API_KEY}"
    }
    
    // ... 나머지 파이프라인
}
```

## 현재 Jenkinsfile 동작 방식

현재 Jenkinsfile은 다음 순서로 .env 파일을 찾습니다:

1. **Jenkins 서버의 `/var/jenkins_home/.env`** 파일이 있으면 복사
2. **환경 변수**가 설정되어 있으면 .env 파일 생성
3. **Git 저장소**에 .env 파일이 있으면 사용 (보안 위험)

## 보안 권장사항

### ✅ 권장 방법

1. **Jenkins Credentials 사용**
   - 가장 안전한 방법
   - API 키가 로그에 노출되지 않음
   - 권한 관리 용이

2. **Jenkins 서버에 .env 파일 배치**
   - Git에 포함되지 않음
   - 서버 접근 권한으로 보호

### ❌ 비권장 방법

1. **Git 저장소에 .env 파일 포함**
   - 보안 위험
   - API 키가 Git 히스토리에 남음

2. **Jenkinsfile에 하드코딩**
   - 코드에 노출
   - 버전 관리에 포함됨

## 설정 예시

### 예시 1: Jenkins Credentials 사용

```groovy
pipeline {
    agent any
    
    environment {
        OPENAI_API_KEY = credentials('openai-api-key')
        GMS_API_KEY = credentials('gms-api-key')
    }
    
    stages {
        stage('Prepare Environment') {
            steps {
                sh '''
                    cat > .env << EOF
OPENAI_API_KEY=${OPENAI_API_KEY}
GMS_API_KEY=${GMS_API_KEY}
USE_GMS=true
GMS_BASE_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1
EOF
                '''
            }
        }
        // ... 나머지 스테이지
    }
}
```

### 예시 2: Jenkins 서버에 .env 파일 배치

```bash
# EC2에서 실행
sudo -u jenkins bash
cd /var/lib/jenkins
nano .env

# 내용 입력
OPENAI_API_KEY=sk-...
USE_GMS=true
GMS_BASE_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1
GMS_API_KEY=your-key

# 저장 후 권한 설정
chmod 600 .env
```

## 트러블슈팅

### .env 파일을 찾을 수 없음

```bash
# Jenkins 서버에서 확인
sudo -u jenkins ls -la /var/lib/jenkins/.env

# 경로 확인
echo $JENKINS_HOME
```

### 환경 변수가 적용되지 않음

```bash
# Jenkins 빌드 로그에서 확인
# "Prepare Environment" 스테이지 로그 확인

# 수동으로 테스트
docker-compose config
```

### Docker Compose에서 .env 파일 인식 안 됨

```bash
# .env 파일 위치 확인
ls -la .env

# docker-compose가 .env를 읽는지 확인
docker-compose config | grep -i api_key
```

## 참고사항

- `.env` 파일은 `.gitignore`에 포함되어 있어야 합니다
- Jenkins 빌드 로그에 민감한 정보가 노출되지 않도록 주의하세요
- 프로덕션 환경에서는 반드시 Jenkins Credentials를 사용하세요

