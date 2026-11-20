"""
Automated Pytest and Unittest Test Suite for Student Management DevOps Project.
Validates DevOps healthcheck probes, admin authentication, student CRUD,
USN uniqueness, input validation, and attendance tracking.
Run during CI/CD pipeline automation (Jenkinsfile).
"""

import os
import sys
import json
import unittest

# Ensure backend directory is in Python module search path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Force SQLite in-memory / file-based database for isolated, reproducible automated tests
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_students.db")
os.environ["USE_SQLITE"] = "true"
os.environ["SQLITE_DB_PATH"] = TEST_DB_PATH

import database as db
from app import app


class StudentManagementTestCase(unittest.TestCase):
    """Integration and Unit Test Suite covering all application requirements."""

    @classmethod
    def setUpClass(cls):
        """Prepare fresh clean test database."""
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        """Tear down test database after completing test execution."""
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def setUp(self):
        """Configure Flask test client."""
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key-student-management-2026"
        self.client = app.test_client()

    def login_as_admin(self):
        """Helper to authenticate admin user."""
        return self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

    # =========================================================================
    # 1. Health Probe Endpoint Tests (DevOps / Container probes)
    # =========================================================================
    def test_01_health_check_endpoint(self):
        """Verify GET /api/health returns 200 and reports UP for service & DB."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "UP")
        self.assertEqual(data["service"], "student-management-api")
        self.assertIn("database", data)
        self.assertEqual(data["database"]["status"], "UP")

    # =========================================================================
    # 2. Authentication & Authorization Tests
    # =========================================================================
    def test_02_admin_login_success(self):
        """Verify admin login with valid credentials."""
        res = self.login_as_admin()
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["username"], "admin")

    def test_03_admin_login_invalid_password(self):
        """Verify admin login rejection with bad password."""
        res = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        self.assertEqual(res.status_code, 401)
        data = json.loads(res.data)
        self.assertIn("error", data)

    def test_04_admin_login_missing_credentials(self):
        """Verify 400 Bad Request on empty login submission."""
        res = self.client.post("/api/auth/login", json={})
        self.assertEqual(res.status_code, 400)

    def test_05_unauthorized_access_protection(self):
        """Verify that protected endpoints return 401 when no session exists."""
        res = self.client.get("/api/students")
        self.assertEqual(res.status_code, 401)

    # =========================================================================
    # 3. Dashboard Statistics Tests
    # =========================================================================
    def test_06_dashboard_statistics(self):
        """Verify GET /api/stats computes total, male, female, and attendance rate."""
        self.login_as_admin()
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        self.assertIn("total_students", data)
        self.assertIn("male_students", data)
        self.assertIn("female_students", data)
        self.assertIn("attendance_rate", data)
        self.assertIn("today_attendance", data)
        self.assertIn("departments_breakdown", data)
        self.assertIn("recent_students", data)

        self.assertGreaterEqual(data["total_students"], 1)
        self.assertEqual(data["total_students"], data["male_students"] + data["female_students"] + data.get("other_students", 0))

    # =========================================================================
    # 4. Student Registration & CRUD Tests
    # =========================================================================
    def test_07_get_all_students(self):
        """Verify GET /api/students returns populated seed records."""
        self.login_as_admin()
        res = self.client.get("/api/students")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("students", data)
        self.assertGreaterEqual(data["count"], 1)

    def test_08_create_student_success(self):
        """Verify registration of a new student with all required fields."""
        self.login_as_admin()
        payload = {
            "student_id": "STU-2099",
            "usn": "1MS21CS099",
            "full_name": "Test Candidate",
            "gender": "Male",
            "email": "test.candidate@university.edu",
            "phone": "+91 9999988888",
            "department": "Computer Science",
            "semester": 6,
            "dob": "2003-05-12",
            "address": "404 Cloud Native Boulevard",
            "status": "Active"
        }
        res = self.client.post("/api/students", json=payload)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["student"]["usn"], "1MS21CS099")
        self.assertEqual(data["student"]["full_name"], "Test Candidate")

    def test_09_create_student_duplicate_usn_rejection(self):
        """Verify rejection of student with existing USN."""
        self.login_as_admin()
        duplicate_payload = {
            "student_id": "STU-NEW-DIFF",
            "usn": "1MS21CS099",  # Duplicate USN
            "full_name": "Clone Student",
            "gender": "Female",
            "email": "clone.different@university.edu",
            "phone": "+91 9999900000",
            "department": "Information Science",
            "semester": 4,
            "dob": "2004-01-01"
        }
        res = self.client.post("/api/students", json=duplicate_payload)
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn("already exists", data["error"])

    def test_10_create_student_input_validation(self):
        """Verify rejection when required fields are missing or invalid."""
        self.login_as_admin()
        # Invalid semester
        bad_sem_payload = {
            "student_id": "STU-BAD-SEM",
            "usn": "1MS21CS990",
            "full_name": "Bad Sem User",
            "gender": "Male",
            "email": "bad.sem@university.edu",
            "phone": "+91 1234567890",
            "department": "Computer Science",
            "semester": 12,  # Invalid semester (> 8)
            "dob": "2003-05-12"
        }
        res = self.client.post("/api/students", json=bad_sem_payload)
        self.assertEqual(res.status_code, 400)

        # Invalid gender
        bad_gender_payload = {
            "student_id": "STU-BAD-GEN",
            "usn": "1MS21CS991",
            "full_name": "Bad Gender User",
            "gender": "UnknownGender",
            "email": "bad.gender@university.edu",
            "phone": "+91 1234567890",
            "department": "Computer Science",
            "semester": 6,
            "dob": "2003-05-12"
        }
        res = self.client.post("/api/students", json=bad_gender_payload)
        self.assertEqual(res.status_code, 400)

    def test_11_search_students_by_name_and_usn(self):
        """Verify search query parameter matches by name or USN."""
        self.login_as_admin()

        # Search by USN
        res_usn = self.client.get("/api/students?search=1MS21CS099")
        self.assertEqual(res_usn.status_code, 200)
        data_usn = json.loads(res_usn.data)
        self.assertEqual(data_usn["count"], 1)
        self.assertEqual(data_usn["students"][0]["usn"], "1MS21CS099")

        # Search by Name
        res_name = self.client.get("/api/students?search=Candidate")
        self.assertEqual(res_name.status_code, 200)
        data_name = json.loads(res_name.data)
        self.assertGreaterEqual(data_name["count"], 1)

    def test_12_filter_students_by_department_and_gender(self):
        """Verify department and gender filters work as expected."""
        self.login_as_admin()
        res = self.client.get("/api/students?department=Computer Science&gender=Male")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        for s in data["students"]:
            self.assertEqual(s["department"], "Computer Science")
            self.assertEqual(s["gender"], "Male")

    def test_13_get_single_student_profile(self):
        """Verify GET /api/students/<id> retrieves details and attendance summary."""
        self.login_as_admin()
        res = self.client.get("/api/students/1MS21CS099")
        self.assertEqual(res.status_code, 200)
        student = json.loads(res.data)
        self.assertEqual(student["usn"], "1MS21CS099")
        self.assertIn("attendance_summary", student)

    def test_14_update_student_details(self):
        """Verify PUT /api/students/<id> updates fields correctly."""
        self.login_as_admin()
        update_payload = {
            "full_name": "Test Candidate Updated",
            "semester": 7,
            "status": "Graduated"
        }
        res = self.client.put("/api/students/1MS21CS099", json=update_payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["student"]["full_name"], "Test Candidate Updated")
        self.assertEqual(data["student"]["semester"], 7)
        self.assertEqual(data["student"]["status"], "Graduated")

    # =========================================================================
    # 5. Attendance Management Tests
    # =========================================================================
    def test_15_get_attendance_by_date(self):
        """Verify GET /api/attendance?date=... returns list of students and status."""
        self.login_as_admin()
        res = self.client.get("/api/attendance?date=2026-11-20")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("records", data)
        self.assertGreaterEqual(data["count"], 1)

    def test_16_mark_individual_attendance(self):
        """Verify POST /api/attendance records student status."""
        self.login_as_admin()
        # Find ID for 1MS21CS099
        s_res = self.client.get("/api/students/1MS21CS099")
        sid = json.loads(s_res.data)["id"]

        att_payload = {
            "student_id": sid,
            "date": "2026-11-20",
            "status": "Present",
            "remarks": "On time test"
        }
        res = self.client.post("/api/attendance", json=att_payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])

    def test_17_bulk_mark_attendance(self):
        """Verify POST /api/attendance/bulk updates class attendance."""
        self.login_as_admin()
        # Get list of students
        s_res = self.client.get("/api/students")
        students = json.loads(s_res.data)["students"][:3]

        bulk_payload = {
            "date": "2026-11-20",
            "records": [
                {"student_id": s["id"], "status": "Present", "remarks": "Bulk Test"}
                for s in students
            ]
        }
        res = self.client.post("/api/attendance/bulk", json=bulk_payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])

    def test_18_delete_student_cascade(self):
        """Verify DELETE /api/students/<id> removes student and their attendance."""
        self.login_as_admin()
        res = self.client.delete("/api/students/1MS21CS099")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])

        # Confirm 404 for deleted student
        check_res = self.client.get("/api/students/1MS21CS099")
        self.assertEqual(check_res.status_code, 404)

    def test_19_logout_session_invalidation(self):
        """Verify logout clears session and subsequent protected calls fail."""
        self.login_as_admin()
        res = self.client.post("/api/auth/logout")
        self.assertEqual(res.status_code, 200)

        check_res = self.client.get("/api/students")
        self.assertEqual(check_res.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
