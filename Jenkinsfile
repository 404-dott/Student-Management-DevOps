pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        // Application Metadata
        APP_NAME = 'student-management-devops'
        BUILD_TAG = "${env.BUILD_NUMBER ?: '1.0.0'}"

        // Docker Registry Configuration
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_USER = credentials('dockerhub-username')
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        BACKEND_IMAGE = "${DOCKER_USER}/student-backend"
        FRONTEND_IMAGE = "${DOCKER_USER}/student-frontend"

        // Automated Testing Configuration (Isolated SQLite environment)
        USE_SQLITE = 'true'
        SQLITE_DB_PATH = 'tests/test_students.db'
    }

    stages {
        // =============================================================
        // Stage 1: Source Code Checkout from GitHub
        // =============================================================
        stage('Checkout Source Code') {
            steps {
                echo '📥 Step 1: Checking out source code from Git repository...'
                checkout scm
                sh 'git log -1 --pretty=format:"Commit: %h by %an, %ar : %s"'
            }
        }

        // =============================================================
        // Stage 2: Environment Setup & Dependency Installation
        // =============================================================
        stage('Install Dependencies') {
            steps {
                echo '📦 Step 2: Setting up Python virtual environment and installing dependencies...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip setuptools wheel
                    pip install -r backend/requirements.txt
                '''
            }
        }

        // =============================================================
        // Stage 3: Automated Testing with Pytest
        // =============================================================
        stage('Automated Pytest Testing') {
            steps {
                echo '🧪 Step 3: Running automated unit & integration test suite with Pytest...'
                sh '''
                    . venv/bin/activate
                    export USE_SQLITE=true
                    export SQLITE_DB_PATH=tests/test_students.db
                    pytest tests/test_app.py -v --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    // Record and publish JUnit test results in Jenkins UI
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        // =============================================================
        // Stage 4: Docker Image Building
        // =============================================================
        stage('Build Docker Images') {
            steps {
                echo "🐳 Step 4: Building production Docker container images (Tag: ${BUILD_TAG})..."
                script {
                    // Build Backend Flask container image
                    sh """
                        docker build \
                            -t ${BACKEND_IMAGE}:${BUILD_TAG} \
                            -t ${BACKEND_IMAGE}:latest \
                            ./backend
                    """

                    // Build Frontend Nginx container image
                    sh """
                        docker build \
                            -t ${FRONTEND_IMAGE}:${BUILD_TAG} \
                            -t ${FRONTEND_IMAGE}:latest \
                            ./frontend
                    """
                }
            }
        }

        // =============================================================
        // Stage 5: Container Smoke Test & Verification
        // =============================================================
        
        

stage('Smoke Test Stack') {
    steps {
        echo 'Verifying isolated test containers...'
        sh '''
            set -e

            export DB_HOST_PORT=3309
            export BACKEND_HOST_PORT=5002
            export FRONTEND_HOST_PORT=8082

            PROJECT_NAME=student-management-ci-test

            cleanup() {
                docker compose -p $PROJECT_NAME down
            }
            trap cleanup EXIT

            echo "Starting isolated test stack..."
            docker compose -p $PROJECT_NAME up -d --build

            echo "Waiting for services..."
            sleep 30

            echo "Checking Backend Health..."
            docker compose -p $PROJECT_NAME exec -T backend \
                curl -s -f http://localhost:5000/api/health

            echo "Checking Frontend..."
            docker compose -p $PROJECT_NAME exec -T backend \
                curl -s -f -I http://frontend:80/ | grep -E "200 OK|302 Found"

            echo "Smoke testing succeeded!"
        '''
    }
}


        // =============================================================
        // Stage 6: Push Images to Container Registry
        // =============================================================
        stage('Push to Docker Registry') {
            when {
                branch 'main'
            }
            steps {
                echo '📤 Authenticating and pushing Docker images to registry...'
                script {
                    withCredentials([usernamePassword(
                        credentialsId: "${DOCKER_CREDENTIALS_ID}",
                        usernameVariable: 'DOCKER_REG_USER',
                        passwordVariable: 'DOCKER_REG_PASS'
                    )]) {
                        sh '''
                            echo "$DOCKER_REG_PASS" | docker login -u "$DOCKER_REG_USER" --password-stdin
                            docker push ${BACKEND_IMAGE}:${BUILD_TAG}
                            docker push ${BACKEND_IMAGE}:latest
                            docker push ${FRONTEND_IMAGE}:${BUILD_TAG}
                            docker push ${FRONTEND_IMAGE}:latest
                            docker logout
                        '''
                    }
                }
            }
        }

        // =============================================================
        // Stage 7: Deployment using Docker Compose
        // =============================================================
       stage('Deploy via Docker Compose') {
    when {
        branch 'main'
    }
    steps {
        echo 'Deploying updated application using Docker Compose...'
        sh '''
            docker compose up -d --build

            echo "Application deployment completed."
        '''
    }
}

    // =================================================================
    // Post-Pipeline Actions & Notifications
    // =================================================================
    post {
        success {
            echo '✅ Pipeline execution SUCCESSFUL! Code checked out, tested, built, and deployed.'
        }
        failure {
            echo '❌ Pipeline execution FAILED! Check console log output for diagnostic traces.'
        }
    }
}
