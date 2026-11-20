"""
Database abstraction layer for Student Management System.
Supports MySQL with connection retry & health checking,
with automatic fallback to SQLite for local development & automated unit tests.
"""

import os
import time
import sqlite3

try:
    import pymysql
    from pymysql.cursors import DictCursor
    HAS_PYMYSQL = True
except ImportError:
    pymysql = None
    DictCursor = None
    HAS_PYMYSQL = False

from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# Configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
DB_NAME = os.getenv("DB_NAME", "student_db")
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(os.path.dirname(__file__), "students_dev.db"))


def get_mysql_connection(retries=5, delay=3):
    """Establishes connection to MySQL with retry backoff."""
    if not HAS_PYMYSQL:
        raise RuntimeError("PyMySQL is not installed. Use SQLite or install PyMySQL.")

    for attempt in range(1, retries + 1):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                cursorclass=DictCursor,
                autocommit=True,
                connect_timeout=5
            )
            return conn
        except pymysql.MySQLError as err:
            print(f"[DB] MySQL connection attempt {attempt}/{retries} failed: {err}")
            if attempt < retries:
                time.sleep(delay)
            else:
                raise err


def get_sqlite_connection():
    """Returns a SQLite connection configured for dict-like access."""
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_connection():
    """Universal connection selector based on environment or availability."""
    if USE_SQLITE or not HAS_PYMYSQL:
        return get_sqlite_connection(), "sqlite"
    try:
        conn = get_mysql_connection(retries=2, delay=1)
        return conn, "mysql"
    except Exception as err:
        print(f"[DB] MySQL unavailable ({err}). Falling back to SQLite.")
        return get_sqlite_connection(), "sqlite"


def check_db_health():
    """Pings database to verify health status."""
    try:
        conn, db_type = get_db_connection()
        if db_type == "mysql":
            conn.ping(reconnect=True)
            conn.close()
        else:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            conn.close()
        return True, db_type
    except Exception as e:
        return False, str(e)


def init_db():
    """Initializes tables and seeds default records if they do not exist."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()

        if db_type == "sqlite":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL UNIQUE,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    course TEXT NOT NULL,
                    enrollment_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Seed default admin
            cursor.execute("SELECT COUNT(*) as count FROM admins WHERE username = 'admin'")
            row = cursor.fetchone()
            count = row[0] if isinstance(row, tuple) else row["count"]
            if count == 0:
                pwd_hash = generate_password_hash("admin123")
                cursor.execute("""
                    INSERT INTO admins (username, password_hash, full_name, email)
                    VALUES (?, ?, ?, ?)
                """, ("admin", pwd_hash, "System Administrator", "admin@university.edu"))

            # Seed sample students if empty
            cursor.execute("SELECT COUNT(*) as count FROM students")
            row = cursor.fetchone()
            count = row[0] if isinstance(row, tuple) else row["count"]
            if count == 0:
                sample_students = [
                    ('STU-1001', 'Alice', 'Johnson', 'alice.johnson@university.edu', 'Cloud Computing & DevOps', '2024-01-15', 'Active'),
                    ('STU-1002', 'Brian', 'Smith', 'brian.smith@university.edu', 'Computer Science', '2023-09-01', 'Active'),
                    ('STU-1003', 'Clara', 'Zhang', 'clara.zhang@university.edu', 'Data Science & AI', '2023-09-01', 'Active'),
                    ('STU-1004', 'David', 'Patel', 'david.patel@university.edu', 'Cybersecurity', '2022-09-10', 'Graduated'),
                    ('STU-1005', 'Emma', 'Williams', 'emma.williams@university.edu', 'Software Engineering', '2024-02-01', 'Active'),
                    ('STU-1006', 'Faisal', 'Al-Mansoor', 'faisal.mansoor@university.edu', 'Cloud Computing & DevOps', '2023-01-20', 'Suspended'),
                    ('STU-1007', 'Grace', 'Hopper', 'grace.hopper@university.edu', 'Computer Science', '2022-09-01', 'Graduated'),
                    ('STU-1008', 'Henry', 'Cavill', 'henry.cavill@university.edu', 'Data Science & AI', '2024-03-12', 'Active')
                ]
                cursor.executemany("""
                    INSERT INTO students (student_id, first_name, last_name, email, course, enrollment_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, sample_students)
            conn.commit()

        print(f"[DB] Database initialized successfully using {db_type.upper()}.")
    finally:
        conn.close()


def authenticate_admin(username, password):
    """Verifies admin credentials."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        placeholder = "?" if db_type == "sqlite" else "%s"
        query = f"SELECT * FROM admins WHERE username = {placeholder}"
        cursor.execute(query, (username,))
        row = cursor.fetchone()

        if not row:
            return None

        admin = dict(row)
        # Check password hash (or fallback plaintext for bootstrap tolerance)
        stored_hash = admin.get("password_hash")
        if check_password_hash(stored_hash, password) or stored_hash == password:
            return {
                "id": admin["id"],
                "username": admin["username"],
                "full_name": admin["full_name"],
                "email": admin["email"]
            }
        return None
    finally:
        conn.close()


def get_all_students(search=None, course=None, status=None):
    """Fetches students with optional search query and filters."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        placeholder = "?" if db_type == "sqlite" else "%s"

        clauses = []
        params = []

        if search:
            search_param = f"%{search.strip()}%"
            clauses.append(
                f"(student_id LIKE {placeholder} OR first_name LIKE {placeholder} OR last_name LIKE {placeholder} OR email LIKE {placeholder} OR course LIKE {placeholder})"
            )
            params.extend([search_param] * 5)

        if course:
            clauses.append(f"course = {placeholder}")
            params.append(course)

        if status:
            clauses.append(f"status = {placeholder}")
            params.append(status)

        query = "SELECT * FROM students"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_student_by_id(student_id):
    """Finds a student by internal primary key ID or student registration ID."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        placeholder = "?" if db_type == "sqlite" else "%s"
        query = f"SELECT * FROM students WHERE id = {placeholder} OR student_id = {placeholder}"
        cursor.execute(query, (student_id, str(student_id)))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_student(data):
    """Inserts a new student record."""
    required = ["student_id", "first_name", "last_name", "email", "course", "enrollment_date"]
    for field in required:
        if not data.get(field):
            raise ValueError(f"Missing required field: {field}")

    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        placeholder = "?" if db_type == "sqlite" else "%s"

        # Check unique constraint on student_id and email
        check_query = f"SELECT id FROM students WHERE student_id = {placeholder} OR email = {placeholder}"
        cursor.execute(check_query, (data["student_id"], data["email"]))
        if cursor.fetchone():
            raise ValueError("Student ID or Email already exists.")

        status = data.get("status", "Active")
        if status not in ("Active", "Graduated", "Suspended"):
            status = "Active"

        insert_query = f"""
            INSERT INTO students (student_id, first_name, last_name, email, course, enrollment_date, status)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """
        values = (
            data["student_id"].strip(),
            data["first_name"].strip(),
            data["last_name"].strip(),
            data["email"].strip().lower(),
            data["course"].strip(),
            data["enrollment_date"],
            status
        )
        cursor.execute(insert_query, values)
        if db_type == "sqlite":
            conn.commit()
            new_id = cursor.lastrowid
        else:
            new_id = cursor.lastrowid

        return get_student_by_id(new_id)
    finally:
        conn.close()


def update_student(student_id, data):
    """Updates an existing student."""
    existing = get_student_by_id(student_id)
    if not existing:
        return None

    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        placeholder = "?" if db_type == "sqlite" else "%s"

        # Check unique constraints excluding this record
        if "student_id" in data or "email" in data:
            new_sid = data.get("student_id", existing["student_id"])
            new_email = data.get("email", existing["email"])
            check_q = f"SELECT id FROM students WHERE (student_id = {placeholder} OR email = {placeholder}) AND id != {placeholder}"
            cursor.execute(check_q, (new_sid, new_email, existing["id"]))
            if cursor.fetchone():
                raise ValueError("Student ID or Email is already used by another student.")

        fields = ["student_id", "first_name", "last_name", "email", "course", "enrollment_date", "status"]
        updates = []
        values = []
        for field in fields:
            if field in data and data[field] is not None:
                updates.append(f"{field} = {placeholder}")
                val = data[field].strip() if isinstance(data[field], str) else data[field]
                if field == "email" and isinstance(val, str):
                    val = val.lower()
                values.append(val)

        if not updates:
            return existing

        values.append(existing["id"])
        query = f"UPDATE students SET {', '.join(updates)} WHERE id = {placeholder}"
        cursor.execute(query, tuple(values))
        if db_type == "sqlite":
            conn.commit()

        return get_student_by_id(existing["id"])
    finally:
        conn.close()


def delete_student(student_id):
    """Deletes a student by ID."""
    existing = get_student_by_id(student_id)
    if not existing:
        return False

    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        placeholder = "?" if db_type == "sqlite" else "%s"
        query = f"DELETE FROM students WHERE id = {placeholder}"
        cursor.execute(query, (existing["id"],))
        if db_type == "sqlite":
            conn.commit()
        return True
    finally:
        conn.close()


def get_dashboard_stats():
    """Computes summary statistics for dashboard metrics cards."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status, count(*) as count FROM students GROUP BY status")
        status_counts = cursor.fetchall()

        total = 0
        active = 0
        graduated = 0
        suspended = 0

        for row in status_counts:
            r = dict(row)
            cnt = r["count"]
            total += cnt
            if r["status"] == "Active":
                active = cnt
            elif r["status"] == "Graduated":
                graduated = cnt
            elif r["status"] == "Suspended":
                suspended = cnt

        cursor.execute("SELECT course, count(*) as count FROM students GROUP BY course ORDER BY count DESC")
        course_counts = [dict(c) for c in cursor.fetchall()]

        return {
            "total_students": total,
            "active_students": active,
            "graduated_students": graduated,
            "suspended_students": suspended,
            "total_courses": len(course_counts),
            "courses_breakdown": course_counts
        }
    finally:
        conn.close()
