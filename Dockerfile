# Multi-AI Chat - Docker Container
# Multi-stage build for LLM Council Multi-AI Chat Application
# https://github.com/bjeans/Multi-AI-Chat
# https://hub.docker.com/r/bjeans/multi-ai-chat

# === Frontend Builder Stage ===
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files explicitly
# npm ci requires both package.json and package-lock.json
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies with clean install (faster, more reliable for CI/CD)
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# === Runtime Stage ===
FROM python:3.14-alpine

# Metadata
LABEL maintainer="Barnaby Jeans <barnaby@bjeans.dev>"
LABEL description="Multi-AI debate platform using LLM council for synthesized responses"
LABEL org.opencontainers.image.source="https://github.com/bjeans/Multi-AI-Chat"
LABEL org.opencontainers.image.licenses="MIT"

# Create non-root user for security
RUN adduser -D -u 1000 appuser && \
    mkdir -p /app /app/data && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy backend requirements
COPY --chown=appuser:appuser backend/requirements.txt ./

# Upgrade pip to 25.3+ and install Python dependencies (mitigates CVE-2025-8869)
RUN pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY --chown=appuser:appuser backend/ ./

# Copy built frontend from stage 1
COPY --chown=appuser:appuser --from=frontend-builder /frontend/dist ./static

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Environment variables with defaults
ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite+aiosqlite:///./data/database.db

# Health check (verifies the /health endpoint is responding)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
