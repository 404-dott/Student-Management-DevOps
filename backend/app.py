"""
Flask REST API & Web Application Server for Student Management DevOps Project.
Implements admin authentication, student CRUD with USN/name search, attendance tracking,
dashboard metric aggregation, and container health probes.
"""

import os
from functools import wraps
from datetime import date
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_cors import CORS

import database as db

# Resolve template & static directories (located in ../frontend)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

app.secret_key = os.getenv("SECRET_KEY", "student-devops-secret-key-2026")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Enable CORS for frontend clients
CORS(app, supports_credentials=True)

# Bootstrap database on startup
try:
    db.init_db()
except Exception as e:
    print(f"[WARN] Initial DB bootstrap encountered issue: {e}")


def login_required(f):
    """Protects admin endpoints requiring valid session or bearer token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Unauthorized. Please log in first."}), 401
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# Frontend Page Handlers (SSR / Direct Browser Navigation)
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Redirects to dashboard if logged in, otherwise displays login page."""
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("login.html")


@app.route("/login")
def login_page():
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard_page():
    if not session.get("user_id"):
        return redirect("/login")
    return render_template("dashboard.html", user=session.get("user"))


@app.route("/students")
def students_page():
    if not session.get("user_id"):
        return redirect("/login")
    return render_template("students.html", user=session.get("user"))


@app.route("/attendance")
def attendance_page():
    if not session.get("user_id"):
        return redirect("/login")
    return render_template("attendance.html", user=session.get("user"))


@app.route("/student-profile")
def student_profile_page():
    if not session.get("user_id"):
        return redirect("/login")
    return render_template("student-profile.html", user=session.get("user"))


# -----------------------------------------------------------------------------
# DevOps Health Probe Endpoint
# -----------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint queried by Docker HEALTHCHECK, Jenkins & AWS ALB."""
    healthy, db_info = db.check_db_health()
    status_code = 200 if healthy else 503
    return jsonify({
        "status": "UP" if healthy else "DOWN",
        "service": "student-management-api",
        "database": {
            "status": "UP" if healthy else "DOWN",
            "info": db_info
        },
        "version": "1.0.0"
    }), status_code


# -----------------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Authenticates admin user and establishes session."""
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({"error": "No login credentials provided."}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Both username and password are required."}), 400

    admin = db.authenticate_admin(username, password)
    if not admin:
        return jsonify({"error": "Invalid username or password."}), 401

    session["user_id"] = admin["id"]
    session["user"] = admin

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": admin
    }), 200


@app.route("/api/auth/logout", methods=["POST", "GET"])
def api_logout():
    """Terminates active admin session."""
    session.clear()
    if request.method == "GET":
        return redirect("/login")
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@app.route("/api/auth/user", methods=["GET"])
def api_current_user():
    """Returns currently authenticated session user."""
    user = session.get("user")
    if not user:
        return jsonify({"authenticated": False, "user": None}), 200
    return jsonify({"authenticated": True, "user": user}), 200


# -----------------------------------------------------------------------------
# Dashboard Statistics Endpoint
# -----------------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
@login_required
def api_dashboard_stats():
    """Returns stats: total students, male, female, attendance rate, departments."""
    stats = db.get_dashboard_stats()
    return jsonify(stats), 200


# -----------------------------------------------------------------------------
# Student CRUD & Search Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/students", methods=["GET"])
@login_required
def api_get_students():
    """Lists students with search by name/USN and filter by dept, sem, gender, status."""
    search = request.args.get("search", None)
    department = request.args.get("department", None)
    semester = request.args.get("semester", None)
    gender = request.args.get("gender", None)
    status = request.args.get("status", None)

    students = db.get_all_students(
        search=search,
        department=department,
        semester=semester,
        gender=gender,
        status=status
    )
    return jsonify({
        "count": len(students),
        "students": students
    }), 200


@app.route("/api/students/<student_id>", methods=["GET"])
@login_required
def api_get_student(student_id):
    """Retrieves student profile by internal ID or USN, with attendance history."""
    student = db.get_student_by_id(student_id)
    if not student:
        return jsonify({"error": f"Student '{student_id}' not found."}), 404

    # Include student's attendance summary
    att_summary = db.get_student_attendance_history(student["id"])
    student["attendance_summary"] = att_summary

    return jsonify(student), 200


@app.route("/api/students", methods=["POST"])
@login_required
def api_create_student():
    """Registers a new student record."""
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({"error": "No student data provided."}), 400

    try:
        new_student = db.create_student(data)
        return jsonify({
            "success": True,
            "message": f"Student {new_student['full_name']} registered successfully.",
            "student": new_student
        }), 201
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as err:
        return jsonify({"error": f"Failed to register student: {str(err)}"}), 500


@app.route("/api/students/<student_id>", methods=["PUT"])
@login_required
def api_update_student(student_id):
    """Updates existing student record."""
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({"error": "No update data provided."}), 400

    try:
        updated = db.update_student(student_id, data)
        if not updated:
            return jsonify({"error": f"Student '{student_id}' not found."}), 404
        return jsonify({
            "success": True,
            "message": f"Student {updated['full_name']} updated successfully.",
            "student": updated
        }), 200
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as err:
        return jsonify({"error": f"Failed to update student: {str(err)}"}), 500


@app.route("/api/students/<student_id>", methods=["DELETE"])
@login_required
def api_delete_student(student_id):
    """Deletes student record by ID or USN."""
    success = db.delete_student(student_id)
    if not success:
        return jsonify({"error": f"Student '{student_id}' not found."}), 404
    return jsonify({
        "success": True,
        "message": f"Student '{student_id}' deleted successfully."
    }), 200


# -----------------------------------------------------------------------------
# Attendance Management Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/attendance", methods=["GET"])
@login_required
def api_get_attendance():
    """Fetches attendance records for all active students for a given date."""
    target_date = request.args.get("date", date.today().isoformat())
    records = db.get_attendance_by_date(target_date)
    return jsonify({
        "date": target_date,
        "count": len(records),
        "records": records
    }), 200


@app.route("/api/attendance", methods=["POST"])
@login_required
def api_mark_attendance():
    """Records attendance for an individual student."""
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data or "student_id" not in data:
        return jsonify({"error": "Missing student_id or attendance data."}), 400

    target_date = data.get("date", date.today().isoformat())
    status = data.get("status", "Present")
    remarks = data.get("remarks", "")

    try:
        db.mark_attendance(int(data["student_id"]), target_date, status, remarks)
        return jsonify({
            "success": True,
            "message": f"Attendance marked as '{status}' for date {target_date}."
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to record attendance: {str(e)}"}), 500


@app.route("/api/attendance/bulk", methods=["POST"])
@login_required
def api_bulk_attendance():
    """Bulk updates attendance records for an entire class/date."""
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data or "records" not in data:
        return jsonify({"error": "Missing records payload."}), 400

    target_date = data.get("date", date.today().isoformat())
    records = data["records"]

    try:
        saved_count = db.mark_bulk_attendance(records, target_date)
        return jsonify({
            "success": True,
            "message": f"Successfully updated attendance for {saved_count} students on {target_date}."
        }), 200
    except Exception as e:
        return jsonify({"error": f"Bulk attendance recording failed: {str(e)}"}), 500


@app.route("/api/attendance/student/<student_id>", methods=["GET"])
@login_required
def api_student_attendance_history(student_id):
    """Retrieves full attendance logs and metrics for an individual student."""
    student = db.get_student_by_id(student_id)
    if not student:
        return jsonify({"error": f"Student '{student_id}' not found."}), 404

    history = db.get_student_attendance_history(student["id"])
    return jsonify({
        "student": student,
        "attendance": history
    }), 200


# -----------------------------------------------------------------------------
# Main Application Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    print(f"🚀 Student Management System Backend starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
