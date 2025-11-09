"""
SpendSense FastAPI Application

This is the main entry point for the SpendSense backend API.
It sets up the FastAPI app, configures logging, and defines core routes.

Why this file exists:
- FastAPI needs a main app instance to run
- We configure logging here so it's ready for all requests
- Health check endpoint helps verify the app is running
"""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

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

# CORS Debugging Middleware - logs all requests
class CORSDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = get_logger(__name__)
        logger.info(
            "incoming_request",
            method=request.method,
            path=request.url.path,
            origin=request.headers.get("origin"),
            headers=dict(request.headers)
        )
        response = await call_next(request)
        logger.info(
            "outgoing_response",
            status=response.status_code,
            headers=dict(response.headers)
        )
        return response

# Add debug middleware first
app.add_middleware(CORSDebugMiddleware)

# Configure CORS to allow frontend to call the API
# EXTREMELY PERMISSIVE (temporary to unblock deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",  # Allow ALL origins (temporary)
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        f"http://localhost:{settings.frontend_port}",
        f"http://127.0.0.1:{settings.frontend_port}",
        "https://spend-sense-alpha-liard.vercel.app",
    ],
    allow_credentials=False,  # Simpler CORS; we use Authorization header, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# Catch-all OPTIONS handler to ensure preflight requests always succeed
@app.options("/{full_path:path}")
async def preflight_catch_all(full_path: str, request: Request) -> PlainTextResponse:
    """
    Respond to any CORS preflight request with 204 and let CORSMiddleware
    attach the appropriate Access-Control-* headers.
    """
    return PlainTextResponse("", status_code=status.HTTP_204_NO_CONTENT)


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


# Import route modules
from spendsense.app.api import (
    routes_auth,
    routes_consent,
    routes_operator,
    routes_profiles,
    routes_recommendations,
    routes_transactions,
    routes_users,
)

# Include all routers
app.include_router(routes_auth.router)  # Auth routes already have /auth prefix
app.include_router(routes_users.router, prefix="/users", tags=["users"])
app.include_router(routes_consent.router, prefix="/consent", tags=["consent"])
app.include_router(routes_profiles.router, prefix="/profile", tags=["profiles"])
app.include_router(routes_recommendations.router, prefix="/recommendations", tags=["recommendations"])
app.include_router(routes_transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(routes_operator.router, prefix="/operator", tags=["operator"])


# Exception handlers for structured error responses

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Returns 422 with structured error response showing field-level errors.
    
    Why this exists:
    - PRD requires structured errors with clear field-level feedback
    - Makes it easy for frontend to show validation errors
    - Includes trace ID for debugging
    """
    trace_id = str(uuid.uuid4())
    logger = get_logger(__name__)

    logger.warning(
        "validation_error",
        trace_id=trace_id,
        path=request.url.path,
        errors=exc.errors(),
    )

    # Format field errors
    field_errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        field_errors[field] = error["msg"]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": "Request data failed validation",
            "field_errors": field_errors,
            "trace_id": trace_id,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected errors.
    
    Returns 500 with trace ID for debugging.
    
    Why this exists:
    - Catch-all for unexpected errors
    - Logs full exception for debugging
    - Returns user-friendly error without exposing internals
    """
    trace_id = str(uuid.uuid4())
    logger = get_logger(__name__)

    logger.error(
        "unexpected_error",
        trace_id=trace_id,
        path=request.url.path,
        error=str(exc),
        exc_info=True,  # Include traceback
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please contact support with the trace ID.",
            "trace_id": trace_id,
        },
    )

