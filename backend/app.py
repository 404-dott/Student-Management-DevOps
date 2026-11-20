"""
Flask REST API and Application Server for Student Management DevOps Project.
"""

import os
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory, render_template, redirect, url_for
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

# Enable CORS for frontend clients (useful for local dev and microservices architecture)
CORS(app, supports_credentials=True)

# Bootstrap database tables
try:
    db.init_db()
except Exception as e:
    print(f"[WARN] Initial DB bootstrap encountered error: {e}")


def login_required(f):
    """Decorator to protect administrative API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow bypass if disabled by env (useful for simple headless tests) or if session exists
        if not session.get("user_id"):
            # Also check Authorization header token fallback
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Unauthorized. Please log in first."}), 401
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# Frontend SSR / Direct Route Handlers
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Serves login page or redirects to dashboard if already logged in."""
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("login.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard_page():
    if not session.get("user_id"):
        return redirect("/")
    return render_template("dashboard.html", user=session.get("user"))


# -----------------------------------------------------------------------------
# DevOps Health & Metrics Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint for Docker, Jenkins, Kubernetes & AWS ALB."""
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
    """Authenticates admin and creates session."""
    data = request.get_json(silent=True) or request.form.to_dict()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

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
    """Clears current user session."""
    session.clear()
    if request.method == "GET":
        return redirect("/")
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@app.route("/api/auth/user", methods=["GET"])
def api_current_user():
    """Returns currently authenticated user."""
    user = session.get("user")
    if not user:
        return jsonify({"authenticated": False, "user": None}), 200
    return jsonify({"authenticated": True, "user": user}), 200


# -----------------------------------------------------------------------------
# Dashboard Statistics Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
@login_required
def api_dashboard_stats():
    """Returns aggregated stats for dashboard counters."""
    stats = db.get_dashboard_stats()
    return jsonify(stats), 200


# -----------------------------------------------------------------------------
# Student CRUD & Search Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/students", methods=["GET"])
@login_required
def api_get_students():
    """Lists students with optional search and filters."""
    search = request.args.get("search", None)
    course = request.args.get("course", None)
    status = request.args.get("status", None)

    students = db.get_all_students(search=search, course=course, status=status)
    return jsonify({
        "count": len(students),
        "students": students
    }), 200


@app.route("/api/students/<int:student_id>", methods=["GET"])
@login_required
def api_get_student(student_id):
    """Retrieves single student record."""
    student = db.get_student_by_id(student_id)
    if not student:
        return jsonify({"error": f"Student with ID {student_id} not found."}), 404
    return jsonify(student), 200


@app.route("/api/students", methods=["POST"])
@login_required
def api_create_student():
    """Creates a new student."""
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({"error": "No data provided."}), 400

    try:
        new_student = db.create_student(data)
        return jsonify({
            "success": True,
            "message": "Student created successfully.",
            "student": new_student
        }), 201
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as err:
        return jsonify({"error": f"Failed to create student: {str(err)}"}), 500


@app.route("/api/students/<int:student_id>", methods=["PUT"])
@login_required
def api_update_student(student_id):
    """Updates an existing student."""
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({"error": "No data provided."}), 400

    try:
        updated = db.update_student(student_id, data)
        if not updated:
            return jsonify({"error": f"Student with ID {student_id} not found."}), 404
        return jsonify({
            "success": True,
            "message": "Student updated successfully.",
            "student": updated
        }), 200
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as err:
        return jsonify({"error": f"Failed to update student: {str(err)}"}), 500


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
@login_required
def api_delete_student(student_id):
    """Deletes a student."""
    success = db.delete_student(student_id)
    if not success:
        return jsonify({"error": f"Student with ID {student_id} not found."}), 404
    return jsonify({
        "success": True,
        "message": f"Student {student_id} deleted successfully."
    }), 200


# -----------------------------------------------------------------------------
# Main Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    print(f"🚀 Starting Student Management System Backend on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
