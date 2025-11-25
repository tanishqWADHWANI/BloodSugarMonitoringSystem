-- ============================================================================
-- Blood Sugar Monitoring System - Demo Users Creation Script
-- ============================================================================
-- Purpose: Create staff and admin demo accounts for system testing
-- Usage: Execute this SQL script in MySQL/phpMyAdmin
-- 
-- Demo Accounts Created:
-- 1. Staff User (ID: 106)
--    Email: staff@clinic.com
--    Password: demo123 (SHA256 hashed)
--    Role: staff
--    License ID: STAFF-106
--
-- 2. Admin User (ID: 999)
--    Email: admin@clinic.com
--    Password: admin123 (SHA256 hashed)
--    Role: admin
--
-- Note: Uses ON DUPLICATE KEY UPDATE to avoid errors if users already exist
-- ============================================================================

-- Create demo staff and admin users

-- Staff User (ID: 106)
-- Create staff member with clinic access for managing specialists and patients
INSERT INTO users (user_id, role, first_name, last_name, email, phone, date_of_birth, password_hash, created_at, updated_at)
VALUES (106, 'staff', 'Staff', 'Demo', 'staff@clinic.com', '555-0106', '1985-06-15', SHA2('demo123', 256), NOW(), NOW())
ON DUPLICATE KEY UPDATE email = 'staff@clinic.com';

-- Insert into staff table with license ID
-- Links staff user to staff-specific data
INSERT INTO staff (user_id, license_id)
VALUES (106, 'STAFF-106')
ON DUPLICATE KEY UPDATE license_id = 'STAFF-106';

-- Admin User (ID: 999)
-- Create administrator with full system access
INSERT INTO users (user_id, role, first_name, last_name, email, phone, date_of_birth, password_hash, created_at, updated_at)
VALUES (999, 'admin', 'Admin', 'User', 'admin@clinic.com', '555-0999', '1980-01-01', SHA2('admin123', 256), NOW(), NOW())
ON DUPLICATE KEY UPDATE email = 'admin@clinic.com';

-- Verify the inserts
-- Display created users to confirm successful creation
SELECT user_id, role, first_name, last_name, email, phone FROM users WHERE user_id IN (106, 999);

