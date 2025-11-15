pipeline {
    // 젠킨스 컨테이너에서 실행
    agent any

    environment {
        // --- [설정 필요 1] ---
        // EC2 호스트에 실제 프로젝트가 배포될 경로
        PROJECT_DIR = "/home/ubuntu/rag-chatbot" 
        
        // --- [설정 필요 2] ---
        // Git 리포지토리 주소
        GIT_REPO_URL = "https://github.com/whitesnakegang/ouroboros-chatbot.git"
        
        // --- [설정 필요 3] ---
        // EC2 접속 유저 이름 (이전에 'ec2-user'로 가정)
        EC2_USER = "ubuntu" 

        // --- [Credential ID] ---
        // 젠킨스에 등록한 SSH 키 ID
        SSH_CRED_ID = 'ec2-host-ssh-key' 
        // 젠킨스에 등록한 Secret File ID
        ENV_FILE_CRED_ID = 'ENV_FILE' 
    }

    stages {
        stage('Deploy to Host via SSH') {
            steps {
                // 1. 젠킨스에 등록한 SSH 키를 로드합니다. (sshagent 플러그인 필요)
                sshagent(credentials: [env.SSH_CRED_ID]) {
                    
                    // 2. 젠킨스에 등록한 'ENV_FILE'을 로드합니다.
                    //    'ENV_FILE_PATH'라는 임시 변수에 파일 경로가 저장됩니다.
                    withCredentials([file(credentialsId: env.ENV_FILE_CRED_ID, variable: 'ENV_FILE_PATH')]) {
                        
                        script {
                            echo "--- 1. Preparing Host Directory ---"
                            // SSH로 호스트에 접속해 프로젝트 폴더가 있는지 확인하고 없으면 생성
                            sh "ssh -o StrictHostKeyChecking=no ${env.EC2_USER}@localhost 'mkdir -p ${env.PROJECT_DIR}'"

                            echo "--- 2. Copying .env file to Host ---"
                            // 젠킨스 컨테이너의 임시 파일을 'scp'를 이용해 EC2 호스트로 복사
                            // ${env.PROJECT_DIR}/.env 경로에 저장됩니다.
                            sh "scp -o StrictHostKeyChecking=no ${env.ENV_FILE_PATH} ${env.EC2_USER}@localhost:${env.PROJECT_DIR}/.env"
                            echo ".env file copied successfully."

                            echo "--- 3. Running Git, Build, and Deploy on Host ---"
                            // SSH로 호스트에 접속하여 모든 배포 명령을 실행 (Heredoc 사용)
                            sh """
                                ssh -o StrictHostKeyChecking=no ${env.EC2_USER}@localhost <<EOF
                                    
                                    # 명령어 실패 시 즉시 중단
                                    set -e 
                                    
                                    echo '[Host] Connected. Moving to project directory...'
                                    cd ${env.PROJECT_DIR}
                                    
                                    # 1. Git Clone 또는 Pull
                                    if [ ! -d ".git" ]; then
                                        echo '[Host] Cloning repository...'
                                        git clone ${env.GIT_REPO_URL} .
                                    else
                                        echo '[Host] Pulling repository...'
                                        git pull
                                    fi
                                    
                                    echo '[Host] .env file confirmed:'
                                    ls -l .env
                                    
                                    # 2. Docker Compose로 빌드 및 배포
                                    # (호스트에 docker-compose가 설치되어 있어야 함)
                                    echo '[Host] Stopping old containers...'
                                    docker-compose down || true
                                    
                                    echo '[Host] Building new images...'
                                    docker-compose build --no-cache
                                    
                                    echo '[Host] Starting new containers...'
                                    docker-compose up -d
                                    
                                    echo '[Host] --- Deployment Complete ---'
                                    docker-compose ps
                                EOF
                            """
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline finished.'
        }
    }
}