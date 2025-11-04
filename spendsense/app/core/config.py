"""
Configuration management using Pydantic Settings.

This module reads environment variables from .env file and provides
type-safe configuration throughout the application.

Why this exists:
- Pydantic Settings automatically reads from .env file
- Provides type safety and validation for all config values
- Makes it easy to access configuration anywhere in the app
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All values are read from the .env file in the project root.
    Pydantic validates types automatically and raises clear errors
    if required values are missing or invalid.
    """
    
    # Application Environment
    app_env: Literal["dev", "prod"] = Field(
        default="dev",
        description="Application environment (dev or prod)"
    )
    seed: int = Field(
        default=42,
        description="Random seed for deterministic data generation"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode with verbose logging"
    )
    
    # Backend API Configuration
    api_host: str = Field(
        default="127.0.0.1",
        description="API server host address"
    )
    api_port: int = Field(
        default=8000,
        description="API server port"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./data/spendsense.db",
        description="SQLAlchemy database connection string"
    )
    
    # Data Storage Paths
    data_dir: str = Field(
        default="./data",
        description="Root directory for all data storage"
    )
    parquet_dir: str = Field(
        default="./data/parquet",
        description="Directory for Parquet analytics files"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="WARNING",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    # Frontend Configuration
    frontend_port: int = Field(
        default=5173,
        description="Frontend development server port"
    )
    
    # Pydantic Settings Configuration
    # This tells Pydantic to read from .env file automatically
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allow lowercase env vars
        extra="ignore"  # Ignore extra env vars not in model
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    def ensure_data_directories(self) -> None:
        """
        Create data directories if they don't exist.
        
        This is helpful during first-time setup to ensure
        the app can write data files without errors.
        """
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.parquet_dir).mkdir(parents=True, exist_ok=True)
    
    @property
    def is_dev(self) -> bool:
        """Helper to check if running in development mode."""
        return self.app_env == "dev"
    
    @property
    def is_prod(self) -> bool:
        """Helper to check if running in production mode."""
        return self.app_env == "prod"


# Create a singleton instance
# This is imported throughout the app to access configuration
settings = Settings()

# Ensure data directories exist on import
settings.ensure_data_directories()

