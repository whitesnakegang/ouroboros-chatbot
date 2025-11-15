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
                                cd ${env.PROJECT_DIR}
                                
                                # Git Clone 또는 Pull 로직
                                if [ ! -d ".git" ]; then
                                    echo '[Host] Cloning repository...'
                                    git clone ${env.GIT_REPO_URL} .
                                else
                                    echo '[Host] Pulling repository...'
                                    git pull
                                fi
                            EOF
                        """

                        // 2. 젠킨스에 등록한 'ENV_FILE'을 로드하여 호스트에 복사
                        withCredentials([file(credentialsId: env.ENV_FILE_CRED_ID, variable: 'ENV_FILE_PATH')]) {
                            echo "--- 2. Copying .env file to Host ---"
                            sh "scp -o StrictHostKeyChecking=no ${env.ENV_FILE_PATH} ${env.EC2_USER}@host.docker.internal:${env.PROJECT_DIR}/.env"
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
                        """
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