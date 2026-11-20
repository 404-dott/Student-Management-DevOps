-- ==========================================================
-- Student Management System Database Initialization
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
);

-- ----------------------------------------------------------
-- 2. Students Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    course VARCHAR(100) NOT NULL,
    enrollment_date DATE NOT NULL,
    status ENUM('Active', 'Graduated', 'Suspended') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------
-- 3. Seed Default Admin User
-- Credentials: username = admin, password = admin123
-- ----------------------------------------------------------
INSERT INTO admins (username, password_hash, full_name, email)
VALUES (
    'admin',
    'scrypt:32768:8:1$fTOjeaDN4Qw13GaY$94ebbd3e20678c14768ff8edb5b00549f39bf99167f9a0b86da2a79162fad228fabd094aaf25c9d1df887eed51329ecdd4ddf50e6889295abfc168f8e0a8bb1d',
    'System Administrator',
    'admin@university.edu'
)
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

-- ----------------------------------------------------------
-- 4. Seed Initial Student Records
-- ----------------------------------------------------------
INSERT INTO students (student_id, first_name, last_name, email, course, enrollment_date, status)
VALUES
    ('STU-1001', 'Alice', 'Johnson', 'alice.johnson@university.edu', 'Cloud Computing & DevOps', '2024-01-15', 'Active'),
    ('STU-1002', 'Brian', 'Smith', 'brian.smith@university.edu', 'Computer Science', '2023-09-01', 'Active'),
    ('STU-1003', 'Clara', 'Zhang', 'clara.zhang@university.edu', 'Data Science & AI', '2023-09-01', 'Active'),
    ('STU-1004', 'David', 'Patel', 'david.patel@university.edu', 'Cybersecurity', '2022-09-10', 'Graduated'),
    ('STU-1005', 'Emma', 'Williams', 'emma.williams@university.edu', 'Software Engineering', '2024-02-01', 'Active'),
    ('STU-1006', 'Faisal', 'Al-Mansoor', 'faisal.mansoor@university.edu', 'Cloud Computing & DevOps', '2023-01-20', 'Suspended'),
    ('STU-1007', 'Grace', 'Hopper', 'grace.hopper@university.edu', 'Computer Science', '2022-09-01', 'Graduated'),
    ('STU-1008', 'Henry', 'Cavill', 'henry.cavill@university.edu', 'Data Science & AI', '2024-03-12', 'Active')
ON DUPLICATE KEY UPDATE status = VALUES(status);
