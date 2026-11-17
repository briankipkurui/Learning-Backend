-- Initial database setup for Career Elevate
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas if needed
-- CREATE SCHEMA IF NOT EXISTS app;

-- You can add initial data or additional setup here
-- INSERT INTO users (name, email) VALUES ('Admin', 'admin@career-elevate.com');

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE career_elevate TO career_elevate_user;
