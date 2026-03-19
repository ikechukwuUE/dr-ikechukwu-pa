"""
Dr. Ikechukwu PA - FastAPI Entry Point
======================================
Main FastAPI application with rate limiting, CORS, and all domain routers.
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import structlog
from datetime import datetime
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

from .core.config import app_config
from .core.schemas import HealthCheckResponse, APIResponse
from .api import routes_cds, routes_finance, routes_aidev, routes_fashion
from .core.memory import get_memory_client

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()


# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID for tracing."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to logging
        logger = structlog.get_logger().bind(request_id=request_id)
        
        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    logger.info("application_starting", version=app_config.app_version)
    
    # Initialize memory client
    try:
        memory_client = get_memory_client()
        logger.info("memory_client_initialized")
    except Exception as e:
        logger.warning("memory_client_init_failed", error=str(e))
    
    yield
    
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=app_config.app_name,
    version=app_config.app_version,
    description="Multi-agent AI system for Clinical, Finance, AI-Dev, and Fashion domains",
    lifespan=lifespan,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware for tracing
app.add_middleware(RequestIDMiddleware)


# Add rate limiting
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "message": "Rate limit exceeded",
            "error": str(exc.detail),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions."""
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "error": "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(routes_cds.router, prefix="/api/cds", tags=["Clinical Decision Support"])
app.include_router(routes_finance.router, prefix="/api/finance", tags=["Finance"])
app.include_router(routes_aidev.router, prefix="/api/aidev", tags=["AI Development"])
app.include_router(routes_fashion.router, prefix="/api/fashion", tags=["Fashion"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return APIResponse(
        success=True,
        message=f"Welcome to {app_config.app_name}",
        data={
            "name": app_config.app_name,
            "version": app_config.app_version,
            "domains": ["cds", "finance", "aidev", "fashion"],
        },
    )


@app.get("/health", tags=["Health"], response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    # Check memory service
    memory_status = "unhealthy"
    try:
        memory_client = get_memory_client()
        if memory_client is not None:
            health = memory_client.health_check()
            memory_status = health.get("status", "unhealthy")
        else:
            memory_status = "unavailable"
    except Exception:
        pass
    
    # Determine overall status
    if memory_status == "healthy":
        overall_status = "healthy"
    elif memory_status == "degraded":
        overall_status = "degraded"
    else:
        overall_status = "degraded"  # Still running even without memory
    
    return HealthCheckResponse(
        status=overall_status,
        version=app_config.app_version,
        timestamp=datetime.utcnow(),
        services={
            "api": "healthy",
            "memory": memory_status,
        },
    )


@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """Basic metrics endpoint."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "requests_total": 0,
        "active_sessions": 0,
    }


# Export app for uvicorn
__all__ = ["app"]