## Docker Setup (Recommended)

### Prerequisites
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Ensure Docker is running on your machine

### Quick Start
1. Clone the repository and navigate to the project directory
2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
3. Update the `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-actual-openai-api-key-here
   ```
4. Start all services with Docker Compose:
   ```bash
   docker compose up --build
   ```

### Service Architecture
The Docker setup includes:
- **Frontend**: React SPA served by nginx (port 3000)
- **Backend**: FastAPI application with Python 3.11 (port 8000) 
- **Database**: PostgreSQL 15 with vector extension support (port 5432)
- **Cache**: Redis 7 for session and data caching (port 6379)

### Docker Commands

**Start all services:**
```bash
docker compose up --build
```

**Start in background:**
```bash
docker compose up -d --build
```

**Start with development tools (pgAdmin, Redis Commander):**
```bash
docker compose --profile dev up --build
```

**Stop all services:**
```bash
docker compose down
```

**View logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

**Reset all data (removes volumes):**
```bash
docker compose down -v
```

### Health Checks
Once running, verify all services:
- Frontend: http://localhost:3000/health
- Backend: http://localhost:8000/health
- Backend API docs: http://localhost:8000/docs

### Development Tools (Optional)
Start with `--profile dev` to access:
- **pgAdmin**: http://localhost:8080 (Database management)
- **Redis Commander**: http://localhost:8081 (Redis management)

### Environment Variables
All required environment variables are documented in `.env.example`:

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `DB_PASSWORD`: Secure database password
- `SECRET_KEY`: Application secret key

**Optional:**
- Development tool credentials
- Advanced database/Redis configuration
- CORS and security settings

### Docker Architecture Features
- **Multi-stage builds** for optimized image sizes
- **Non-root users** for enhanced security
- **Health checks** for all services
- **Persistent volumes** for data storage
- **Automatic restarts** on failure
- **Network isolation** between services
- **Resource optimization** with minimal base images

### Troubleshooting

**Services not starting:**
```bash
docker compose ps
docker compose logs [service-name]
```

**Port conflicts:**
Stop other applications using ports 3000, 8000, 5432, or 6379.

**Permission issues:**
```bash
docker compose down
docker system prune -f
docker compose up --build
```

**Database connection issues:**
Ensure PostgreSQL service is healthy:
```bash
docker compose exec database pg_isready -U hsa_user
```

---

## 📚 Documentation

### Infrastructure & Setup
- **[docs/infrastructure/](./docs/infrastructure/)** - Complete infrastructure documentation
  - [OpenAI Setup Guide](./docs/infrastructure/OPENAI_SETUP.md) - HSA Assistant configuration
  - [Test Analysis Report](./docs/infrastructure/TEST_ANALYSIS_REPORT.md) - Testing coverage and metrics
  - [Infrastructure Overview](./docs/infrastructure/README.md) - Complete setup and troubleshooting guide

### Architecture & Features  
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture and design decisions
- **[docs/features/hsa_user_stories.md](./docs/features/hsa_user_stories.md)** - User stories and requirements
- **[PROJECT_ROADMAP.md](./PROJECT_ROADMAP.md)** - Development progress and activity log

---

## Manual Setup (Alternative)
If you prefer running services locally instead of Docker:

1) Copy .env.example to .env and fill in OPENAI_API_KEY
2) Ensure Python 3.10+ and Node 18+ are available
3) Install and configure PostgreSQL and Redis locally

**For detailed setup instructions, see [docs/infrastructure/](./docs/infrastructure/)**
