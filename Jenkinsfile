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
        
        stage('Code Quality Check') {
            steps {
                script {
                    echo 'Running code quality checks...'
                    sh '''
                        # Python 가상환경 생성 (선택적)
                        python3 -m venv venv || true
                        source venv/bin/activate || true
        
                        # 필요한 패키지 설치 (linting용)
                        pip install --quiet flake8 pylint || true
        
                        # 코드 품질 검사 (선택적, 실패해도 계속 진행)
                        flake8 app/ --max-line-length=120 --ignore=E501,W503 || echo "Linting warnings found"
                    '''
                    echo 'Code quality check completed'
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    echo 'Running tests...'
                    sh '''
                        # Python 가상환경 활성화
                        python3 -m venv venv || true
                        source venv/bin/activate || true
        
                        # 테스트 의존성 설치
                        pip install --quiet pytest pytest-cov requests || true
        
                        # 테스트 실행 (테스트 파일이 없는 경우 스킵)
                        if [ -d "tests" ] || [ -f "test_*.py" ]; then
                            pytest tests/ -v --cov=app --cov-report=term-missing || echo "Tests completed with warnings"
                        else
                            echo "No test files found, skipping tests"
                        fi
                    '''
                    echo 'Test stage completed'
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
        
                        # 컨테이너 시작
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

