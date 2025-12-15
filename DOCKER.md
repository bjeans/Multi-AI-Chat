# Docker Deployment Guide

This guide explains how to deploy the LLM Council Multi-AI Chat Application using Docker.

## Overview

The application is containerized as a **single Docker container** that includes:
- FastAPI backend (Python)
- React frontend (built as static files)
- SQLite database (persisted via volume)

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- LiteLLM Proxy running (accessible from the container)

## Quick Start

### 1. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# LiteLLM Configuration
LITELLM_PROXY_URL=http://host.docker.internal:4000
LITELLM_API_KEY=your-api-key-here
```

**Notes:**
- Use `host.docker.internal:4000` if LiteLLM is running on your host machine
- Use the actual IP/hostname if LiteLLM is running elsewhere
- Replace `your-api-key-here` with your actual LiteLLM API key

### 2. Build and Run with Docker Compose

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The application will be available at: **http://localhost:8000**

### 3. Access the Application

Open your browser and navigate to:
- **Frontend UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Manual Docker Commands

If you prefer not to use Docker Compose:

### Build the Image

```bash
docker build -t llm-council:latest .
```

### Run the Container

```bash
docker run -d \
  --name llm-council-app \
  -p 8000:8000 \
  -e LITELLM_PROXY_URL=http://host.docker.internal:4000 \
  -e LITELLM_API_KEY=your-api-key-here \
  -e DATABASE_URL=sqlite+aiosqlite:///./data/database.db \
  -e CORS_ORIGINS=* \
  -v $(pwd)/data:/app/data \
  llm-council:latest
```

### View Logs

```bash
docker logs -f llm-council-app
```

### Stop and Remove

```bash
docker stop llm-council-app
docker rm llm-council-app
```

## Architecture

### Multi-Stage Build

The Dockerfile uses a multi-stage build process:

1. **Stage 1 (frontend-builder)**:
   - Uses Node.js Alpine image
   - Installs frontend dependencies
   - Builds React app with Vite
   - Outputs to `/frontend/dist`

2. **Stage 2 (final image)**:
   - Uses Python 3.11 slim image
   - Installs backend dependencies
   - Copies backend code
   - Copies built frontend from Stage 1 to `/app/static`
   - Configures FastAPI to serve both API and static files

### How It Works

- The backend FastAPI application (`main.py`) detects the `static` folder
- If present, it serves the frontend from `/app/static`
- API routes are available at `/api/*`
- All other routes serve the React SPA (Single Page Application)
- Database is persisted to `/app/data/database.db` (mounted as volume)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_PROXY_URL` | - | URL to LiteLLM proxy server |
| `LITELLM_API_KEY` | - | API key for LiteLLM authentication |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/database.db` | Database connection string |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |

### Volumes

- `./data:/app/data` - Persists the SQLite database outside the container

### Ports

- `8000:8000` - Main application port (frontend + backend)

## Production Deployment

### Security Considerations

1. **API Keys**: Never commit `.env` files. Use secrets management.
2. **CORS**: Restrict `CORS_ORIGINS` to specific domains in production.
3. **Reverse Proxy**: Use nginx or Traefik for SSL/TLS termination.
4. **Database**: Consider using PostgreSQL for production workloads.

### Recommended Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  llm-council:
    image: llm-council:latest
    container_name: llm-council-app
    restart: always
    ports:
      - "8000:8000"
    environment:
      - LITELLM_PROXY_URL=${LITELLM_PROXY_URL}
      - LITELLM_API_KEY=${LITELLM_API_KEY}
      - DATABASE_URL=sqlite+aiosqlite:///./data/database.db
      - CORS_ORIGINS=https://yourdomain.com
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### Using with Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Required for SSE streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs
```

Common issues:
- Port 8000 already in use
- Invalid LiteLLM credentials
- Missing environment variables

### Database issues

Reset the database:
```bash
# Stop container
docker-compose down

# Remove database
rm -rf ./data

# Restart
docker-compose up -d
```

### Frontend not loading

1. Verify the build completed successfully:
```bash
docker-compose logs | grep "Build complete"
```

2. Check if static files exist:
```bash
docker exec llm-council-app ls -la /app/static
```

### LiteLLM connection issues

If running LiteLLM on the host machine:
- **macOS/Windows**: Use `host.docker.internal:4000`
- **Linux**: Use `172.17.0.1:4000` or your host's IP

Test connectivity:
```bash
docker exec llm-council-app curl http://host.docker.internal:4000/health
```

## Health Checks

The container includes health checks:

```bash
# Check container health status
docker inspect llm-council-app | grep -A 10 Health

# Manual health check
curl http://localhost:8000/health
```

## Updating

### Update the Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

### View Changes

```bash
docker-compose logs -f
```

## Data Persistence

Database is persisted in `./data/database.db`:
- **Backup**: `cp ./data/database.db ./data/database.db.backup`
- **Restore**: `cp ./data/database.db.backup ./data/database.db`
- **Export**: Use SQLite tools to export/import data

## Development vs Production

The application automatically detects its environment:

- **Development**: Run backend and frontend separately (see QUICKSTART.md)
- **Production (Docker)**: Serves built frontend from backend

This is controlled by the presence of the `/app/static` folder in the container.
