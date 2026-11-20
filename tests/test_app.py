"""
Automated Unit and Integration Tests for Student Management DevOps Project.
Compatible with both standard Python `unittest` and `pytest`.
Executed during CI/CD pipeline validation stages in Jenkinsfile.
"""

import os
import sys
import unittest
import json

# Add backend directory to Python system path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Force SQLite in-memory / temporary test database for fast, isolated CI/CD testing
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_students.db")
os.environ["USE_SQLITE"] = "true"
os.environ["SQLITE_DB_PATH"] = TEST_DB_PATH

import database as db
from app import app


class StudentManagementTestCase(unittest.TestCase):
    """Test suite covering DevOps health checks, authentication, and Student CRUD."""

    @classmethod
    def setUpClass(cls):
        """Prepare clean test database before all tests."""
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database file after all tests finish."""
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def setUp(self):
        """Set up Flask test client for each test."""
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key-2026"
        self.client = app.test_client()

    def login_as_admin(self):
        """Helper to authenticate test client."""
        return self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

    # -------------------------------------------------------------------------
    # 1. Health Check Tests (DevOps / Container readiness probe)
    # -------------------------------------------------------------------------
    def test_01_health_check(self):
        """Verify GET /api/health returns 200 OK and reports service UP."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "UP")
        self.assertEqual(data["service"], "student-management-api")
        self.assertIn("database", data)

    # -------------------------------------------------------------------------
    # 2. Authentication Tests
    # -------------------------------------------------------------------------
    def test_02_login_success(self):
        """Verify admin login with valid credentials."""
        response = self.login_as_admin()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["username"], "admin")

    def test_03_login_invalid_credentials(self):
        """Verify rejection of invalid admin credentials."""
        response = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrong-password"
        })
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_04_login_missing_fields(self):
        """Verify rejection of empty login request body."""
        response = self.client.post("/api/auth/login", json={})
        self.assertEqual(response.status_code, 400)

    def test_05_unauthorized_access_protection(self):
        """Verify that protected API endpoints reject unauthenticated requests with 401."""
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 401)

    # -------------------------------------------------------------------------
    # 3. Dashboard Statistics Tests
    # -------------------------------------------------------------------------
    def test_06_dashboard_stats(self):
        """Verify GET /api/stats computes metrics for dashboard cards."""
        self.login_as_admin()
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("total_students", data)
        self.assertIn("active_students", data)
        self.assertIn("graduated_students", data)
        self.assertIn("total_courses", data)
        self.assertGreaterEqual(data["total_students"], 1)

    # -------------------------------------------------------------------------
    # 4. Student CRUD & Search Tests
    # -------------------------------------------------------------------------
    def test_07_get_all_students(self):
        """Verify GET /api/students returns seeded records."""
        self.login_as_admin()
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("students", data)
        self.assertGreater(data["count"], 0)

    def test_08_create_student_success(self):
        """Verify POST /api/students creates a new student record."""
        self.login_as_admin()
        new_student = {
            "student_id": "STU-9099",
            "first_name": "DevOps",
            "last_name": "Specialist",
            "email": "devops.specialist@university.edu",
            "course": "Cloud Computing & DevOps",
            "enrollment_date": "2026-02-15",
            "status": "Active"
        }
        response = self.client.post("/api/students", json=new_student)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["student"]["student_id"], "STU-9099")

    def test_09_create_duplicate_student_validation(self):
        """Verify unique constraint check rejects duplicate student ID or email."""
        self.login_as_admin()
        duplicate_payload = {
            "student_id": "STU-9099",  # Duplicate ID
            "first_name": "Clone",
            "last_name": "User",
            "email": "clone.user@university.edu",
            "course": "Cybersecurity",
            "enrollment_date": "2026-02-15"
        }
        response = self.client.post("/api/students", json=duplicate_payload)
        self.assertEqual(response.status_code, 400)

    def test_10_search_student_functionality(self):
        """Verify GET /api/students?search=... finds matching records."""
        self.login_as_admin()
        response = self.client.get("/api/students?search=Specialist")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreaterEqual(data["count"], 1)
        found_ids = [s["student_id"] for s in data["students"]]
        self.assertIn("STU-9099", found_ids)

    def test_11_update_student_profile(self):
        """Verify PUT /api/students/<id> updates existing student data."""
        self.login_as_admin()
        # Find internal ID for STU-9099
        search_res = self.client.get("/api/students?search=STU-9099")
        students = json.loads(search_res.data)["students"]
        self.assertTrue(len(students) > 0)
        internal_id = students[0]["id"]

        update_payload = {
            "status": "Graduated",
            "course": "Cloud Computing & DevOps (Honors)"
        }
        update_res = self.client.put(f"/api/students/{internal_id}", json=update_payload)
        self.assertEqual(update_res.status_code, 200)
        updated_student = json.loads(update_res.data)["student"]
        self.assertEqual(updated_student["status"], "Graduated")
        self.assertEqual(updated_student["course"], "Cloud Computing & DevOps (Honors)")

    def test_12_delete_student_record(self):
        """Verify DELETE /api/students/<id> removes student from database."""
        self.login_as_admin()
        search_res = self.client.get("/api/students?search=STU-9099")
        students = json.loads(search_res.data)["students"]
        self.assertTrue(len(students) > 0)
        internal_id = students[0]["id"]

        del_res = self.client.delete(f"/api/students/{internal_id}")
        self.assertEqual(del_res.status_code, 200)
        del_data = json.loads(del_res.data)
        self.assertTrue(del_data["success"])

        # Confirm 404 when querying deleted ID
        check_res = self.client.get(f"/api/students/{internal_id}")
        self.assertEqual(check_res.status_code, 404)

    def test_13_logout_and_session_clearing(self):
        """Verify that POST /api/auth/logout revokes session authorization."""
        self.login_as_admin()
        logout_res = self.client.post("/api/auth/logout")
        self.assertEqual(logout_res.status_code, 200)

        # Subsequent call to protected endpoint must return 401
        protected_res = self.client.get("/api/students")
        self.assertEqual(protected_res.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
