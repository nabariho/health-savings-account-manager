# Infrastructure Documentation

This folder contains all infrastructure-related documentation for the HSA Manager project.

## 📁 Documentation Index

### Setup & Configuration
- **[OPENAI_SETUP.md](./OPENAI_SETUP.md)** - OpenAI Vector Stores API setup guide
  - Environment configuration
  - API key management
  - Vector store initialization
  - Troubleshooting guide

### Testing & Analysis  
- **[TEST_ANALYSIS_REPORT.md](./TEST_ANALYSIS_REPORT.md)** - Comprehensive test coverage analysis
  - Unit test results and coverage
  - Integration test status
  - Performance benchmarks
  - Quality metrics

## 🏗️ Infrastructure Overview

### Core Technology Stack
- **Frontend**: React 18 + TypeScript + Tailwind CSS (Vite)
- **Backend**: Python 3.11 + FastAPI + Pydantic v2
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis for sessions and response caching
- **AI Services**: OpenAI Vector Stores API + Assistants API

### HSA Assistant Service
- **Architecture**: OpenAI Vector Stores-based RAG system
- **Knowledge Base**: `data/knowledge_base/hsa/irs.pdf` (IRS documentation)
- **API Pattern**: Two-step file upload → Assistant with file_search tool
- **Endpoints**: `/api/v1/hsa_assistant/*` for all HSA-related queries

### Docker Configuration
- **Services**: Frontend (nginx), Backend (uvicorn), PostgreSQL, Redis
- **Security**: Non-root containers, minimal images, no baked secrets
- **Health Checks**: All services monitored with proper validation
- **Development**: `docker compose up --build` for complete environment

## 🚀 Quick Start

### Prerequisites
1. **OpenAI API Key**: Required for HSA Assistant functionality
2. **Docker & Docker Compose**: For containerized deployment
3. **Node.js 18+**: For frontend development
4. **Python 3.11+**: For backend development

### Local Development
```bash
# Clone and setup
git clone <repository>
cd health-savings-account-manager

# Configure environment
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY

# Start all services
docker compose up --build

# Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# HSA Assistant: http://localhost:8000/api/v1/hsa_assistant/health
```

### Environment Variables
See `.env.example` for complete configuration. Key variables:
- `OPENAI_API_KEY`: Required for HSA Assistant service
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching

## 📋 Health Checks

All services include health endpoints:
- **Frontend**: `GET /health` → `healthy`
- **Backend**: `GET /health` → `{"status":"healthy"}`
- **HSA Assistant**: `GET /api/v1/hsa_assistant/health` → Service status with vector store info
- **Database**: Automatic health monitoring via connection pool
- **Redis**: Automatic health monitoring via connection check

## 📚 Related Documentation

- **[ARCHITECTURE.md](../../ARCHITECTURE.md)** - Overall system architecture
- **[README.md](../../README.md)** - Project overview and setup
- **[docs/features/hsa_user_stories.md](../features/hsa_user_stories.md)** - User stories and requirements
- **[.claude/context/engineering.md](../../.claude/context/engineering.md)** - Engineering standards and practices

## 🔧 Troubleshooting

### Common Issues
1. **OpenAI API Errors**: Check API key configuration in OPENAI_SETUP.md
2. **Docker Build Failures**: Ensure Docker has sufficient memory (4GB+)
3. **Health Check Failures**: Check service logs with `docker compose logs <service>`
4. **Database Connection Issues**: Verify PostgreSQL is running and accessible

### Support
- Check service logs: `docker compose logs -f <service-name>`
- Verify configuration: All environment variables in `.env` file
- Test individual services: Use health check endpoints listed above

---

For detailed setup instructions, see individual documentation files in this folder.