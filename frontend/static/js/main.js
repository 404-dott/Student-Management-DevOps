/**
 * Main Frontend Application Script for Student Management DevOps Portal.
 * Handles API integration, dynamic DOM manipulation, real-time filtering,
 * interactive modals, Chart.js visualizations, and responsive UI toggles.
 */

// =============================================================================
// 1. Shared Global Utilities & Authentication
// =============================================================================

async function checkAuthAndInitUser() {
    try {
        const res = await fetch('/api/auth/user');
        const data = await res.json();
        if (!data.authenticated || !data.user) {
            window.location.href = '/login';
            return null;
        }

        const nameEl = document.getElementById('admin-name');
        const emailEl = document.getElementById('admin-email');
        if (nameEl && data.user.full_name) nameEl.textContent = data.user.full_name;
        if (emailEl && data.user.email) emailEl.textContent = data.user.email;

        return data.user;
    } catch (err) {
        console.warn('Auth validation warning:', err);
        return null;
    }
}

async function checkHealthStatus() {
    const pill = document.getElementById('health-pill');
    const text = document.getElementById('health-status-text');
    if (!pill || !text) return;

    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        if (res.ok && data.status === 'UP') {
            pill.className = 'badge rounded-pill bg-success-subtle text-success border border-success-subtle d-flex align-items-center gap-2 px-3 py-2';
            text.textContent = 'Database Online';
        } else {
            pill.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger-subtle d-flex align-items-center gap-2 px-3 py-2';
            text.textContent = 'Service Degraded';
        }
    } catch (e) {
        pill.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning-subtle d-flex align-items-center gap-2 px-3 py-2';
        text.textContent = 'Healthcheck Offline';
    }
}

function showToast(message, type = 'success') {
    const toastEl = document.getElementById('live-toast');
    if (!toastEl) return;

    const iconEl = document.getElementById('toast-icon');
    const msgEl = document.getElementById('toast-message');

    if (msgEl) msgEl.textContent = message;

    toastEl.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-primary');
    if (type === 'success') {
        toastEl.classList.add('bg-success');
        if (iconEl) iconEl.className = 'fa-solid fa-circle-check';
    } else if (type === 'error') {
        toastEl.classList.add('bg-danger');
        if (iconEl) iconEl.className = 'fa-solid fa-triangle-exclamation';
    } else {
        toastEl.classList.add('bg-primary');
        if (iconEl) iconEl.className = 'fa-solid fa-circle-info';
    }

    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
}

// Global DOM setup for all pages
document.addEventListener('DOMContentLoaded', () => {
    // Setup mobile sidebar toggle
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('appSidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    // Setup sign-out handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                await fetch('/api/auth/logout', { method: 'POST' });
            } finally {
                window.location.href = '/login';
            }
        });
    }

    // Run health check
    checkHealthStatus();
    setInterval(checkHealthStatus, 30000);
});


// =============================================================================
// 2. Dashboard Logic
// =============================================================================

let deptChartInstance = null;

async function initDashboard() {
    await checkAuthAndInitUser();

    try {
        const res = await fetch('/api/stats');
        if (!res.ok) throw new Error('Failed to fetch statistics');
        const stats = await res.json();

        // 1. Update 4 Key Statistics Cards
        const total = stats.total_students || 0;
        const male = stats.male_students || 0;
        const female = stats.female_students || 0;
        const rate = stats.attendance_rate || 0;

        document.getElementById('stat-total-students').textContent = total;
        document.getElementById('stat-male-students').textContent = male;
        document.getElementById('stat-female-students').textContent = female;
        document.getElementById('stat-attendance-rate').textContent = `${rate}%`;

        const malePct = total > 0 ? Math.round((male / total) * 100) : 0;
        const femalePct = total > 0 ? Math.round((female / total) * 100) : 0;

        document.getElementById('stat-male-sub').textContent = `${malePct}% of total students`;
        document.getElementById('stat-female-sub').textContent = `${femalePct}% of total students`;

        // 2. Update Today's Attendance Widget Counters
        const todayAtt = stats.today_attendance || {};
        document.getElementById('today-present-count').textContent = todayAtt.present || 0;
        document.getElementById('today-late-count').textContent = todayAtt.late || 0;
        document.getElementById('today-absent-count').textContent = todayAtt.absent || 0;

        // 3. Render Department Breakdown Chart (Chart.js)
        renderDepartmentChart(stats.departments_breakdown || []);

        // 4. Render Recent Students Table
        renderRecentStudents(stats.recent_students || []);

    } catch (err) {
        console.error('Error initializing dashboard:', err);
        showToast('Error loading dashboard statistics', 'error');
    }
}

function renderDepartmentChart(departments) {
    const canvas = document.getElementById('departmentChart');
    if (!canvas) return;

    const labels = departments.map(d => d.department);
    const dataValues = departments.map(d => d.count);

    if (deptChartInstance) {
        deptChartInstance.destroy();
    }

    const ctx = canvas.getContext('2d');
    deptChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['No Data'],
            datasets: [{
                label: 'Enrolled Students',
                data: dataValues.length ? dataValues : [0],
                backgroundColor: [
                    '#4f46e5',
                    '#06b6d4',
                    '#10b981',
                    '#f59e0b',
                    '#8b5cf6',
                    '#ec4899'
                ],
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    padding: 12,
                    cornerRadius: 8,
                    backgroundColor: '#1e293b'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0, font: { family: 'Inter' } },
                    grid: { color: '#f1f5f9' }
                },
                x: {
                    ticks: { font: { family: 'Inter', size: 11 } },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderRecentStudents(students) {
    const tbody = document.getElementById('recent-students-tbody');
    if (!tbody) return;

    if (!students || students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">No student records found.</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = students.map(s => {
        const statusClass = s.status ? s.status.toLowerCase() : 'active';
        return `
            <tr>
                <td><span class="fw-semibold text-primary">${escapeHtml(s.usn)}</span></td>
                <td>
                    <div class="fw-bold">${escapeHtml(s.full_name)}</div>
                    <small class="text-muted">${escapeHtml(s.student_id)}</small>
                </td>
                <td>${escapeHtml(s.department)}</td>
                <td><span class="badge bg-light text-dark border">Sem ${s.semester}</span></td>
                <td><span class="badge-status ${statusClass}">${escapeHtml(s.status || 'Active')}</span></td>
                <td class="text-end pe-4">
                    <a href="/student-profile?usn=${encodeURIComponent(s.usn)}" class="btn-icon view" title="View Profile">
                        <i class="fa-solid fa-arrow-right"></i>
                    </a>
                </td>
            </tr>
        `;
    }).join('');
}


// =============================================================================
// 3. Student Directory & CRUD Management
// =============================================================================

let allLoadedStudents = [];
let deleteTargetId = null;

async function initStudentsPage() {
    await checkAuthAndInitUser();

    // Event listeners for search & filters
    const searchInput = document.getElementById('filter-search');
    const deptSelect = document.getElementById('filter-department');
    const semSelect = document.getElementById('filter-semester');
    const genderSelect = document.getElementById('filter-gender');
    const resetBtn = document.getElementById('reset-filters-btn');
    const refreshBtn = document.getElementById('refresh-students-btn');

    let debounceTimer;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadStudentsTable, 300);
        });
    }

    if (deptSelect) deptSelect.addEventListener('change', loadStudentsTable);
    if (semSelect) semSelect.addEventListener('change', loadStudentsTable);
    if (genderSelect) genderSelect.addEventListener('change', loadStudentsTable);

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            if (deptSelect) deptSelect.value = '';
            if (semSelect) semSelect.value = '';
            if (genderSelect) genderSelect.value = '';
            loadStudentsTable();
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadStudentsTable);
    }

    // Add Student Form submission
    const addForm = document.getElementById('add-student-form');
    if (addForm) {
        addForm.addEventListener('submit', handleAddStudentSubmit);
    }

    // Edit Student Form submission
    const editForm = document.getElementById('edit-student-form');
    if (editForm) {
        editForm.addEventListener('submit', handleEditStudentSubmit);
    }

    // Delete Student Confirmation button
    const confirmDelBtn = document.getElementById('confirm-delete-btn');
    if (confirmDelBtn) {
        confirmDelBtn.addEventListener('click', handleConfirmDelete);
    }

    // Initial load
    await loadStudentsTable();
}

async function loadStudentsTable() {
    const tbody = document.getElementById('students-table-body');
    const countBadge = document.getElementById('students-count-badge');
    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-5 text-muted">
                <div class="spinner-border text-primary spinner-border-sm me-2" role="status"></div>
                Fetching student records...
            </td>
        </tr>
    `;

    const search = document.getElementById('filter-search')?.value.trim() || '';
    const dept = document.getElementById('filter-department')?.value || '';
    const sem = document.getElementById('filter-semester')?.value || '';
    const gender = document.getElementById('filter-gender')?.value || '';

    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (dept) params.append('department', dept);
    if (sem) params.append('semester', sem);
    if (gender) params.append('gender', gender);

    try {
        const res = await fetch(`/api/students?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to fetch students');
        const data = await res.json();
        allLoadedStudents = data.students || [];

        if (countBadge) countBadge.textContent = `${data.count} Students`;

        if (allLoadedStudents.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-5 text-muted">
                        <i class="fa-solid fa-folder-open fa-2x mb-2 d-block text-secondary"></i>
                        No student records match the given criteria.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = allLoadedStudents.map(s => {
            const genderClass = s.gender ? s.gender.toLowerCase() : 'male';
            const statusClass = s.status ? s.status.toLowerCase() : 'active';
            return `
                <tr>
                    <td><span class="fw-semibold text-secondary">${escapeHtml(s.student_id)}</span></td>
                    <td><span class="fw-bold text-primary">${escapeHtml(s.usn)}</span></td>
                    <td>
                        <div class="fw-semibold">${escapeHtml(s.full_name)}</div>
                    </td>
                    <td>
                        <div>${escapeHtml(s.department)}</div>
                        <small class="text-muted">Semester ${s.semester}</small>
                    </td>
                    <td>
                        <span class="gender-pill ${genderClass}">${escapeHtml(s.gender)}</span>
                    </td>
                    <td>
                        <div class="small"><i class="fa-regular fa-envelope me-1 text-muted"></i>${escapeHtml(s.email)}</div>
                        <div class="small text-muted"><i class="fa-solid fa-phone me-1 text-muted"></i>${escapeHtml(s.phone)}</div>
                    </td>
                    <td>
                        <span class="badge-status ${statusClass}">${escapeHtml(s.status || 'Active')}</span>
                    </td>
                    <td class="text-end pe-4">
                        <div class="action-btn-group justify-content-end">
                            <a href="/student-profile?usn=${encodeURIComponent(s.usn)}" class="btn-icon view" title="View Profile">
                                <i class="fa-solid fa-eye"></i>
                            </a>
                            <button type="button" class="btn-icon edit" title="Edit Student" onclick="openEditStudentModal(${s.id})">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button type="button" class="btn-icon delete" title="Delete Student" onclick="openDeleteStudentModal(${s.id}, '${escapeHtml(s.full_name)}')">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error('Error loading students table:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5 text-danger">
                    <i class="fa-solid fa-triangle-exclamation me-1"></i> Failed to communicate with student service.
                </td>
            </tr>
        `;
    }
}

async function handleAddStudentSubmit(e) {
    e.preventDefault();
    const alertBox = document.getElementById('add-alert');
    const submitBtn = document.getElementById('add-submit-btn');
    if (alertBox) alertBox.classList.add('d-none');
    if (submitBtn) submitBtn.disabled = true;

    const payload = {
        student_id: document.getElementById('add-student-id').value.trim(),
        usn: document.getElementById('add-usn').value.trim().toUpperCase(),
        full_name: document.getElementById('add-full-name').value.trim(),
        gender: document.getElementById('add-gender').value,
        email: document.getElementById('add-email').value.trim().toLowerCase(),
        phone: document.getElementById('add-phone').value.trim(),
        department: document.getElementById('add-department').value,
        semester: parseInt(document.getElementById('add-semester').value),
        dob: document.getElementById('add-dob').value,
        address: document.getElementById('add-address').value.trim(),
        status: document.getElementById('add-status').value
    };

    try {
        const res = await fetch('/api/students', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok && data.success) {
            showToast(`Student ${payload.full_name} registered successfully!`, 'success');
            const modalEl = document.getElementById('addStudentModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            document.getElementById('add-student-form').reset();
            loadStudentsTable();
        } else {
            if (alertBox) {
                alertBox.textContent = data.error || 'Failed to register student.';
                alertBox.classList.remove('d-none');
            }
        }
    } catch (err) {
        if (alertBox) {
            alertBox.textContent = 'Server connection error.';
            alertBox.classList.remove('d-none');
        }
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

function openEditStudentModal(id) {
    const student = allLoadedStudents.find(s => s.id === id);
    if (!student) return;

    document.getElementById('edit-internal-id').value = student.id;
    document.getElementById('edit-student-id').value = student.student_id;
    document.getElementById('edit-usn').value = student.usn;
    document.getElementById('edit-full-name').value = student.full_name;
    document.getElementById('edit-gender').value = student.gender;
    document.getElementById('edit-email').value = student.email;
    document.getElementById('edit-phone').value = student.phone;
    document.getElementById('edit-department').value = student.department;
    document.getElementById('edit-semester').value = student.semester;
    document.getElementById('edit-dob').value = student.dob;
    document.getElementById('edit-address').value = student.address || '';
    document.getElementById('edit-status').value = student.status || 'Active';

    const alertBox = document.getElementById('edit-alert');
    if (alertBox) alertBox.classList.add('d-none');

    const modal = new bootstrap.Modal(document.getElementById('editStudentModal'));
    modal.show();
}

async function handleEditStudentSubmit(e) {
    e.preventDefault();
    const alertBox = document.getElementById('edit-alert');
    const submitBtn = document.getElementById('edit-submit-btn');
    if (alertBox) alertBox.classList.add('d-none');
    if (submitBtn) submitBtn.disabled = true;

    const id = document.getElementById('edit-internal-id').value;
    const payload = {
        student_id: document.getElementById('edit-student-id').value.trim(),
        usn: document.getElementById('edit-usn').value.trim().toUpperCase(),
        full_name: document.getElementById('edit-full-name').value.trim(),
        gender: document.getElementById('edit-gender').value,
        email: document.getElementById('edit-email').value.trim().toLowerCase(),
        phone: document.getElementById('edit-phone').value.trim(),
        department: document.getElementById('edit-department').value,
        semester: parseInt(document.getElementById('edit-semester').value),
        dob: document.getElementById('edit-dob').value,
        address: document.getElementById('edit-address').value.trim(),
        status: document.getElementById('edit-status').value
    };

    try {
        const res = await fetch(`/api/students/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok && data.success) {
            showToast(`Student ${payload.full_name} updated successfully!`, 'success');
            const modalEl = document.getElementById('editStudentModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            loadStudentsTable();
        } else {
            if (alertBox) {
                alertBox.textContent = data.error || 'Failed to update student profile.';
                alertBox.classList.remove('d-none');
            }
        }
    } catch (err) {
        if (alertBox) {
            alertBox.textContent = 'Server connection error.';
            alertBox.classList.remove('d-none');
        }
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

function openDeleteStudentModal(id, name) {
    deleteTargetId = id;
    const nameEl = document.getElementById('delete-student-name');
    if (nameEl) nameEl.textContent = name;

    const modal = new bootstrap.Modal(document.getElementById('deleteStudentModal'));
    modal.show();
}

async function handleConfirmDelete() {
    if (!deleteTargetId) return;
    const btn = document.getElementById('confirm-delete-btn');
    if (btn) btn.disabled = true;

    try {
        const res = await fetch(`/api/students/${deleteTargetId}`, {
            method: 'DELETE'
        });

        const data = await res.json();

        if (res.ok && data.success) {
            showToast('Student record deleted successfully', 'success');
            const modalEl = document.getElementById('deleteStudentModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            loadStudentsTable();
        } else {
            showToast(data.error || 'Failed to delete student', 'error');
        }
    } catch (err) {
        showToast('Server communication error', 'error');
    } finally {
        if (btn) btn.disabled = false;
        deleteTargetId = null;
    }
}


// =============================================================================
// 4. Attendance Hub Logic
// =============================================================================

let attendanceRecords = [];

async function initAttendancePage() {
    await checkAuthAndInitUser();

    const dateInput = document.getElementById('attendance-date-input');
    const loadBtn = document.getElementById('btn-load-date');
    const saveBtn = document.getElementById('btn-save-attendance');
    const markAllPresentBtn = document.getElementById('btn-mark-all-present');
    const markAllAbsentBtn = document.getElementById('btn-mark-all-absent');
    const deptFilter = document.getElementById('att-filter-dept');
    const semFilter = document.getElementById('att-filter-sem');

    // Default to today
    const today = new Date().toISOString().split('T')[0];
    if (dateInput) {
        dateInput.value = today;
        dateInput.max = today;
    }

    if (loadBtn) {
        loadBtn.addEventListener('click', loadAttendanceRoster);
    }

    if (dateInput) {
        dateInput.addEventListener('change', loadAttendanceRoster);
    }

    if (deptFilter) deptFilter.addEventListener('change', filterAttendanceView);
    if (semFilter) semFilter.addEventListener('change', filterAttendanceView);

    if (markAllPresentBtn) {
        markAllPresentBtn.addEventListener('click', () => {
            setAllAttendanceStatus('Present');
        });
    }

    if (markAllAbsentBtn) {
        markAllAbsentBtn.addEventListener('click', () => {
            setAllAttendanceStatus('Absent');
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', handleSaveAttendance);
    }

    await loadAttendanceRoster();
}

async function loadAttendanceRoster() {
    const tbody = document.getElementById('attendance-table-body');
    const dateInput = document.getElementById('attendance-date-input');
    const dateLabel = document.getElementById('active-date-label');
    if (!tbody || !dateInput) return;

    const chosenDate = dateInput.value || new Date().toISOString().split('T')[0];
    if (dateLabel) dateLabel.textContent = chosenDate;

    tbody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-5 text-muted">
                <div class="spinner-border text-primary spinner-border-sm me-2" role="status"></div>
                Loading attendance for ${chosenDate}...
            </td>
        </tr>
    `;

    try {
        const res = await fetch(`/api/attendance?date=${chosenDate}`);
        if (!res.ok) throw new Error('Failed to retrieve attendance roster');
        const data = await res.json();
        attendanceRecords = data.records || [];

        renderAttendanceRows(attendanceRecords);
        updateAttendanceMetrics();
    } catch (err) {
        console.error('Error loading attendance roster:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5 text-danger">
                    <i class="fa-solid fa-triangle-exclamation me-1"></i> Failed to retrieve attendance roster.
                </td>
            </tr>
        `;
    }
}

function renderAttendanceRows(records) {
    const tbody = document.getElementById('attendance-table-body');
    if (!tbody) return;

    if (!records || records.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5 text-muted">
                    <i class="fa-solid fa-users-slash fa-2x mb-2 d-block text-secondary"></i>
                    No active students enrolled for attendance.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = records.map((r, index) => {
        const currentStatus = r.status || 'Present';
        const isPresent = currentStatus === 'Present' || currentStatus === 'Unmarked';
        const isLate = currentStatus === 'Late';
        const isAbsent = currentStatus === 'Absent';

        return `
            <tr data-student-id="${r.student_id}">
                <td><span class="fw-bold text-primary">${escapeHtml(r.usn)}</span></td>
                <td>
                    <div class="fw-semibold">${escapeHtml(r.full_name)}</div>
                    <small class="text-muted">${escapeHtml(r.student_code)}</small>
                </td>
                <td>${escapeHtml(r.department)}</td>
                <td><span class="badge bg-light text-dark border">Sem ${r.semester}</span></td>
                <td>
                    <div class="attendance-toggle-group">
                        <button type="button" class="btn-att ${isPresent ? 'active-present' : ''}" onclick="toggleRowStatus(${r.student_id}, 'Present', this)">
                            <i class="fa-solid fa-check me-1"></i>Present
                        </button>
                        <button type="button" class="btn-att ${isLate ? 'active-late' : ''}" onclick="toggleRowStatus(${r.student_id}, 'Late', this)">
                            <i class="fa-solid fa-clock me-1"></i>Late
                        </button>
                        <button type="button" class="btn-att ${isAbsent ? 'active-absent' : ''}" onclick="toggleRowStatus(${r.student_id}, 'Absent', this)">
                            <i class="fa-solid fa-xmark me-1"></i>Absent
                        </button>
                    </div>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm remarks-input" placeholder="Optional remark..." value="${escapeHtml(r.remarks || '')}" data-student-id="${r.student_id}">
                </td>
            </tr>
        `;
    }).join('');
}

function filterAttendanceView() {
    const dept = document.getElementById('att-filter-dept')?.value;
    const sem = document.getElementById('att-filter-sem')?.value;

    let filtered = attendanceRecords;
    if (dept) filtered = filtered.filter(r => r.department === dept);
    if (sem) filtered = filtered.filter(r => String(r.semester) === String(sem));

    renderAttendanceRows(filtered);
    updateAttendanceMetrics();
}

function toggleRowStatus(studentId, newStatus, clickedBtn) {
    const record = attendanceRecords.find(r => r.student_id === studentId);
    if (record) {
        record.status = newStatus;
    }

    const group = clickedBtn.closest('.attendance-toggle-group');
    const buttons = group.querySelectorAll('.btn-att');
    buttons.forEach(b => {
        b.classList.remove('active-present', 'active-late', 'active-absent');
    });

    if (newStatus === 'Present') clickedBtn.classList.add('active-present');
    if (newStatus === 'Late') clickedBtn.classList.add('active-late');
    if (newStatus === 'Absent') clickedBtn.classList.add('active-absent');

    updateAttendanceMetrics();
}

function setAllAttendanceStatus(status) {
    attendanceRecords.forEach(r => {
        r.status = status;
    });

    const rows = document.querySelectorAll('#attendance-table-body tr');
    rows.forEach(tr => {
        const btns = tr.querySelectorAll('.btn-att');
        btns.forEach(b => b.classList.remove('active-present', 'active-late', 'active-absent'));
        if (status === 'Present') {
            btns[0]?.classList.add('active-present');
        } else if (status === 'Absent') {
            btns[2]?.classList.add('active-absent');
        }
    });

    updateAttendanceMetrics();
    showToast(`Marked all visible students as ${status}`, 'info');
}

function updateAttendanceMetrics() {
    const total = attendanceRecords.length;
    let present = 0;
    let late = 0;
    let absent = 0;

    attendanceRecords.forEach(r => {
        const s = r.status || 'Present';
        if (s === 'Present' || s === 'Unmarked') present++;
        else if (s === 'Late') late++;
        else if (s === 'Absent') absent++;
    });

    document.getElementById('att-stat-total').textContent = total;
    document.getElementById('att-stat-present').textContent = present;
    document.getElementById('att-stat-late').textContent = late;
    document.getElementById('att-stat-absent').textContent = absent;
}

async function handleSaveAttendance() {
    const saveBtn = document.getElementById('btn-save-attendance');
    const btnText = document.getElementById('save-btn-text');
    const dateInput = document.getElementById('attendance-date-input');
    const targetDate = dateInput?.value || new Date().toISOString().split('T')[0];

    if (!attendanceRecords.length) {
        showToast('No student records loaded to save.', 'warning');
        return;
    }

    if (saveBtn) saveBtn.disabled = true;
    if (btnText) btnText.textContent = 'Saving...';

    // Gather remarks from inputs
    const remarksInputs = document.querySelectorAll('.remarks-input');
    const remarksMap = {};
    remarksInputs.forEach(inp => {
        remarksMap[inp.dataset.studentId] = inp.value.trim();
    });

    const payloadRecords = attendanceRecords.map(r => ({
        student_id: r.student_id,
        status: r.status || 'Present',
        remarks: remarksMap[r.student_id] || r.remarks || ''
    }));

    try {
        const res = await fetch('/api/attendance/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: targetDate,
                records: payloadRecords
            })
        });

        const data = await res.json();

        if (res.ok && data.success) {
            showToast(`Attendance synchronized for ${data.message}!`, 'success');
        } else {
            showToast(data.error || 'Failed to save attendance roster.', 'error');
        }
    } catch (err) {
        showToast('Server communication error during save.', 'error');
    } finally {
        if (saveBtn) saveBtn.disabled = false;
        if (btnText) btnText.textContent = 'Save Attendance';
    }
}


// =============================================================================
// 5. Student Profile Page Logic
// =============================================================================

async function initProfilePage() {
    await checkAuthAndInitUser();

    const searchInput = document.getElementById('profile-search-input');
    const searchBtn = document.getElementById('btn-search-profile');
    const editForm = document.getElementById('profile-edit-form');

    // Parse URL parameter ?usn=... or ?id=...
    const urlParams = new URLSearchParams(window.location.search);
    const requestedIdentifier = urlParams.get('usn') || urlParams.get('id') || '1MS21CS001';

    if (searchInput) {
        searchInput.value = requestedIdentifier;
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                loadProfile(searchInput.value.trim());
            }
        });
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const val = searchInput?.value.trim();
            if (val) loadProfile(val);
        });
    }

    if (editForm) {
        editForm.addEventListener('submit', handleProfileModalUpdate);
    }

    await loadProfile(requestedIdentifier);
}

async function loadProfile(identifier) {
    const container = document.getElementById('profile-container');
    if (!container) return;

    container.innerHTML = `
        <div class="text-center py-5 text-muted">
            <div class="spinner-border text-primary spinner-border-sm me-2" role="status"></div>
            Loading profile for '${escapeHtml(identifier)}'...
        </div>
    `;

    try {
        const res = await fetch(`/api/students/${encodeURIComponent(identifier)}`);
        if (!res.ok) {
            container.innerHTML = `
                <div class="app-card p-5 text-center">
                    <i class="fa-solid fa-user-xmark fa-3x text-warning mb-3"></i>
                    <h4 class="fw-bold">Student Record Not Found</h4>
                    <p class="text-muted">No student found matching '${escapeHtml(identifier)}'. Please verify the USN or Student ID.</p>
                    <a href="/students" class="btn btn-primary fw-semibold mt-2">
                        <i class="fa-solid fa-users me-1"></i> Back to Student Directory
                    </a>
                </div>
            `;
            return;
        }

        const student = await res.json();
        const att = student.attendance_summary || {};
        const pct = att.percentage !== undefined ? att.percentage : 100.0;
        const eligible = pct >= 75.0;

        const initials = student.full_name ? student.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'ST';
        const genderClass = student.gender ? student.gender.toLowerCase() : 'male';
        const statusClass = student.status ? student.status.toLowerCase() : 'active';

        // Render Profile Hero, Metrics Gauge, and Attendance Log
        container.innerHTML = `
            <!-- Profile Hero Card -->
            <div class="app-card mb-4">
                <div class="profile-cover">
                    <div class="profile-avatar-wrapper">
                        <span>${initials}</span>
                    </div>
                </div>
                <div class="profile-header-details">
                    <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
                        <div>
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <h3 class="fw-bold mb-0 text-dark">${escapeHtml(student.full_name)}</h3>
                                <span class="badge-status ${statusClass}">${escapeHtml(student.status || 'Active')}</span>
                            </div>
                            <div class="text-muted d-flex flex-wrap align-items-center gap-3 small">
                                <span><i class="fa-solid fa-id-badge text-primary me-1"></i>USN: <strong>${escapeHtml(student.usn)}</strong></span>
                                <span><i class="fa-solid fa-barcode text-primary me-1"></i>ID: ${escapeHtml(student.student_id)}</span>
                                <span><i class="fa-solid fa-graduation-cap text-primary me-1"></i>${escapeHtml(student.department)} (Sem ${student.semester})</span>
                            </div>
                        </div>

                        <div>
                            <button type="button" class="btn btn-outline-primary fw-semibold d-flex align-items-center gap-2" onclick="openProfileEditModal(${student.id})">
                                <i class="fa-solid fa-user-pen"></i> Edit Profile
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Two-Column Grid: Details & Attendance Analytics -->
            <div class="row g-4 mb-4">
                <!-- Personal & Academic Details Card -->
                <div class="col-12 col-lg-6">
                    <div class="app-card h-100">
                        <div class="app-card-header">
                            <h4 class="card-title-main"><i class="fa-solid fa-user-circle text-primary me-2"></i>Personal & Contact Information</h4>
                        </div>
                        <div class="p-4">
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-2 border-bottom">
                                    <span class="text-muted small fw-semibold">Email Address</span>
                                    <span class="fw-semibold"><a href="mailto:${escapeHtml(student.email)}" class="text-decoration-none">${escapeHtml(student.email)}</a></span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-2 border-bottom">
                                    <span class="text-muted small fw-semibold">Phone Number</span>
                                    <span class="fw-semibold">${escapeHtml(student.phone)}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-2 border-bottom">
                                    <span class="text-muted small fw-semibold">Gender</span>
                                    <span class="gender-pill ${genderClass}">${escapeHtml(student.gender)}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-2 border-bottom">
                                    <span class="text-muted small fw-semibold">Date of Birth</span>
                                    <span class="fw-semibold">${escapeHtml(student.dob)}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-2">
                                    <span class="text-muted small fw-semibold">Residential Address</span>
                                    <span class="fw-semibold text-end" style="max-width: 60%;">${escapeHtml(student.address || 'Not Provided')}</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Attendance Analytics & Eligibility Card -->
                <div class="col-12 col-lg-6">
                    <div class="app-card h-100">
                        <div class="app-card-header">
                            <h4 class="card-title-main"><i class="fa-solid fa-chart-pie text-success me-2"></i>Attendance Compliance</h4>
                            <span class="badge ${eligible ? 'bg-success-subtle text-success border border-success-subtle' : 'bg-danger-subtle text-danger border border-danger-subtle'}">
                                ${eligible ? 'Exam Eligible' : 'Attendance Shortage'}
                            </span>
                        </div>
                        <div class="p-4">
                            <div class="d-flex align-items-center gap-4 mb-4">
                                <div class="attendance-progress-circle" style="--percentage: ${pct}%;">
                                    <div class="attendance-progress-inner">
                                        ${pct}%
                                    </div>
                                </div>
                                <div>
                                    <h5 class="fw-bold mb-1">${eligible ? 'Good Academic Standing' : 'Attendance Warning'}</h5>
                                    <p class="text-muted small mb-0">Minimum university requirement: 75% attendance across lecture sessions.</p>
                                </div>
                            </div>

                            <div class="row g-2 text-center">
                                <div class="col-3">
                                    <div class="p-2 border rounded-3 bg-light">
                                        <div class="small text-muted">Classes</div>
                                        <div class="fw-bold fs-5">${att.total_classes || 0}</div>
                                    </div>
                                </div>
                                <div class="col-3">
                                    <div class="p-2 border rounded-3 bg-light">
                                        <div class="small text-success">Present</div>
                                        <div class="fw-bold fs-5 text-success">${att.present || 0}</div>
                                    </div>
                                </div>
                                <div class="col-3">
                                    <div class="p-2 border rounded-3 bg-light">
                                        <div class="small text-warning">Late</div>
                                        <div class="fw-bold fs-5 text-warning">${att.late || 0}</div>
                                    </div>
                                </div>
                                <div class="col-3">
                                    <div class="p-2 border rounded-3 bg-light">
                                        <div class="small text-danger">Absent</div>
                                        <div class="fw-bold fs-5 text-danger">${att.absent || 0}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Attendance History Log -->
            <div class="app-card">
                <div class="app-card-header">
                    <h4 class="card-title-main"><i class="fa-solid fa-clock-rotate-left text-primary me-2"></i>Attendance History Logs</h4>
                    <span class="text-muted small">Recorded sessions for this student</span>
                </div>
                <div class="table-responsive">
                    <table class="custom-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Attendance Status</th>
                                <th>Remarks</th>
                                <th class="text-end pe-4">Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${renderAttendanceHistoryRows(att.logs || [])}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // Store loaded student for modal editing
        window.currentLoadedStudent = student;

    } catch (err) {
        console.error('Error loading student profile:', err);
        container.innerHTML = `
            <div class="alert alert-danger">Failed to load student profile. Check API connection.</div>
        `;
    }
}

function renderAttendanceHistoryRows(logs) {
    if (!logs || logs.length === 0) {
        return `
            <tr>
                <td colspan="4" class="text-center py-4 text-muted">No attendance sessions recorded yet.</td>
            </tr>
        `;
    }

    return logs.map(l => {
        const statusClass = l.status ? l.status.toLowerCase() : 'present';
        return `
            <tr>
                <td><strong>${escapeHtml(l.date)}</strong></td>
                <td><span class="badge-status ${statusClass}">${escapeHtml(l.status)}</span></td>
                <td>${escapeHtml(l.remarks || '—')}</td>
                <td class="text-end pe-4 text-muted small">${escapeHtml(l.marked_at || l.date)}</td>
            </tr>
        `;
    }).join('');
}

function openProfileEditModal(id) {
    const s = window.currentLoadedStudent;
    if (!s) return;

    document.getElementById('p-edit-id').value = s.id;
    document.getElementById('p-edit-code').value = s.student_id;
    document.getElementById('p-edit-usn').value = s.usn;
    document.getElementById('p-edit-name').value = s.full_name;
    document.getElementById('p-edit-gender').value = s.gender;
    document.getElementById('p-edit-email').value = s.email;
    document.getElementById('p-edit-phone').value = s.phone;
    document.getElementById('p-edit-dept').value = s.department;
    document.getElementById('p-edit-sem').value = s.semester;
    document.getElementById('p-edit-dob').value = s.dob;
    document.getElementById('p-edit-address').value = s.address || '';
    document.getElementById('p-edit-status').value = s.status || 'Active';

    const modal = new bootstrap.Modal(document.getElementById('editProfileModal'));
    modal.show();
}

async function handleProfileModalUpdate(e) {
    e.preventDefault();
    const alertBox = document.getElementById('p-edit-alert');
    const submitBtn = document.getElementById('p-edit-submit-btn');
    if (alertBox) alertBox.classList.add('d-none');
    if (submitBtn) submitBtn.disabled = true;

    const id = document.getElementById('p-edit-id').value;
    const payload = {
        student_id: document.getElementById('p-edit-code').value.trim(),
        usn: document.getElementById('p-edit-usn').value.trim().toUpperCase(),
        full_name: document.getElementById('p-edit-name').value.trim(),
        gender: document.getElementById('p-edit-gender').value,
        email: document.getElementById('p-edit-email').value.trim().toLowerCase(),
        phone: document.getElementById('p-edit-phone').value.trim(),
        department: document.getElementById('p-edit-dept').value,
        semester: parseInt(document.getElementById('p-edit-sem').value),
        dob: document.getElementById('p-edit-dob').value,
        address: document.getElementById('p-edit-address').value.trim(),
        status: document.getElementById('p-edit-status').value
    };

    try {
        const res = await fetch(`/api/students/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok && data.success) {
            showToast('Student profile updated successfully!', 'success');
            const modalEl = document.getElementById('editProfileModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            loadProfile(payload.usn);
        } else {
            if (alertBox) {
                alertBox.textContent = data.error || 'Failed to update student profile.';
                alertBox.classList.remove('d-none');
            }
        }
    } catch (err) {
        if (alertBox) {
            alertBox.textContent = 'Server connection error.';
            alertBox.classList.remove('d-none');
        }
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

// XSS Sanitizer Helper
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
