import os
from typing import Dict
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers.digest import router as digest_router
from app.routers.users import router as users_router

# Load environment variables from .env file if present
load_dotenv()


def create_app() -> FastAPI:
    """Application factory for the FastAPI backend service."""
    application = FastAPI(
        title="Personalized Weekly Digest Engine API",
        version="0.1.0",
        description="Backend API service for personalized activity ranking and digest generation.",
    )

    # Register API routers with /api prefix
    application.include_router(digest_router, prefix="/api")
    application.include_router(users_router, prefix="/api")

    @application.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Global exception handler to handle unhandled exceptions cleanly."""
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    @application.get("/health")
    async def health_check() -> Dict[str, str]:
        """Health check endpoint to verify backend service availability."""
        return {"status": "ok"}

    return application


app: FastAPI = create_app()
