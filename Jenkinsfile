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
                    script {
                        
                        echo "--- 1. Cloning/Pulling Repository on Host ---"
                        // SSH로 호스트에 접속해 폴더를 만들고 Git 작업을 먼저 수행
                        sh """
                            ssh -o StrictHostKeyChecking=no ${env.EC2_USER}@host.docker.internal <<EOF
                                set -e
                                
                                echo '[Host] Preparing project directory...'
                                mkdir -p ${env.PROJECT_DIR}
                                
                                echo '[Host] Ensuring correct directory ownership...'
                                sudo chown -R ${env.EC2_USER}:${env.EC2_USER} ${env.PROJECT_DIR}
                                
                                echo '[Host] Moving to project directory...'
                                cd ${env.PROJECT_DIR}
                                
                                echo '[Host] Removing old .env file to prevent scp conflicts...'
                                # [수정됨] scp가 덮어쓰기 전에 기존의 읽기 전용 파일을 삭제합니다.
                                rm -f .env
                                
                                # Git Clone 또는 Pull 로직
                                if [ ! -d ".git" ]; then
                                    echo '[Host] No .git directory found. Cleaning directory for fresh clone...'
                                    rm -rf * .[^.]* || true
                                    echo '[Host] Cloning repository...'
                                    git clone ${env.GIT_REPO_URL} .
                                else
                                    echo '[Host] Pulling repository...'
                                    git pull
                                fi
EOF
                        """ // 닫는 EOF를 줄 맨 앞으로 이동

                        // 2. 젠킨스에 등록한 'ENV_FILE'을 로드하여 호스트에 복사
                        withCredentials([file(credentialsId: env.ENV_FILE_CRED_ID, variable: 'ENV_FILE_PATH')]) {
                            echo "--- 2. Copying .env file to Host ---"
                            sh '''
                                scp -o StrictHostKeyChecking=no $ENV_FILE_PATH ${EC2_USER}@host.docker.internal:${PROJECT_DIR}/.env
                            '''
                            echo ".env file copied successfully."
                        }

                        echo "--- 3. Running Build and Deploy on Host ---"
                        // SSH로 호스트에 다시 접속하여 Docker Compose 실행
                        sh """
                            ssh -o StrictHostKeyChecking=no ${env.EC2_USER}@host.docker.internal <<EOF
                                set -e 
                                
                                echo '[Host] Moving to project directory...'
                                cd ${env.PROJECT_DIR}
                                
                                echo '[Host] .env file confirmed:'
                                ls -l .env
                                
                                echo '[Host] Stopping old containers...'
                                docker-compose down || true
                                
                                echo '[Host] Building new images...'
                                docker-compose build --no-cache
                                
                                echo '[Host] Starting new containers...'
                                docker-compose up -d
                                
                                echo '[Host] --- Deployment Complete ---'
                                docker-compose ps
EOF
                        """ // 닫는 EOF를 줄 맨 앞으로 이동
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