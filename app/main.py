"""
Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router
from app.db.session import close_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events.

    This replaces the deprecated @app.on_event decorators.
    """
    # Startup
    print("🚀 Starting Soccer Analytics API...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Database: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"📦 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    yield

    # Shutdown
    print("🛑 Shutting down Soccer Analytics API...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## Soccer Player Analytics API

    A comprehensive REST API for managing and analyzing soccer player data.

    ### Features

    * **Player Management**: Full CRUD operations for player records
    * **Advanced Filtering**: Search and filter players by multiple criteria
    * **Statistics**: Calculate and retrieve player statistics and ratings
    * **Async Operations**: Fully asynchronous for high performance
    * **Background Tasks**: Celery integration for data scraping and processing
    * **Pagination**: Efficient pagination for large datasets

    ### Technology Stack

    * **FastAPI**: Modern, high-performance web framework
    * **PostgreSQL**: Robust relational database
    * **SQLAlchemy 2.0**: Async ORM with type hints
    * **Celery**: Distributed task queue
    * **Redis**: Caching and message broker
    * **Docker**: Containerized deployment

    ### API Endpoints

    * `/api/v1/players`: Player management endpoints
    * `/api/v1/players/top/scorers`: Top scorer statistics
    * `/api/v1/players/stats/overview`: Overall statistics
    * `/health`: Health check endpoint
    * `/docs`: Interactive API documentation (Swagger UI)
    * `/redoc`: Alternative API documentation (ReDoc)
    """,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint.

    Returns basic API information and available endpoints.
    """
    return {
        "message": "Welcome to Soccer Analytics API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "api": settings.API_V1_PREFIX,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Used by Docker and monitoring systems to verify the API is running.

    Returns:
        Dict with health status and system information
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/info", tags=["Info"])
async def info() -> dict:
    """
    Get detailed API information.

    Returns configuration details and service status.
    """
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "api_prefix": settings.API_V1_PREFIX,
        "database": {
            "host": settings.POSTGRES_SERVER,
            "port": settings.POSTGRES_PORT,
            "database": settings.POSTGRES_DB,
        },
        "redis": {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
        },
        "features": {
            "async": True,
            "celery": True,
            "pagination": True,
            "filtering": True,
            "cors": bool(settings.BACKEND_CORS_ORIGINS),
        },
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.

    Args:
        request: The request that caused the exception
        exc: The exception that was raised

    Returns:
        JSON response with error details
    """
    # In production, you would log this to a logging service
    print(f"❌ Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )
