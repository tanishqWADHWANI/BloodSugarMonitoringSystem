-- Create demo staff and admin users

-- Staff User (ID: 106)
INSERT INTO users (user_id, role, first_name, last_name, email, phone, date_of_birth, password_hash, created_at, updated_at)
VALUES (106, 'staff', 'Staff', 'Demo', 'staff@clinic.com', '555-0106', '1985-06-15', SHA2('demo123', 256), NOW(), NOW())
ON DUPLICATE KEY UPDATE email = 'staff@clinic.com';

-- Insert into staff table
INSERT INTO staff (user_id, license_id)
VALUES (106, 'STAFF-106')
ON DUPLICATE KEY UPDATE license_id = 'STAFF-106';

-- Admin User (ID: 999)
INSERT INTO users (user_id, role, first_name, last_name, email, phone, date_of_birth, password_hash, created_at, updated_at)
VALUES (999, 'admin', 'Admin', 'User', 'admin@clinic.com', '555-0999', '1980-01-01', SHA2('admin123', 256), NOW(), NOW())
ON DUPLICATE KEY UPDATE email = 'admin@clinic.com';

-- Verify the inserts
SELECT user_id, role, first_name, last_name, email, phone FROM users WHERE user_id IN (106, 999);
