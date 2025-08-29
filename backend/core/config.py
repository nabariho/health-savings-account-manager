"""
Configuration management for HSA backend application.

This module provides configuration management using Pydantic settings,
supporting environment variables and default values for all application settings.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings.
    
    All settings can be overridden using environment variables.
    For example, OPENAI_API_KEY environment variable will override openai_api_key.
    """
    
    # Database configuration
    database_url: str = Field(
        default="sqlite:///./hsa_app.db",
        description="Database connection URL"
    )
    
    # OpenAI API configuration
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for LLM services"
    )
    
    # Application settings
    app_name: str = Field(
        default="HSA Onboarding System",
        description="Application name"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # API configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API host address"
    )
    
    api_port: int = Field(
        default=8000,
        description="API port number"
    )
    
    # CORS configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    
    # File upload configuration
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file upload size in bytes"
    )
    
    upload_dir: str = Field(
        default="./uploads",
        description="Directory for uploaded files"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()