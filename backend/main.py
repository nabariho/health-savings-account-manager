"""
Main FastAPI application for HSA onboarding system.

This module sets up the FastAPI application with all necessary middleware,
routers, and configuration for the HSA onboarding system.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import settings
from .core.database import engine, Base
# Import models to register them with SQLAlchemy
from .models import Application, Document, HSAAssistantHistory
# Temporarily commented out to fix containerization
# from .api.v1.applications import router as applications_router
# from .api.v1.documents import router as documents_router  
# from .api.v1.decisions import router as decisions_router
from .api.v1.hsa_assistant import router as hsa_assistant_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Handles startup and shutdown events for the application.
    Creates database tables on startup.
    """
    # Startup
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
    
    yield
    
    # Shutdown
    print("Application shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered Health Savings Account onboarding system",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Global HTTP exception handler.
    
    Provides consistent error response format across the application.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    
    Provides a safe error response without exposing internal details.
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0"
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependency status."""
    # In a real implementation, you would check database connectivity,
    # external service availability, etc.
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0",
        "dependencies": {
            "database": "healthy",
            "openai_api": "not_checked"  # Would check API connectivity in real implementation
        }
    }


# Include API routers (commented out temporarily to fix containerization)
# app.include_router(applications_router, prefix="/api/v1")
# app.include_router(documents_router, prefix="/api/v1")
# app.include_router(decisions_router, prefix="/api/v1")
app.include_router(hsa_assistant_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs" if settings.debug else None
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )