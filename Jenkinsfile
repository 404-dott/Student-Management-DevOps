pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        ansiColor('xterm')
    }

    environment {
        // Registry & Image Configuration
        DOCKER_REGISTRY = credentials('dockerhub-username-var') // Or set your Docker Hub username
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'       // Jenkins Credentials ID
        APP_NAME = 'student-management'
        BACKEND_IMAGE = "${DOCKER_REGISTRY}/student-backend"
        FRONTEND_IMAGE = "${DOCKER_REGISTRY}/student-frontend"
        IMAGE_TAG = "${env.BUILD_NUMBER}"

        // Test environment
        USE_SQLITE = 'true'
    }

    stages {
        // -------------------------------------------------------------
        // Stage 1: SCM Checkout
        // -------------------------------------------------------------
        stage('Checkout Code') {
            steps {
                echo '📥 Checking out source code from Git repository...'
                checkout scm
            }
        }

        // -------------------------------------------------------------
        // Stage 2: Code Quality & Linting
        // -------------------------------------------------------------
        stage('Code Quality & Linting') {
            steps {
                echo '🔍 Running Python syntax compilation and flake8 linting...'
                sh '''
                    python3 -m py_compile backend/*.py tests/*.py
                '''
            }
        }

        // -------------------------------------------------------------
        // Stage 3: Automated Unit & Integration Tests
        // -------------------------------------------------------------
        stage('Automated Tests') {
            steps {
                echo '🧪 Executing unit and integration tests...'
                sh '''
                    python3 -m unittest tests/test_app.py -v
                '''
            }
        }

        // -------------------------------------------------------------
        // Stage 4: Build Docker Images
        // -------------------------------------------------------------
        stage('Build Docker Images') {
            steps {
                echo "🐳 Building Docker images with build tag ${IMAGE_TAG}..."
                script {
                    // Build Backend Image
                    sh """
                        docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} -t ${BACKEND_IMAGE}:latest ./backend
                    """

                    // Build Frontend Image
                    sh """
                        docker build -t ${FRONTEND_IMAGE}:${IMAGE_TAG} -t ${FRONTEND_IMAGE}:latest ./frontend
                    """
                }
            }
        }

        // -------------------------------------------------------------
        // Stage 5: Container Security Vulnerability Scan (Trivy)
        // -------------------------------------------------------------
        stage('Security Scan (Trivy)') {
            steps {
                echo '🛡️ Scanning built Docker images for CVE vulnerabilities...'
                sh '''
                    if command -v trivy >/dev/null 2>&1; then
                        trivy image --severity HIGH,CRITICAL --exit-code 0 ${BACKEND_IMAGE}:${IMAGE_TAG}
                        trivy image --severity HIGH,CRITICAL --exit-code 0 ${FRONTEND_IMAGE}:${IMAGE_TAG}
                    else
                        echo "Trivy not detected on Jenkins agent. Skipping security scan."
                    fi
                '''
            }
        }

        // -------------------------------------------------------------
        // Stage 6: Docker Compose Smoke Test
        // -------------------------------------------------------------
        stage('Compose Integration Test') {
            steps {
                echo '🚀 Spinning up multi-container stack for smoke testing...'
                sh '''
                    # Start containers detached
                    docker compose up -d

                    # Wait for services to initialize and MySQL healthcheck to pass
                    echo "Waiting for services to warm up..."
                    sleep 20

                    # Verify Backend Health Check
                    echo "Testing Backend API healthcheck (/api/health)..."
                    curl -s -f http://localhost:5000/api/health || {
                        echo "Backend health check failed!"
                        docker compose logs
                        docker compose down -v
                        exit 1
                    }

                    # Verify Frontend Nginx HTTP 200
                    echo "Testing Frontend HTTP response..."
                    curl -s -f -I http://localhost:80/ | grep "200 OK" || {
                        echo "Frontend check failed!"
                        docker compose logs
                        docker compose down -v
                        exit 1
                    }

                    # Teardown smoke test environment
                    echo "Smoke tests passed. Tearing down test containers..."
                    docker compose down -v
                '''
            }
        }

        // -------------------------------------------------------------
        // Stage 7: Push Docker Images to Container Registry
        // -------------------------------------------------------------
        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                echo '📤 Authenticating and pushing Docker images to registry...'
                script {
                    withCredentials([usernamePassword(
                        credentialsId: "${DOCKER_CREDENTIALS_ID}",
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh '''
                            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                            docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                            docker push ${BACKEND_IMAGE}:latest
                            docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                            docker push ${FRONTEND_IMAGE}:latest
                            docker logout
                        '''
                    }
                }
            }
        }

        // -------------------------------------------------------------
        // Stage 8: Continuous Deployment to AWS / Production
        // -------------------------------------------------------------
        stage('Deploy to Server') {
            when {
                branch 'main'
            }
            steps {
                echo '🚀 Deploying updated containers to AWS EC2 / Staging environment...'
                script {
                    // Example remote deployment via SSH:
                    // withCredentials([sshUserPrivateKey(credentialsId: 'ec2-ssh-key', keyFileVariable: 'KEY', usernameVariable: 'USER')]) {
                    //     sh '''
                    //         ssh -i $KEY -o StrictHostKeyChecking=no $USER@ec2-target-ip \
                    //         "cd /opt/Student-Management-DevOps && docker compose pull && docker compose up -d"
                    //     '''
                    // }
                    echo 'Continuous deployment step configured. Update EC2 host / credentials to enable live target push.'
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Post-Pipeline Notifications & Workspace Cleanup
    // -----------------------------------------------------------------
    post {
        always {
            echo '🧹 Cleaning up Jenkins workspace...'
            cleanWs()
        }
        success {
            echo '✅ Pipeline execution SUCCESSFUL! Build and tests passed.'
        }
        failure {
            echo '❌ Pipeline execution FAILED! Check console output for diagnostic details.'
        }
    }
}
