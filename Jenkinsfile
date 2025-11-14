pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = 'rag-chatbot'
        DOCKER_IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Git Clone') {
            steps {
                script {
                    // Git 저장소 클론 (브랜치는 Jenkins 설정에서 지정)
                    checkout scm
                    echo "Git clone success - Branch: ${env.BRANCH_NAME}"
                }
            }
        }
        
       

        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker image...'
                    sh """
                        # 기존 컨테이너 및 이미지 정리 (선택적)
                        docker-compose down || true
                        docker rmi ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG} || true
                        docker rmi ${env.DOCKER_IMAGE_NAME}:latest || true
        
                        # Docker 이미지 빌드
                        docker build -t ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG} .
                        docker tag ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG} ${env.DOCKER_IMAGE_NAME}:latest
        
                        echo "Docker image built: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
                    """
                    echo 'Docker image build success'
                }
            }
        }

        stage('Docker Image Test') {
            steps {
                script {
                    echo 'Testing Docker image...'
                    sh """
                        # Docker 이미지가 제대로 빌드되었는지 확인
                        docker images | grep ${env.DOCKER_IMAGE_NAME}
        
                        # 컨테이너 실행 테스트 (헬스체크)
                        docker run -d --name test-container -p 8001:8000 ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG} || true
        
                        # 잠시 대기 후 헬스체크
                        sleep 10
                        curl -f http://localhost:8001/health || echo "Health check failed"
        
                        # 테스트 컨테이너 정리
                        docker stop test-container || true
                        docker rm test-container || true
                    """
                    echo 'Docker image test completed'
                }
            }
        }

        stage('Prepare Environment') {
            steps {
                script {
                    echo 'Preparing environment variables...'
                    sh '''
                        # .env 파일이 Jenkins 서버에 있는 경우 복사
                        # 방법 1: Jenkins 서버의 특정 경로에서 .env 파일 복사
                        if [ -f /var/jenkins_home/.env ]; then
                            cp /var/jenkins_home/.env .env
                            echo ".env file copied from Jenkins home directory"
                        # 방법 2: 환경 변수로부터 .env 파일 생성
                        elif [ ! -f .env ] && [ -n "$OPENAI_API_KEY" ]; then
                            echo "Creating .env file from environment variables..."
                            cat > .env << EOF
# API Keys
OPENAI_API_KEY=${OPENAI_API_KEY:-}
USE_GMS=${USE_GMS:-false}
GMS_BASE_URL=${GMS_BASE_URL:-}
GMS_API_KEY=${GMS_API_KEY:-}

# LLM Settings
LLM_MODEL=${LLM_MODEL:-gpt-4o-mini}
LLM_TEMPERATURE=${LLM_TEMPERATURE:-1}
MAX_TOKENS=${MAX_TOKENS:-1000}

# Embedding Settings
EMBEDDING_MODEL=${EMBEDDING_MODEL:-intfloat/multilingual-e5-base}
EMBEDDING_DEVICE=${EMBEDDING_DEVICE:-cpu}

# Vector DB Settings
CHROMA_DB_PATH=${CHROMA_DB_PATH:-./vector_db}
COLLECTION_NAME=${COLLECTION_NAME:-documents}

# Document Processing
CHUNK_SIZE=${CHUNK_SIZE:-1000}
CHUNK_OVERLAP=${CHUNK_OVERLAP:-200}

# RAG Settings
RETRIEVAL_TOP_K=${RETRIEVAL_TOP_K:-5}
EOF
                            echo ".env file created from environment variables"
                        else
                            echo ".env file already exists or will be used from repository"
                        fi
                        
                        # .env 파일 존재 확인
                        if [ -f .env ]; then
                            echo ".env file found"
                            # 민감한 정보는 마스킹하여 출력
                            grep -v "API_KEY\|SECRET\|PASSWORD" .env || true
                        else
                            echo "Warning: .env file not found. Using default values or environment variables."
                        fi
                    '''
                }
            }
        }

        stage('Deploy') {
            when {
                // develop 또는 main 브랜치일 때만 배포
                anyOf {
                    branch 'develop'
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                script {
                    echo 'Deploying application...'
                    sh '''
                        # 기존 컨테이너 중지
                        docker-compose down || true
        
                        # 최신 이미지로 업데이트
                        docker-compose build --no-cache
        
                        # 컨테이너 시작 (.env 파일 자동 로드)
                        docker-compose up -d
        
                        # 배포 상태 확인
                        sleep 5
                        docker-compose ps
        
                        echo "Deployment completed"
                    '''
                    echo 'Deploy success'
                }
            }
        }
    }

    post {
        always {
            script {
                echo 'Cleaning up...'
                sh '''
                    # 테스트 컨테이너 정리
                    docker stop test-container || true
                    docker rm test-container || true
                    
                    # 가상환경 정리 (선택적)
                    rm -rf venv || true
                '''
            }
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}

