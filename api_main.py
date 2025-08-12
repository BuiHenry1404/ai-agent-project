import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
load_dotenv()
from api.v1.router import api_router
from core.config import settings

# Initialize logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("study_planner_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for Study Planner API."""
    try:
        logger.info("🚀 Starting Study Planner API")
        logger.info(f"📚 LLM Provider in use: {settings.DEFAULT_LLM_PROVIDER}")
        yield
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("🛑 Shutting down Study Planner API")


# Create FastAPI app
app = FastAPI(
    title="Study Planner API",
    description="API for managing and generating study plans using AI agents.",
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    root_path=settings.SWAGGER_PATH,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Error handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "code": "VALIDATION_ERROR",
            "message": "Invalid request data"
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "SERVER_ERROR",
            "message": "An unexpected error occurred"
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Study Planner API",
        "version": settings.PROJECT_VERSION
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Study Planner API — Plan your learning with AI agents",
        "version": settings.PROJECT_VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_url": "/health"
    }


def main():
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )


if __name__ == "__main__":
    main()
