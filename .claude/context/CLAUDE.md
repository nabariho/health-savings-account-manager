# Project Memory for Claude Code
This repository’s product contract and implementation rules must always be considered.

## Canonical docs (imported)
@README.md
@docs/features/hsa_user_stories.md
@.claude/context/requirements.md
@.claude/context/openai.md
@.claude/context/engineering.md
@.claude/context/openai-model.md
@docs/infrastructure/OPENAI_SETUP.md
@docs/infrastructure/TEST_ANALYSIS_REPORT.md

## Infrastructure Characteristics
### Core Technology Stack
- **Frontend**: React 18 + TypeScript + Tailwind CSS (Vite build system)
- **Backend**: Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy 
- **Database**: PostgreSQL with pgvector for embeddings
- **Cache**: Redis for session management and response caching
- **AI Services**: OpenAI Vector Stores API with `gpt-4o-mini` and `text-embedding-3-large`

### HSA Assistant Service
- **Architecture**: OpenAI Vector Stores-based RAG system
- **Knowledge Source**: `data/knowledge_base/hsa/irs.pdf` (IRS HSA documentation)
- **API Endpoints**: `/api/v1/hsa_assistant/*` (renamed from `/qa/` for clarity)
- **Integration Pattern**: Two-step file upload → OpenAI Assistant with file_search tool
- **Environment**: Requires `OPENAI_API_KEY` for Vector Stores and Assistants API

### Docker Configuration
- **Multi-service**: Frontend (nginx), Backend (uvicorn), PostgreSQL, Redis
- **Health Checks**: All services include `/health` endpoints with proper validation
- **Security**: Non-root containers, minimal base images, no baked secrets
- **Development**: `docker compose up --build` for full local environment

### Deployment Requirements
- **Environment Variables**: See `.env.example` for complete configuration
- **File Access**: IRS PDF mounted as read-only volume in containers
- **API Keys**: OpenAI API key required for HSA Assistant functionality
- **Database**: Automatic migrations on startup, persistent volumes

## Instructions to all subagents
- Obey the imported docs as the source of truth.
- Frontend must be React + TypeScript + Tailwind.
- Backend must be a Python API; prefer OpenAI Vector Stores/Assistants for LLM work.
- HSA Assistant uses OpenAI Vector Stores API (not custom RAG implementations).
- All infrastructure documentation lives in `docs/infrastructure/`.
- Produce tests, code review notes, and Docker packaging as part of each slice.
- Never read `.env*` or `secrets/**`; treat secrets as environment variables only.
