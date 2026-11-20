/**
 * Student Management Portal - Frontend Application Logic
 * Integrates with Flask REST API backend
 */

// Global State
let currentStudents = [];
let deleteTargetId = null;
let searchDebounceTimer = null;

// Bootstrap Modal Instances
let addModal = null;
let editModal = null;
let deleteModal = null;
let toastInstance = null;

// DOM Initialization
document.addEventListener("DOMContentLoaded", () => {
    initModalsAndToasts();
    checkAuthentication();
    setupEventListeners();
    loadDashboardData();
    checkSystemHealth();

    // Periodic health check every 30 seconds
    setInterval(checkSystemHealth, 30000);
});

/**
 * Initializes Bootstrap modals and toast instances.
 */
function initModalsAndToasts() {
    const addEl = document.getElementById("addStudentModal");
    if (addEl) addModal = new bootstrap.Modal(addEl);

    const editEl = document.getElementById("editStudentModal");
    if (editEl) editModal = new bootstrap.Modal(editEl);

    const delEl = document.getElementById("deleteStudentModal");
    if (delEl) deleteModal = new bootstrap.Modal(delEl);

    const toastEl = document.getElementById("live-toast");
    if (toastEl) toastInstance = new bootstrap.Toast(toastEl, { delay: 4000 });

    // Set default enrollment date to today on Add form
    const addDateInput = document.getElementById("add-enrollment-date");
    if (addDateInput) {
        addDateInput.value = new Date().toISOString().split("T")[0];
    }
}

/**
 * Validates admin authentication status.
 */
async function checkAuthentication() {
    try {
        const response = await fetch("/api/auth/user");
        const data = await response.json();

        if (response.ok && data.authenticated && data.user) {
            updateAdminProfileUI(data.user);
            return;
        }
    } catch (e) {
        console.warn("Backend auth verification fallback:", e);
    }

    // Check localStorage fallback
    const localUser = localStorage.getItem("admin_user");
    if (localUser) {
        try {
            const user = JSON.parse(localUser);
            updateAdminProfileUI(user);
            return;
        } catch (e) {}
    }

    // Redirect to login if not authenticated
    redirectToLogin();
}

function updateAdminProfileUI(user) {
    const nameEl = document.getElementById("admin-display-name");
    const emailEl = document.getElementById("admin-display-email");
    if (nameEl) nameEl.textContent = user.full_name || user.username || "Admin";
    if (emailEl) emailEl.textContent = user.email || "admin@university.edu";
}

function redirectToLogin() {
    const isHtml = window.location.pathname.endsWith(".html");
    window.location.href = isHtml ? "login.html" : "/";
}

/**
 * Attaches event listeners to inputs, filters, forms, and buttons.
 */
function setupEventListeners() {
    // Logout Handler
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                await fetch("/api/auth/logout", { method: "POST" });
            } catch (err) {}
            localStorage.removeItem("admin_user");
            redirectToLogin();
        });
    }

    // Search input with debounce
    const searchInput = document.getElementById("search-input");
    const clearSearchBtn = document.getElementById("clear-search-btn");

    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            const val = e.target.value.trim();
            if (clearSearchBtn) {
                clearSearchBtn.classList.toggle("d-none", val.length === 0);
            }
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                fetchStudents();
            }, 300);
        });
    }

    if (clearSearchBtn && searchInput) {
        clearSearchBtn.addEventListener("click", () => {
            searchInput.value = "";
            clearSearchBtn.classList.add("d-none");
            fetchStudents();
        });
    }

    // Status Filter
    const statusFilter = document.getElementById("status-filter");
    if (statusFilter) {
        statusFilter.addEventListener("change", () => {
            fetchStudents();
        });
    }

    // Refresh Button
    const refreshBtn = document.getElementById("refresh-btn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            loadDashboardData();
            showToast("Records refreshed", "info");
        });
    }

    // Add Student Form Submission
    const addForm = document.getElementById("add-student-form");
    if (addForm) {
        addForm.addEventListener("submit", handleAddStudent);
    }

    // Edit Student Form Submission
    const editForm = document.getElementById("edit-student-form");
    if (editForm) {
        editForm.addEventListener("submit", handleEditStudent);
    }

    // Confirm Delete Button
    const confirmDeleteBtn = document.getElementById("confirm-delete-btn");
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener("click", handleConfirmDelete);
    }
}

/**
 * Loads all dashboard data: stats and student records.
 */
function loadDashboardData() {
    fetchStats();
    fetchStudents();
}

/**
 * Fetches dashboard metric counters.
 */
async function fetchStats() {
    try {
        const response = await fetch("/api/stats");
        if (response.ok) {
            const stats = await response.json();
            document.getElementById("stat-total").textContent = stats.total_students || 0;
            document.getElementById("stat-active").textContent = stats.active_students || 0;
            document.getElementById("stat-graduated").textContent = stats.graduated_students || 0;
            document.getElementById("stat-courses").textContent = stats.total_courses || 0;
        }
    } catch (error) {
        console.error("Error loading stats:", error);
    }
}

/**
 * Fetches student directory with optional search query & status filters.
 */
async function fetchStudents() {
    const tbody = document.getElementById("students-tbody");
    const countLabel = document.getElementById("record-count-label");
    const searchVal = document.getElementById("search-input")?.value.trim() || "";
    const statusVal = document.getElementById("status-filter")?.value || "";

    const params = new URLSearchParams();
    if (searchVal) params.append("search", searchVal);
    if (statusVal) params.append("status", statusVal);

    try {
        const url = `/api/students${params.toString() ? "?" + params.toString() : ""}`;
        const response = await fetch(url);

        if (!response.ok) {
            if (response.status === 401) {
                redirectToLogin();
                return;
            }
            throw new Error(`Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        currentStudents = data.students || [];

        renderStudentsTable(currentStudents);
        if (countLabel) {
            countLabel.textContent = `Showing ${currentStudents.length} student${currentStudents.length === 1 ? "" : "s"}`;
        }
    } catch (err) {
        console.error("Failed to fetch students:", err);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-danger">
                    <i class="fa-solid fa-triangle-exclamation me-2"></i> Failed to load students. Ensure backend is running.
                </td>
            </tr>
        `;
    }
}

/**
 * Renders student rows into table body.
 */
function renderStudentsTable(students) {
    const tbody = document.getElementById("students-tbody");
    if (!tbody) return;

    if (students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5 text-muted">
                    <i class="fa-solid fa-inbox fa-2x mb-3 d-block text-secondary opacity-50"></i>
                    <h6 class="fw-semibold">No students found</h6>
                    <p class="small mb-0">Try clearing your search query or add a new student record.</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = students.map(student => {
        const initials = `${student.first_name[0] || ""}${student.last_name[0] || ""}`.toUpperCase();
        const statusClass = (student.status || "active").toLowerCase();
        const statusIcon = statusClass === "active" ? "fa-circle-check" : (statusClass === "graduated" ? "fa-certificate" : "fa-ban");

        return `
            <tr>
                <td class="ps-4">
                    <span class="student-id-badge">${escapeHtml(student.student_id)}</span>
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="student-avatar">${initials}</div>
                        <div>
                            <div class="fw-semibold text-dark">${escapeHtml(student.first_name)} ${escapeHtml(student.last_name)}</div>
                            <small class="text-muted font-monospace d-sm-none">${escapeHtml(student.email)}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="text-secondary small">${escapeHtml(student.email)}</span>
                </td>
                <td>
                    <span class="badge bg-light text-dark border px-2 py-1">${escapeHtml(student.course)}</span>
                </td>
                <td>
                    <span class="text-muted small">${escapeHtml(student.enrollment_date)}</span>
                </td>
                <td>
                    <span class="status-badge ${statusClass}">
                        <i class="fa-solid ${statusIcon}"></i>
                        ${escapeHtml(student.status)}
                    </span>
                </td>
                <td class="text-end pe-4">
                    <div class="d-inline-flex gap-1">
                        <button class="btn btn-outline-primary action-btn" onclick="openEditModal(${student.id})" title="Edit Student">
                            <i class="fa-solid fa-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger action-btn" onclick="openDeleteModal(${student.id}, '${escapeHtml(student.first_name)} ${escapeHtml(student.last_name)}', '${escapeHtml(student.student_id)}')" title="Delete Student">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

/**
 * Handles adding a new student.
 */
async function handleAddStudent(e) {
    e.preventDefault();
    const alertBox = document.getElementById("add-error-alert");
    const submitBtn = document.getElementById("add-submit-btn");

    alertBox.classList.add("d-none");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Saving...`;

    const payload = {
        student_id: document.getElementById("add-student-id").value.trim(),
        first_name: document.getElementById("add-first-name").value.trim(),
        last_name: document.getElementById("add-last-name").value.trim(),
        email: document.getElementById("add-email").value.trim(),
        course: document.getElementById("add-course").value,
        enrollment_date: document.getElementById("add-enrollment-date").value,
        status: document.getElementById("add-status").value
    };

    try {
        const response = await fetch("/api/students", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
            addModal.hide();
            document.getElementById("add-student-form").reset();
            // Reset today's date
            document.getElementById("add-enrollment-date").value = new Date().toISOString().split("T")[0];
            showToast(`Student ${payload.first_name} ${payload.last_name} added successfully!`, "success");
            loadDashboardData();
        } else {
            alertBox.textContent = data.error || "Failed to create student.";
            alertBox.classList.remove("d-none");
        }
    } catch (err) {
        alertBox.textContent = "Server communication error. Please try again.";
        alertBox.classList.remove("d-none");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `Save Student Record`;
    }
}

/**
 * Pre-populates and opens Edit modal.
 */
window.openEditModal = function(studentId) {
    const student = currentStudents.find(s => s.id === studentId);
    if (!student) return;

    document.getElementById("edit-internal-id").value = student.id;
    document.getElementById("edit-student-id").value = student.student_id;
    document.getElementById("edit-first-name").value = student.first_name;
    document.getElementById("edit-last-name").value = student.last_name;
    document.getElementById("edit-email").value = student.email;
    document.getElementById("edit-course").value = student.course;
    document.getElementById("edit-enrollment_date").value = student.enrollment_date;
    document.getElementById("edit-status").value = student.status;

    document.getElementById("edit-error-alert").classList.add("d-none");
    editModal.show();
};

/**
 * Handles updating an existing student.
 */
async function handleEditStudent(e) {
    e.preventDefault();
    const studentId = document.getElementById("edit-internal-id").value;
    const alertBox = document.getElementById("edit-error-alert");
    const submitBtn = document.getElementById("edit-submit-btn");

    alertBox.classList.add("d-none");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Updating...`;

    const payload = {
        student_id: document.getElementById("edit-student-id").value.trim(),
        first_name: document.getElementById("edit-first-name").value.trim(),
        last_name: document.getElementById("edit-last-name").value.trim(),
        email: document.getElementById("edit-email").value.trim(),
        course: document.getElementById("edit-course").value,
        enrollment_date: document.getElementById("edit-enrollment-date").value,
        status: document.getElementById("edit-status").value
    };

    try {
        const response = await fetch(`/api/students/${studentId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
            editModal.hide();
            showToast(`Student profile updated successfully!`, "success");
            loadDashboardData();
        } else {
            alertBox.textContent = data.error || "Failed to update student.";
            alertBox.classList.remove("d-none");
        }
    } catch (err) {
        alertBox.textContent = "Server communication error. Please try again.";
        alertBox.classList.remove("d-none");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `Update Student`;
    }
};

/**
 * Opens delete confirmation modal.
 */
window.openDeleteModal = function(id, fullName, studentId) {
    deleteTargetId = id;
    const nameEl = document.getElementById("delete-student-name");
    if (nameEl) nameEl.textContent = `${fullName} (${studentId})`;
    deleteModal.show();
};

/**
 * Executes deletion on confirmation.
 */
async function handleConfirmDelete() {
    if (!deleteTargetId) return;

    const btn = document.getElementById("confirm-delete-btn");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;

    try {
        const response = await fetch(`/api/students/${deleteTargetId}`, {
            method: "DELETE"
        });

        const data = await response.json();

        if (response.ok && data.success) {
            deleteModal.hide();
            showToast("Student record deleted successfully", "warning");
            loadDashboardData();
        } else {
            alert(data.error || "Failed to delete student record.");
        }
    } catch (err) {
        alert("Failed to communicate with backend server.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `Confirm Delete`;
        deleteTargetId = null;
    }
}

/**
 * Checks system health via /api/health.
 */
async function checkSystemHealth() {
    const badge = document.getElementById("health-badge");
    const text = document.getElementById("health-text");
    if (!badge || !text) return;

    try {
        const response = await fetch("/api/health");
        if (response.ok) {
            const data = await response.json();
            const dbType = data.database?.info || "MySQL";
            badge.className = "badge rounded-pill bg-success-subtle text-success border border-success-subtle d-flex align-items-center gap-1 px-3 py-2";
            text.textContent = `Online (${dbType.toUpperCase()})`;
        } else {
            badge.className = "badge rounded-pill bg-danger-subtle text-danger border border-danger-subtle d-flex align-items-center gap-1 px-3 py-2";
            text.textContent = "Degraded (503)";
        }
    } catch (err) {
        badge.className = "badge rounded-pill bg-warning-subtle text-warning border border-warning-subtle d-flex align-items-center gap-1 px-3 py-2";
        text.textContent = "Offline";
    }
}

/**
 * Triggers a floating toast alert.
 */
function showToast(message, type = "success") {
    const toastEl = document.getElementById("live-toast");
    const msgEl = document.getElementById("toast-message");
    const iconEl = document.getElementById("toast-icon");
    if (!toastEl || !msgEl || !iconEl) return;

    msgEl.textContent = message;

    if (type === "success") {
        toastEl.className = "toast align-items-center text-white bg-success border-0 shadow";
        iconEl.className = "fa-solid fa-circle-check";
    } else if (type === "warning") {
        toastEl.className = "toast align-items-center text-white bg-warning border-0 shadow";
        iconEl.className = "fa-solid fa-triangle-exclamation";
    } else if (type === "danger") {
        toastEl.className = "toast align-items-center text-white bg-danger border-0 shadow";
        iconEl.className = "fa-solid fa-circle-xmark";
    } else {
        toastEl.className = "toast align-items-center text-white bg-primary border-0 shadow";
        iconEl.className = "fa-solid fa-circle-info";
    }

    if (toastInstance) toastInstance.show();
}

/**
 * Escapes HTML characters to prevent XSS.
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
