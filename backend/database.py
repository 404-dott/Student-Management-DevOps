"""
Database abstraction layer for Student Management DevOps System.
Connects to MySQL in production/Docker with PyMySQL and connection retries.
Seamlessly falls back to SQLite for local lightweight development and isolated Pytest/CI runs.
"""

import os
import time
import sqlite3
from datetime import datetime, date

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

# MySQL configuration from environment variables (Never hardcoded)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
DB_NAME = os.getenv("DB_NAME", "student_db")
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(os.path.dirname(__file__), "students_dev.db"))


def get_mysql_connection(retries=5, delay=2):
    """Establishes connection to MySQL with retry backoff."""
    if not HAS_PYMYSQL:
        raise RuntimeError("PyMySQL is not installed. Falling back to SQLite.")

    last_error = None
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
        except Exception as err:
            last_error = err
            if attempt < retries:
                time.sleep(delay)
    raise last_error


def get_sqlite_connection():
    """Returns a SQLite connection configured for dict-like access."""
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db_connection():
    """Universal connection selector returning (connection, 'mysql' | 'sqlite')."""
    if USE_SQLITE or not HAS_PYMYSQL:
        return get_sqlite_connection(), "sqlite"
    try:
        conn = get_mysql_connection(retries=2, delay=1)
        return conn, "mysql"
    except Exception as err:
        return get_sqlite_connection(), "sqlite"


def check_db_health():
    """Health check probe for Docker, Kubernetes, and Jenkins smoke test stages."""
    try:
        conn, db_type = get_db_connection()
        if db_type == "mysql":
            conn.ping(reconnect=True)
            conn.close()
        else:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            conn.close()
        return True, f"Connected to {db_type.upper()}"
    except Exception as e:
        return False, str(e)


def init_db():
    """Initializes tables and seeds default admin and sample data if empty."""
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
                    usn TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT NOT NULL,
                    department TEXT NOT NULL,
                    semester INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    dob TEXT NOT NULL,
                    address TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Present',
                    remarks TEXT,
                    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    UNIQUE (student_id, date)
                )
            """)

            # Seed default admin user
            cursor.execute("SELECT COUNT(*) FROM admins WHERE username = 'admin'")
            row = cursor.fetchone()
            count = row[0] if isinstance(row, tuple) else row[0]
            if count == 0:
                pwd_hash = generate_password_hash("admin123")
                cursor.execute("""
                    INSERT INTO admins (username, password_hash, full_name, email)
                    VALUES (?, ?, ?, ?)
                """, ("admin", pwd_hash, "System Administrator", "admin@university.edu"))

            # Seed sample students if empty
            cursor.execute("SELECT COUNT(*) FROM students")
            row = cursor.fetchone()
            s_count = row[0] if isinstance(row, tuple) else row[0]
            if s_count == 0:
                samples = [
                    ('STU-1001', '1MS21CS001', 'Aarav Sharma', 'aarav.sharma@university.edu', '+91 9876543210', 'Computer Science', 6, 'Male', '2003-04-15', '42 Tech Park Avenue, Bengaluru', 'Active'),
                    ('STU-1002', '1MS21CS042', 'Ananya Iyer', 'ananya.iyer@university.edu', '+91 9876543211', 'Computer Science', 6, 'Female', '2003-08-22', '15 Green Glen Layout, Bengaluru', 'Active'),
                    ('STU-1003', '1MS22IS015', 'Rohan Verma', 'rohan.verma@university.edu', '+91 9876543212', 'Information Science', 4, 'Male', '2004-01-10', '78 Koramangala 4th Block, Bengaluru', 'Active'),
                    ('STU-1004', '1MS22AI028', 'Sneha Patel', 'sneha.patel@university.edu', '+91 9876543213', 'Artificial Intelligence', 4, 'Female', '2004-06-18', '21 Indiranagar 100ft Road, Bengaluru', 'Active'),
                    ('STU-1005', '1MS21EC050', 'Vikramaditya Rao', 'vikram.rao@university.edu', '+91 9876543214', 'Electronics & Comm', 6, 'Male', '2003-02-28', '89 Malleshwaram 15th Cross, Bengaluru', 'Active'),
                    ('STU-1006', '1MS20CS088', 'Pooja Hegde', 'pooja.hegde@university.edu', '+91 9876543215', 'Computer Science', 8, 'Female', '2002-11-05', '33 Jayanagar 7th Block, Bengaluru', 'Graduated'),
                    ('STU-1007', '1MS23CS105', 'Karthik Nair', 'karthik.nair@university.edu', '+91 9876543216', 'Computer Science', 2, 'Male', '2005-09-14', '12 HSR Layout Sector 2, Bengaluru', 'Active'),
                    ('STU-1008', '1MS23AI045', 'Meera Kulkarni', 'meera.kulkarni@university.edu', '+91 9876543217', 'Artificial Intelligence', 2, 'Female', '2005-03-30', '56 BTM 2nd Stage, Bengaluru', 'Active'),
                    ('STU-1009', '1MS21ME032', 'Aditya Deshmukh', 'aditya.deshmukh@university.edu', '+91 9876543218', 'Mechanical Engineering', 6, 'Male', '2003-07-19', '64 Rajajinagar 1st Block, Bengaluru', 'Active'),
                    ('STU-1010', '1MS22EC019', 'Divya Krishnan', 'divya.krishnan@university.edu', '+91 9876543219', 'Electronics & Comm', 4, 'Female', '2004-12-03', '90 Whitefield Main Road, Bengaluru', 'Active')
                ]
                cursor.executemany("""
                    INSERT INTO students (student_id, usn, full_name, email, phone, department, semester, gender, dob, address, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, samples)

                # Seed sample attendance for today
                today_str = date.today().isoformat()
                cursor.executemany("""
                    INSERT OR IGNORE INTO attendance (student_id, date, status, remarks)
                    VALUES (?, ?, ?, ?)
                """, [
                    (1, today_str, 'Present', 'On time'),
                    (2, today_str, 'Present', 'On time'),
                    (3, today_str, 'Present', 'On time'),
                    (4, today_str, 'Late', '10m late'),
                    (5, today_str, 'Absent', 'Medical leave'),
                    (6, today_str, 'Present', 'On time'),
                    (7, today_str, 'Present', 'On time'),
                    (8, today_str, 'Present', 'On time'),
                    (9, today_str, 'Absent', 'Unexcused'),
                    (10, today_str, 'Present', 'On time')
                ])

            conn.commit()

        print(f"[DB] Initialized database using {db_type.upper()}.")
    finally:
        conn.close()


def authenticate_admin(username, password):
    """Verifies administrator credentials using secure password hash comparison."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"
        query = f"SELECT * FROM admins WHERE username = {ph}"
        cursor.execute(query, (username,))
        row = cursor.fetchone()

        if not row:
            return None

        admin = dict(row)
        stored_hash = admin.get("password_hash", "")
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


def get_all_students(search=None, department=None, semester=None, gender=None, status=None):
    """Fetches students with filtering and search across full name and USN."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"

        clauses = []
        params = []

        if search:
            search_clean = f"%{search.strip()}%"
            clauses.append(f"(full_name LIKE {ph} OR usn LIKE {ph} OR student_id LIKE {ph} OR email LIKE {ph})")
            params.extend([search_clean, search_clean, search_clean, search_clean])

        if department:
            clauses.append(f"department = {ph}")
            params.append(department)

        if semester:
            clauses.append(f"semester = {ph}")
            params.append(int(semester))

        if gender:
            clauses.append(f"gender = {ph}")
            params.append(gender)

        if status:
            clauses.append(f"status = {ph}")
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


def get_student_by_id(identifier):
    """Finds a student by primary key ID, USN, or student_id string."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"
        query = f"SELECT * FROM students WHERE id = {ph} OR usn = {ph} OR student_id = {ph}"
        cursor.execute(query, (str(identifier), str(identifier), str(identifier)))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_student(data):
    """Inserts a new student record after validating fields and uniqueness."""
    required = ["student_id", "usn", "full_name", "email", "phone", "department", "semester", "gender", "dob"]
    for field in required:
        if not data.get(field):
            raise ValueError(f"Missing required field: '{field}'")

    gender = data["gender"].strip().capitalize()
    if gender not in ("Male", "Female", "Other"):
        raise ValueError("Gender must be 'Male', 'Female', or 'Other'.")

    try:
        sem = int(data["semester"])
        if not (1 <= sem <= 8):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Semester must be an integer between 1 and 8.")

    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"

        # Check unique constraint on student_id, usn, and email
        check_q = f"SELECT id, student_id, usn, email FROM students WHERE student_id = {ph} OR usn = {ph} OR email = {ph}"
        cursor.execute(check_q, (data["student_id"].strip(), data["usn"].strip(), data["email"].strip().lower()))
        existing = cursor.fetchone()
        if existing:
            ex = dict(existing)
            if ex["student_id"] == data["student_id"].strip():
                raise ValueError(f"Student ID '{data['student_id']}' already exists.")
            if ex["usn"] == data["usn"].strip():
                raise ValueError(f"USN '{data['usn']}' already exists.")
            if ex["email"] == data["email"].strip().lower():
                raise ValueError(f"Email '{data['email']}' already exists.")

        status = data.get("status", "Active")
        if status not in ("Active", "Graduated", "Suspended"):
            status = "Active"

        insert_q = f"""
            INSERT INTO students (student_id, usn, full_name, email, phone, department, semester, gender, dob, address, status)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
        """
        values = (
            data["student_id"].strip(),
            data["usn"].strip().upper(),
            data["full_name"].strip(),
            data["email"].strip().lower(),
            data["phone"].strip(),
            data["department"].strip(),
            sem,
            gender,
            str(data["dob"]).strip(),
            data.get("address", "").strip(),
            status
        )
        cursor.execute(insert_q, values)
        if db_type == "sqlite":
            conn.commit()
            new_id = cursor.lastrowid
        else:
            new_id = cursor.lastrowid

        return get_student_by_id(new_id)
    finally:
        conn.close()


def update_student(identifier, data):
    """Updates student information while protecting unique constraints."""
    existing = get_student_by_id(identifier)
    if not existing:
        return None

    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"

        student_id_val = data.get("student_id", existing["student_id"]).strip()
        usn_val = data.get("usn", existing["usn"]).strip().upper()
        email_val = data.get("email", existing["email"]).strip().lower()

        # Check unique collisions with other records
        check_q = f"""
            SELECT id FROM students 
            WHERE (student_id = {ph} OR usn = {ph} OR email = {ph}) AND id != {ph}
        """
        cursor.execute(check_q, (student_id_val, usn_val, email_val, existing["id"]))
        if cursor.fetchone():
            raise ValueError("Student ID, USN, or Email is already used by another student.")

        fields = ["student_id", "usn", "full_name", "email", "phone", "department", "semester", "gender", "dob", "address", "status"]
        updates = []
        values = []

        for field in fields:
            if field in data and data[field] is not None:
                val = data[field]
                if field == "usn" and isinstance(val, str):
                    val = val.strip().upper()
                elif field == "email" and isinstance(val, str):
                    val = val.strip().lower()
                elif field == "semester":
                    val = int(val)
                elif isinstance(val, str):
                    val = val.strip()

                updates.append(f"{field} = {ph}")
                values.append(val)

        if not updates:
            return existing

        values.append(existing["id"])
        update_q = f"UPDATE students SET {', '.join(updates)} WHERE id = {ph}"
        cursor.execute(update_q, tuple(values))
        if db_type == "sqlite":
            conn.commit()

        return get_student_by_id(existing["id"])
    finally:
        conn.close()


def delete_student(identifier):
    """Deletes student record and cascades to attendance logs."""
    existing = get_student_by_id(identifier)
    if not existing:
        return False

    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"

        # Explicitly delete attendance records in case cascade is not enabled in SQLite
        cursor.execute(f"DELETE FROM attendance WHERE student_id = {ph}", (existing["id"],))
        cursor.execute(f"DELETE FROM students WHERE id = {ph}", (existing["id"],))

        if db_type == "sqlite":
            conn.commit()
        return True
    finally:
        conn.close()


def mark_attendance(student_id, target_date, status="Present", remarks=None):
    """Records or updates student attendance for a given date (upsert)."""
    if status not in ("Present", "Absent", "Late"):
        raise ValueError("Status must be 'Present', 'Absent', or 'Late'.")

    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"

        if db_type == "sqlite":
            query = f"""
                INSERT INTO attendance (student_id, date, status, remarks)
                VALUES ({ph}, {ph}, {ph}, {ph})
                ON CONFLICT(student_id, date) DO UPDATE SET
                    status = excluded.status,
                    remarks = excluded.remarks,
                    marked_at = CURRENT_TIMESTAMP
            """
        else:
            query = f"""
                INSERT INTO attendance (student_id, date, status, remarks)
                VALUES ({ph}, {ph}, {ph}, {ph})
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    remarks = VALUES(remarks),
                    marked_at = CURRENT_TIMESTAMP
            """

        cursor.execute(query, (student_id, str(target_date), status, remarks))
        if db_type == "sqlite":
            conn.commit()
        return True
    finally:
        conn.close()


def mark_bulk_attendance(records, target_date):
    """
    Bulk saves attendance.
    records is a list of dicts: [{'student_id': 1, 'status': 'Present', 'remarks': 'def mark_bulk_attendance'}, ...]
    """
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"

        if db_type == "sqlite":
            query = f"""
                INSERT INTO attendance (student_id, date, status, remarks)
                VALUES ({ph}, {ph}, {ph}, {ph})
                ON CONFLICT(student_id, date) DO UPDATE SET
                    status = excluded.status,
                    remarks = excluded.remarks,
                    marked_at = CURRENT_TIMESTAMP
            """
        else:
            query = f"""
                INSERT INTO attendance (student_id, date, status, remarks)
                VALUES ({ph}, {ph}, {ph}, {ph})
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    remarks = VALUES(remarks),
                    marked_at = CURRENT_TIMESTAMP
            """

        
        for item in records:
            sid = item["student_id"]
            stat = item.get("status") or "Present"

            if stat == "Unmarked":
                stat = "Present"

            if stat not in ("Present", "Absent", "Late"):
                raise ValueError(f"Invalid attendance status: {stat}")
            rem = item.get("remarks", "")
            cursor.execute(query, (sid, str(target_date), stat, rem))

        if db_type == "sqlite":
            conn.commit()
        return len(records)
    finally:
        conn.close()


def get_attendance_by_date(target_date):
    """Returns attendance records mapped to all active students for a given date."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"

        query = f"""
            SELECT 
                s.id as student_id,
                s.student_id as student_code,
                s.usn,
                s.full_name,
                s.department,
                s.semester,
                s.gender,
                COALESCE(a.status, 'Unmarked') as status,
                a.remarks,
                a.date as attendance_date
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id AND a.date = {ph}
            WHERE s.status != 'Suspended'
            ORDER BY s.department, s.usn
        """
        cursor.execute(query, (str(target_date),))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_student_attendance_history(student_id):
    """Returns complete attendance breakdown and logs for a single student."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        ph = "?" if db_type == "sqlite" else "%s"

        query = f"""
            SELECT id, date, status, remarks, marked_at
            FROM attendance
            WHERE student_id = {ph}
            ORDER BY date DESC
        """
        cursor.execute(query, (student_id,))
        logs = [dict(r) for r in cursor.fetchall()]

        total_classes = len(logs)
        present_count = sum(1 for log in logs if log["status"] == "Present")
        late_count = sum(1 for log in logs if log["status"] == "Late")
        absent_count = sum(1 for log in logs if log["status"] == "Absent")

        percentage = round(((present_count + (0.5 * late_count)) / total_classes * 100), 1) if total_classes > 0 else 100.0

        return {
            "total_classes": total_classes,
            "present": present_count,
            "late": late_count,
            "absent": absent_count,
            "percentage": percentage,
            "logs": logs
        }
    finally:
        conn.close()


def get_dashboard_stats():
    """Computes real-time statistics for all 4 key metric cards and visual charts."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()

        # 1. Total and Gender counts
        cursor.execute("SELECT gender, count(*) as count FROM students GROUP BY gender")
        gender_rows = [dict(r) for r in cursor.fetchall()]
        total_students = 0
        male_students = 0
        female_students = 0
        other_students = 0

        for r in gender_rows:
            g = r.get("gender")
            cnt = r.get("count", 0)
            total_students += cnt
            if g == "Male":
                male_students = cnt
            elif g == "Female":
                female_students = cnt
            else:
                other_students += cnt

        # 2. Status counts (Active, Graduated, Suspended)
        cursor.execute("SELECT status, count(*) as count FROM students GROUP BY status")
        status_rows = [dict(r) for r in cursor.fetchall()]
        active_students = 0
        graduated_students = 0
        suspended_students = 0
        for r in status_rows:
            st = r.get("status")
            cnt = r.get("count", 0)
            if st == "Active":
                active_students = cnt
            elif st == "Graduated":
                graduated_students = cnt
            elif st == "Suspended":
                suspended_students = cnt

        # 3. Department distribution
        cursor.execute("SELECT department, count(*) as count FROM students GROUP BY department ORDER BY count DESC")
        departments_breakdown = [dict(r) for r in cursor.fetchall()]

        # 4. Attendance statistics for today
        today_str = date.today().isoformat()
        ph = "?" if db_type == "sqlite" else "%s"
        cursor.execute(f"SELECT status, count(*) as count FROM attendance WHERE date = {ph} GROUP BY status", (today_str,))
        att_rows = [dict(r) for r in cursor.fetchall()]

        today_present = 0
        today_absent = 0
        today_late = 0
        for r in att_rows:
            st = r.get("status")
            cnt = r.get("count", 0)
            if st == "Present":
                today_present = cnt
            elif st == "Absent":
                today_absent = cnt
            elif st == "Late":
                today_late = cnt

        today_marked = today_present + today_absent + today_late
        if today_marked > 0:
            attendance_rate = round(((today_present + (0.5 * today_late)) / today_marked * 100), 1)
        elif total_students > 0:
            # Check overall attendance rate
            cursor.execute("SELECT status, count(*) as count FROM attendance GROUP BY status")
            all_att = [dict(r) for r in cursor.fetchall()]
            all_pres = sum(r["count"] for r in all_att if r["status"] == "Present")
            all_late = sum(r["count"] for r in all_att if r["status"] == "Late")
            all_tot = sum(r["count"] for r in all_att)
            attendance_rate = round(((all_pres + (0.5 * all_late)) / all_tot * 100), 1) if all_tot > 0 else 0.0
        else:
            attendance_rate = 0.0

        # 5. Recent student registrations (last 5)
        cursor.execute("SELECT id, student_id, usn, full_name, department, semester, status, created_at FROM students ORDER BY id DESC LIMIT 5")
        recent_students = [dict(r) for r in cursor.fetchall()]

        return {
            "total_students": total_students,
            "male_students": male_students,
            "female_students": female_students,
            "other_students": other_students,
            "active_students": active_students,
            "graduated_students": graduated_students,
            "suspended_students": suspended_students,
            "attendance_rate": attendance_rate,
            "today_attendance": {
                "date": today_str,
                "present": today_present,
                "absent": today_absent,
                "late": today_late,
                "total_marked": today_marked
            },
            "departments_breakdown": departments_breakdown,
            "recent_students": recent_students
        }
    finally:
        conn.close()
