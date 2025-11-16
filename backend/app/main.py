"""
Main FastAPI application entry point.

Sets up the FastAPI app with all routes, middleware, and configurations.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.api.v1 import auth, parent, kid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A kid-safe conversational AI API with parental controls",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors with user-friendly messages.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Don't expose internal errors in production
    if settings.DEBUG:
        detail = str(exc)
    else:
        detail = "An internal error occurred. Please try again later."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail}
    )


# Health check endpoint
@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if the API is running and healthy."
)
async def health_check():
    """
    Health check endpoint.

    Returns the application status and version.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(parent.router, prefix="/api")
app.include_router(kid.router, prefix="/api")


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    """
    logger.info("Application shutting down...")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
