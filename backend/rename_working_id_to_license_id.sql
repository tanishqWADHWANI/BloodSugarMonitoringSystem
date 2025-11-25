-- ============================================================================
-- Blood Sugar Monitoring System - Database Migration Script
-- ============================================================================
-- Migration: Rename working_id to license_id
-- Purpose: Change field name to better reflect that it stores professional
--          license numbers (province/state medical license IDs)
-- 
-- Tables Affected:
-- 1. specialists - stores specialist medical license numbers
-- 2. staff - stores staff professional license numbers
--
-- Original Column: working_id VARCHAR(50)
-- New Column: license_id VARCHAR(50)
--
-- Usage: Execute this SQL script once in MySQL/phpMyAdmin
-- Note: This migration has been completed. This script is for reference only.
-- ============================================================================

-- SQL script to rename working_id to license_id in specialists and staff tables
-- This changes the field name to reflect that it stores province/state professional license numbers

USE blood_sugar_db;

-- Rename column in specialists table
-- Changes working_id to license_id while preserving all data and constraints
ALTER TABLE specialists 
CHANGE COLUMN working_id license_id VARCHAR(50) DEFAULT NULL;

-- Rename column in staff table
-- Changes working_id to license_id while preserving all data and constraints
ALTER TABLE staff 
CHANGE COLUMN working_id license_id VARCHAR(50) DEFAULT NULL;

-- Verify the changes
-- Display table structures to confirm column rename was successful
DESCRIBE specialists;
DESCRIBE staff;

-- Display confirmation message
SELECT 'Database schema updated: working_id renamed to license_id in specialists and staff tables' AS status;

