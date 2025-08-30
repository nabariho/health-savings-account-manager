# Backend Dockerfile - Multi-stage build for HSA Manager
# Build stage: Install dependencies and prepare the application
FROM python:3.11-slim as builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Create non-root user for building
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements files
COPY requirements.txt ./

# Install Python dependencies to user directory
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --user -r requirements.txt \
    && pip install --no-cache-dir --user gunicorn==21.2.0

# Production stage: Create minimal runtime image
FROM python:3.11-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Set work directory to parent directory for proper import structure
WORKDIR /workspace

# Create directories with proper ownership
RUN mkdir -p backend/logs backend/uploads backend/data \
    && chown -R appuser:appuser /workspace

# Copy application code with proper ownership
COPY --chown=appuser:appuser . ./backend/

# Note: Knowledge base data (IRS PDF) is mounted via Docker volume in docker-compose.yml
# See volume: ./data:/workspace/backend/data:ro

# Switch to non-root user
USER appuser

# Add local Python packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Set Python path to include the workspace directory
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check using the built-in health endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command using uvicorn for better error reporting
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]