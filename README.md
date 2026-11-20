# 🎓 Student Management System — DevOps Multi-Tier Project

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-v2-blue?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask%203.0-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/Database-MySQL%208.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Nginx](https://img.shields.io/badge/Frontend-Nginx%20Alpine-009639?logo=nginx&logoColor=white)](https://www.nginx.com/)
[![Jenkins](https://img.shields.io/badge/CI%2FCD-Jenkins%20Pipeline-D24939?logo=jenkins&logoColor=white)](https://www.jenkins.io/)
[![AWS](https://img.shields.io/badge/Cloud-AWS%20EC2%20%7C%20ECS-232F3E?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)

An enterprise-ready, containerized, multi-tier web application built to demonstrate real-world **DevOps practices**: microservices architecture, automated database bootstrapping, containerization with multi-stage Dockerfiles, Docker Compose orchestration, automated testing suites, declarative Jenkins CI/CD pipelines, and AWS cloud deployment.

---

## 📌 Why is this a Good DevOps Project?

| DevOps Principle | How This Project Implements It |
| :--- | :--- |
| **Multi-Tier Containerization** | Decouples Frontend (Nginx), Backend (Python Flask + Gunicorn), and Database (MySQL 8.0) into isolated, communicating containers. |
| **Real-World Docker Implementation** | Non-root container users, volume persistence, multi-stage builds, health check probes (`HEALTHCHECK`), and minimal base images (`alpine`, `slim`). |
| **Automated Database Bootstrapping** | Automatically mounts `init.sql` on startup to seed schemas, administrators, and realistic student records with zero manual database administration. |
| **CI/CD Pipeline Automation** | Full declarative `Jenkinsfile` with 8 distinct stages: checkout, linting, testing, image build, Trivy security scanning, Docker Compose smoke tests, image registry publishing, and remote deployment. |
| **Automated Testing Suite** | Complete test automation in `tests/test_app.py` covering health checks, auth security, and CRUD workflows with 100% pass rate. |
| **High Availability & Health Probing** | Dedicated `/api/health` probe endpoint enabling Kubernetes, AWS ALB, and Docker Compose to monitor live service and database connectivity. |
| **Cloud Deployable** | Production-ready for single-instance AWS EC2 or scalable AWS ECS/EKS with Amazon RDS. |

---

## 🏛️ System Architecture

```text
                                 ┌──────────────────────────────────────────────────────────┐
                                 │                    DOCKER HOST / AWS                     │
                                 │                                                          │
  [ User Browser ] ───────────►  │  Port 80: [ Frontend Container: Nginx Alpine ]           │
                                 │           │                                              │
                                 │           │ Reverse Proxy (/api/*)                       │
                                 │           ▼                                              │
                                 │  Port 5000: [ Backend Container: Flask + Gunicorn ]      │
                                 │           │                                              │
                                 │           │ PyMySQL / Persistent Connection              │
                                 │           ▼                                              │
                                 │  Port 3306: [ Database Container: MySQL 8.0 ]            │
                                 │           │                                              │
                                 │           ▼ Mounted Volumes                              │
                                 │     (mysql_data & init.sql)                              │
                                 └──────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline Workflow

```text
[ Developer Push ] ──► [ GitHub Repo ] ──► [ Jenkins Webhook Trigger ]
                                                   │
     ┌─────────────────────────────────────────────┘
     ▼
 1. SCM Checkout
     ▼
 2. Linting & Syntax Checks
     ▼
 3. Automated Tests (pytest / unittest)
     ▼
 4. Build Docker Images (Backend & Frontend)
     ▼
 5. Security Vulnerability Scan (Trivy)
     ▼
 6. Docker Compose Integration Smoke Test
     ▼
 7. Push Tagged Images to Docker Hub / AWS ECR
     ▼
 8. Continuous Deployment to AWS EC2 / ECS
```

---

## 📂 Project Directory Structure

```text
Student-Management-DevOps/
│
├── frontend/
│   ├── templates/
│   │   ├── login.html              # Admin login interface with credentials helper
│   │   ├── dashboard.html          # Full student dashboard, metrics, table, modals
│   │   └── index.html              # Dynamic auth router
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css           # Modern responsive custom styling & animations
│   │   └── js/
│   │       └── main.js             # Asynchronous API client, search debouncing, CRUD
│   ├── nginx.conf                  # Nginx reverse proxy & static asset configuration
│   └── Dockerfile                  # Lightweight Nginx Alpine container definition
│
├── backend/
│   ├── app.py                      # Flask REST API, session management & routing
│   ├── database.py                 # MySQL database connector with retries & SQLite fallback
│   ├── requirements.txt            # Python dependencies (Flask, PyMySQL, Gunicorn, etc.)
│   └── Dockerfile                  # Secure Python 3.11-slim container with health probes
│
├── database/
│   └── init.sql                    # MySQL schema creation, admin user & sample students
│
├── tests/
│   └── test_app.py                 # Automated unit and integration test suite
│
├── docker-compose.yml              # 3-tier container orchestration configuration
├── Jenkinsfile                     # Declarative 8-stage CI/CD pipeline script
├── .gitignore                      # Git exclusion rules for clean version control
├── .env.example                    # Environment variable template
└── README.md                       # Comprehensive project documentation
```

---

## 🚀 Step-by-Step Implementation Guide

Follow these steps to deploy and manage the project:

### Step 1: Develop the Student Management System
The core application consists of:
- **Admin Authentication**: Secure login with password hashing (`scrypt`/`bcrypt`) and session cookies.
- **Metrics Dashboard**: Live counter cards for Total Students, Active Enrolled, Graduated Students, and Active Courses.
- **Live Search & Filter**: Real-time debounce search by Student ID, Name, Course, or Email, plus status filtering.
- **Student CRUD**:
  - Add Student modal with form validation.
  - Edit Student modal with pre-populated records.
  - Delete Student modal with confirmation.
- **Health Probing**: Real-time `/api/health` endpoint returning database and API status.

### Step 2: Connect the MySQL Database
The database layer is configured in `database/init.sql` and `backend/database.py`:
- Schema sets up `admins` and `students` tables with unique constraints.
- Seed data includes default administrator (`admin` / `admin123`) and 8 realistic student profiles across multiple academic disciplines.
- `database.py` features automatic connection retry with backoff, ensuring resilience when containers boot simultaneously.

### Step 3: Create Dockerfiles
Two optimized Dockerfiles are provided:
- **`backend/Dockerfile`**:
  - Base: `python:3.11-slim`
  - Installs production dependencies and `curl` for container health checks.
  - Runs as non-root user `appuser` (UID 1000) for security hardening.
  - Uses `gunicorn` with 3 workers for high-concurrency production serving.
- **`frontend/Dockerfile`**:
  - Base: `nginx:1.27-alpine`
  - Replaces default Nginx configuration with custom reverse proxy (`nginx.conf`).
  - Proxies `/api/*` requests to `http://backend:5000/api/` with zero CORS issues.

### Step 4: Configure Docker Compose
Run the entire 3-tier stack with a single command:

```bash
docker compose up --build -d
```

Verify running containers:
```bash
docker compose ps
```

Access the application:
- **Frontend Portal**: Open [http://localhost](http://localhost) (or `http://localhost:80`)
- **Backend API**: Open [http://localhost:5000/api/health](http://localhost:5000/api/health)
- **Default Credentials**:
  - **Username:** `admin`
  - **Password:** `admin123`

To inspect container logs:
```bash
docker compose logs -f backend
```

To stop all services:
```bash
docker compose down
```

---

### Step 5: Integrate GitHub
Initialize and push this project to your GitHub repository:

```bash
# 1. Initialize local repository
git init

# 2. Add files and make initial commit
git add .
git commit -m "feat: complete student management devops multi-tier application"

# 3. Rename branch to main
git branch -M main

# 4. Link your remote GitHub repository and push
git remote add origin https://github.com/<your-username>/Student-Management-DevOps.git
git push -u origin main
```

---

### Step 6: Configure Jenkins CI/CD Pipeline

#### 1. Jenkins Prerequisites
- Install Jenkins on your server or run it in Docker.
- Required Jenkins Plugins:
  - *Git Plugin*
  - *Pipeline*
  - *Docker Pipeline*
  - *Credentials Binding Plugin*
  - *AnsiColor*

#### 2. Configure Credentials in Jenkins
Navigate to **Manage Jenkins > Credentials > System > Global credentials**:
1. Add **Username with password**:
   - **ID:** `dockerhub-credentials`
   - **Username:** `<your-dockerhub-username>`
   - **Password:** `<your-dockerhub-token-or-password>`
2. Add **Secret text**:
   - **ID:** `dockerhub-username-var`
   - **Secret:** `<your-dockerhub-username>`

#### 3. Create Pipeline Job
1. In Jenkins, click **New Item**, enter `Student-Management-Pipeline`, and select **Pipeline**.
2. Under **Pipeline Definition**, select **Pipeline script from SCM**.
3. Choose **Git**, enter your repository URL: `https://github.com/<your-username>/Student-Management-DevOps.git`.
4. Set Branch Specifier to `*/main`.
5. Set Script Path to `Jenkinsfile`.
6. Click **Save** and click **Build Now**.

#### 4. Configure GitHub Webhook for Automated Triggers
1. In your GitHub repository, navigate to **Settings > Webhooks > Add webhook**.
2. Set **Payload URL**: `http://<your-jenkins-ip>:8080/github-webhook/`
3. Set **Content type**: `application/json`
4. Select **Just the push event** and click **Add webhook**.
5. Every `git push` to `main` will now trigger an automated test and build cycle!

---

### Step 7: Deploy on AWS

#### Option A: AWS EC2 Deployment (Docker Compose)
1. **Launch EC2 Instance:**
   - AMI: Ubuntu Server 24.04 LTS (t3.small or t2.micro).
   - Security Group: Allow Inbound Ports `22` (SSH), `80` (HTTP), `443` (HTTPS), `5000` (API testing).
2. **Install Docker & Docker Compose on EC2:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y ca-certificates curl gnupg
   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker ubuntu
   ```
3. **Deploy the Application:**
   ```bash
   git clone https://github.com/<your-username>/Student-Management-DevOps.git
   cd Student-Management-DevOps
   docker compose up -d --build
   ```
4. Access the live system at `http://<your-ec2-public-ip>`.

#### Option B: AWS ECS / EKS with Amazon RDS (Production Grade)
1. **Database:** Provision an **Amazon RDS MySQL 8.0** Multi-AZ instance inside your private VPC subnets.
2. **Container Registry:** Create Amazon ECR repositories (`student-backend`, `student-frontend`) and push images from Jenkins.
3. **Application Load Balancer (ALB):**
   - Route `/api/*` path patterns to Backend ECS Target Group (Port 5000).
   - Route default `/*` traffic to Frontend ECS Target Group (Port 80).
   - Attach health check target: `/api/health`.

---

## 🧪 Running Automated Tests

Run the test suite locally without needing MySQL or Docker running (tests automatically use isolated in-memory testing mode):

```bash
# Using standard Python unittest
python tests/test_app.py

# Or using pytest (if installed)
pytest tests/test_app.py -v
```

### Test Coverage Breakdown
- `test_01_health_check`: Verifies `/api/health` returns HTTP 200 and operational status.
- `test_02_login_success`: Validates admin authentication and session creation.
- `test_03_login_invalid_credentials`: Rejects unauthorized passwords with HTTP 401.
- `test_04_login_missing_fields`: Handles bad requests with HTTP 400.
- `test_05_unauthorized_access_protection`: Protects sensitive student endpoints.
- `test_06_dashboard_stats`: Confirms metrics aggregation for UI counters.
- `test_07_get_all_students`: Retrieves student directory.
- `test_08_create_student_success`: Creates new records with HTTP 201.
- `test_09_create_duplicate_student_validation`: Enforces unique student ID and email validation.
- `test_10_search_student_functionality`: Tests dynamic search filtering.
- `test_11_update_student_profile`: Tests student updates via HTTP PUT.
- `test_12_delete_student_record`: Tests record deletion and confirms 404 response.
- `test_13_logout_and_session_clearing`: Validates session invalidation upon logout.

---

## 📡 REST API Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/health` | Service and database connectivity health probe | No |
| `POST` | `/api/auth/login` | Admin authentication (sets HTTP session cookie) | No |
| `POST` | `/api/auth/logout` | Revokes active session | Yes |
| `GET` | `/api/auth/user` | Returns currently authenticated admin info | No |
| `GET` | `/api/stats` | Dashboard counters and course distribution | Yes |
| `GET` | `/api/students` | List students (supports `?search=...&status=...`) | Yes |
| `GET` | `/api/students/<id>` | Retrieve single student by ID or Student ID | Yes |
| `POST` | `/api/students` | Register a new student record | Yes |
| `PUT` | `/api/students/<id>` | Update an existing student record | Yes |
| `DELETE` | `/api/students/<id>` | Delete a student record | Yes |

---

## 💻 Local Development (Without Docker)

If you wish to run the project directly on your workstation without Docker:

1. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```
2. **Start the Backend:**
   ```bash
   cd backend
   python app.py
   ```
3. Open your browser at **[http://localhost:5000](http://localhost:5000)**.
   *(The backend server automatically detects and serves the frontend templates and static assets located in `../frontend`)*.

---

## 📄 License
This project is open-source and licensed under the **MIT License**.
