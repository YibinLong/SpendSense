"""
SpendSense FastAPI Application

This is the main entry point for the SpendSense backend API.
It sets up the FastAPI app, configures logging, and defines core routes.

Why this file exists:
- FastAPI needs a main app instance to run
- We configure logging here so it's ready for all requests
- Health check endpoint helps verify the app is running
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from spendsense.app.core.config import settings
from spendsense.app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan context manager for startup and shutdown tasks.
    
    This runs when the app starts and when it shuts down.
    
    Why we use this:
    - Configure logging once at startup
    - Log when the app starts and stops
    - Clean up resources on shutdown if needed
    """
    # Startup
    configure_logging(debug=settings.debug, log_level=settings.log_level)
    logger = get_logger(__name__)
    logger.info(
        "app_startup",
        environment=settings.app_env,
        debug=settings.debug,
        api_host=settings.api_host,
        api_port=settings.api_port,
    )
    
    yield  # App runs here
    
    # Shutdown
    logger.info("app_shutdown")


# Create the FastAPI application
# This is the main object that uvicorn will run
app = FastAPI(
    title="SpendSense API",
    description=(
        "Transform transaction data into explainable behavioral insights "
        "and personalized financial education with strict consent guardrails."
    ),
    version="0.1.0",
    lifespan=lifespan,
    # Auto-generated docs available at /docs and /redoc
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS to allow frontend to call the API
# This allows requests from the frontend running on a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.frontend_port}",
        f"http://127.0.0.1:{settings.frontend_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Simple JSON confirming the API is running
    
    Why this exists:
    - Quickly verify the API is up and responding
    - Useful for monitoring and deployment checks
    - No authentication needed (public endpoint)
    
    Example:
        GET http://127.0.0.1:8000/health
        Response: {"status": "healthy", "app": "SpendSense"}
    """
    return {
        "status": "healthy",
        "app": "SpendSense",
        "environment": settings.app_env,
    }


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint with API information.
    
    Returns:
        Welcome message and links to documentation
    
    Why this exists:
    - Provides a friendly landing page for the API
    - Directs users to the interactive docs
    """
    return {
        "message": "Welcome to SpendSense API",
        "docs": "/docs",
        "health": "/health",
        "version": "0.1.0",
    }


# Future route modules will be added here:
# app.include_router(users.router, prefix="/users", tags=["users"])
# app.include_router(profiles.router, prefix="/profile", tags=["profiles"])
# app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
# app.include_router(operator.router, prefix="/operator", tags=["operator"])

