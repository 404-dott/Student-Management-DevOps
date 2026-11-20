-- ==========================================================
-- Student Management System Database Initialization
-- MySQL 8.0 Schema & Seed Data
-- ==========================================================

CREATE DATABASE IF NOT EXISTS student_db;
USE student_db;

-- ----------------------------------------------------------
-- 1. Admins Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 2. Students Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL UNIQUE,
    usn VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    department VARCHAR(50) NOT NULL,
    semester INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    dob DATE NOT NULL,
    address TEXT,
    status ENUM('Active', 'Graduated', 'Suspended') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_usn (usn),
    INDEX idx_name (full_name),
    INDEX idx_dept (department)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 3. Attendance Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    status ENUM('Present', 'Absent', 'Late') NOT NULL DEFAULT 'Present',
    remarks VARCHAR(255) NULL,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) 
        REFERENCES students(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_student_date UNIQUE (student_id, date),
    INDEX idx_date (date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 4. Seed Default Admin User
-- Credentials: username = admin, password = admin123
-- ----------------------------------------------------------
INSERT INTO admins (username, password_hash, full_name, email)
VALUES (
    'admin',
    'scrypt:32768:8:1$OpmAyN21XmkGQrN8$3bb017dde473d56d16d03edd8cb42ba1c59f47dfd9e3f8f63de60615427081c9caa6e6ddef46ec88a557b19c1d574bc93b3a39452cb8eaa832d9c0ba298b07e7',
    'System Administrator',
    'admin@university.edu'
)
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

-- ----------------------------------------------------------
-- 5. Seed Initial Student Records
-- ----------------------------------------------------------
INSERT INTO students (student_id, usn, full_name, email, phone, department, semester, gender, dob, address, status)
VALUES
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
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

-- ----------------------------------------------------------
-- 6. Seed Sample Attendance Records
-- ----------------------------------------------------------
INSERT INTO attendance (student_id, date, status, remarks)
VALUES
    (1, CURRENT_DATE(), 'Present', 'On time'),
    (2, CURRENT_DATE(), 'Present', 'On time'),
    (3, CURRENT_DATE(), 'Present', 'On time'),
    (4, CURRENT_DATE(), 'Late', 'Joined 15m late with permission'),
    (5, CURRENT_DATE(), 'Absent', 'Medical leave'),
    (6, CURRENT_DATE(), 'Present', 'On time'),
    (7, CURRENT_DATE(), 'Present', 'On time'),
    (8, CURRENT_DATE(), 'Present', 'On time'),
    (9, CURRENT_DATE(), 'Absent', 'Unexcused'),
    (10, CURRENT_DATE(), 'Present', 'On time'),
    -- Previous date records
    (1, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Present', 'Regular'),
    (2, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Present', 'Regular'),
    (3, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Absent', 'Sick'),
    (4, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Present', 'Regular'),
    (5, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Present', 'Regular'),
    (7, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Present', 'Regular'),
    (8, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Late', 'Bus breakdown'),
    (9, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Present', 'Regular'),
    (10, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), 'Present', 'Regular')
ON DUPLICATE KEY UPDATE status = VALUES(status);
