-- PostgreSQL initialization script for HSA Manager
-- This script sets up the database with required extensions and initial configuration

-- Enable necessary extensions for vector operations (for future RAG implementation)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- Note: pgvector extension would need to be installed separately if using vector embeddings
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Set timezone
SET timezone = 'UTC';

-- Create any additional database configuration here
-- Tables will be created by SQLAlchemy migrations

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hsa_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hsa_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO hsa_user;

-- Set default permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO hsa_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO hsa_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO hsa_user;

-- Log successful initialization
\echo 'Database initialization completed successfully';