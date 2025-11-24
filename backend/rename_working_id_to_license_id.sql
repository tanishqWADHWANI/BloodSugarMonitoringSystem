-- SQL script to rename working_id to license_id in specialists and staff tables
-- This changes the field name to reflect that it stores province/state professional license numbers

USE blood_sugar_db;

-- Rename column in specialists table
ALTER TABLE specialists 
CHANGE COLUMN working_id license_id VARCHAR(50) DEFAULT NULL;

-- Rename column in staff table  
ALTER TABLE staff 
CHANGE COLUMN working_id license_id VARCHAR(50) DEFAULT NULL;

-- Verify the changes
DESCRIBE specialists;
DESCRIBE staff;

SELECT 'Database schema updated: working_id renamed to license_id in specialists and staff tables' AS status;
