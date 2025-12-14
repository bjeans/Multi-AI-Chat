from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv

from services.db import init_db
from api import council, history, config

load_dotenv()

# Get CORS origins from environment
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Initialize database
    await init_db()
    print("Database initialized")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down")


# Create FastAPI app
app = FastAPI(
    title="LLM Council Framework API",
    description="Multi-model AI decision framework with streaming debates",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(council.router)
app.include_router(history.router)
app.include_router(config.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Serve static files for production (when running in Docker)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        """Serve the frontend index.html"""
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA - return index.html for all non-API routes"""
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path.startswith("health"):
            return {"error": "Not found"}

        # Try to serve the file if it exists
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))

        # Otherwise return index.html for client-side routing
        return FileResponse(str(static_dir / "index.html"))
else:
    # Development mode - just return API info
    @app.get("/")
    async def root():
        """Health check endpoint"""
        return {
            "status": "ok",
            "message": "LLM Council Framework API",
            "version": "1.0.0",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
