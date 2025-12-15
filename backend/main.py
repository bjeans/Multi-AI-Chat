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

# Include routers - these must be registered BEFORE catch-all routes
# FastAPI matches specific routes before catch-all patterns
app.include_router(council.router)
app.include_router(history.router)
app.include_router(config.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Serve static files for production (when running in Docker)
# This section handles serving the built React frontend
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Mount static assets (CSS, JS, images)
    # Note: Vite outputs assets to dist/assets/ by default
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        """Serve the frontend index.html"""
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        Serve SPA - handles all non-API routes for client-side routing.

        Note: API routes (/api/*, /health) are handled by routers registered above.
        FastAPI matches specific routes before this catch-all pattern.
        """
        # Prevent path traversal attacks (e.g., "../../../etc/passwd")
        try:
            # Resolve the full path and ensure it's within static_dir
            file_path = (static_dir / full_path).resolve()

            # Security check: ensure resolved path is still within static_dir
            if not str(file_path).startswith(str(static_dir.resolve())):
                # Path traversal attempt detected
                return FileResponse(str(static_dir / "index.html"))

            # If file exists and is within static_dir, serve it
            if file_path.is_file():
                return FileResponse(str(file_path))
        except (ValueError, OSError):
            # Handle invalid paths
            pass

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
