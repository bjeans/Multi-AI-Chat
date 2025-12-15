# LLM Council - Multi-Model AI Decision Framework

A sophisticated application that orchestrates multiple LLMs to collaboratively reason through complex decisions, showing their debates, areas of consensus, and synthesized recommendations.

Inspired by [Satya Nadella's demonstration](https://www.youtube.com/watch?v=SEZADIErqyw) of multi-model decision-making frameworks.

## Features

- **Multi-Model Orchestration**: Run multiple LLMs concurrently to debate questions
- **Real-Time Streaming**: Watch responses stream in real-time from each council member
- **Chairman Synthesis**: Designated chairman model synthesizes consensus and debates
- **Decision History**: Browse and review past decisions with full audit trail
- **LiteLLM Integration**: Unified interface for local (Ollama) and cloud models

## Architecture

### Backend (Python/FastAPI)
- FastAPI server with async operations
- Server-Sent Events (SSE) for streaming responses
- SQLite database for decision history
- LiteLLM proxy integration

### Frontend (React/Vite)
- Modern React with hooks
- Real-time streaming display
- TailwindCSS for styling
- Clean, responsive UI

## Prerequisites

- Python 3.10+
- Node.js 18+
- LiteLLM proxy running (default: `http://localhost:4000`)
- Ollama (optional, for local models)

## Deployment Options

### Option 1: Docker (Recommended for Production)

The easiest way to run the application is using Docker:

```bash
# 1. Create .env file with your LiteLLM configuration
# See .env.docker.example for reference

# 2. Build and run
docker-compose up -d

# 3. Access the application
# Open http://localhost:8000
```

For detailed Docker deployment instructions, see [DOCKER.md](DOCKER.md).

### Option 2: Local Development Setup

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment - copy .env.example to .env and update
cp .env.example .env
# Edit .env with your LiteLLM proxy URL

# Run the server
python main.py
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will start on `http://localhost:5173`

## Usage

1. **Open the application** at `http://localhost:5173`

2. **Enter your question** in the query text area

3. **Select council members** - Choose at least 2 models to participate

4. **Designate a chairman** - This model will synthesize the final conclusion

5. **Start the debate** - Watch responses stream in real-time

6. **Review synthesis** - See consensus points, debates, and chairman's synthesis

7. **Browse history** - View past decisions and their complete audit trails

## API Endpoints

### Models
- `GET /api/config/models` - Get available models
- `POST /api/config/test-model` - Test model availability

### Council Debate
- `POST /api/council/debate` - Start a council debate (SSE streaming)

### History
- `GET /api/history/` - List all decisions
- `GET /api/history/{id}` - Get decision details

## SSE Event Types

The streaming debate endpoint emits the following events:

- `debate_start` - Debate begins
- `model_start` - Model starts responding
- `model_chunk` - Streaming token from model
- `model_complete` - Model finishes
- `model_error` - Model encounters error
- `synthesis_start` - Chairman begins synthesis
- `synthesis_complete` - Synthesis ready
- `debate_complete` - Debate finished

## Database Schema

### Decisions Table
- `id`: Primary key
- `query`: The question/decision
- `chairman_model`: Model acting as chairman
- `created_at`, `updated_at`: Timestamps

### Responses Table
- `id`: Primary key
- `decision_id`: Foreign key to decisions
- `model_name`: Model that provided response
- `response_text`: Full response
- `tokens_used`: Token count
- `response_time`: Time to complete

### Synthesis Table
- `id`: Primary key
- `decision_id`: Foreign key to decisions
- `consensus_items`: JSON array of consensus points
- `debates`: JSON array of debate points
- `synthesis_text`: Chairman's synthesis

## Configuration

### Environment Variables

Backend `.env`:
```
LITELLM_PROXY_URL=http://localhost:4000
LITELLM_API_KEY=your-api-key-here
DATABASE_URL=sqlite+aiosqlite:///./database.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Development

### Backend Development
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Build for Production
```bash
cd frontend
npm run build
```

## Future Enhancements (Phase 2+)

- **DxO Framework**: Role-assignment system (Lead Researcher, Critical Reviewer, etc.)
- **Ensemble Framework**: Anonymization and different synthesis methods
- **Custom Prompts**: Template system for debate prompts
- **Model Weighting**: Confidence scoring and weighted synthesis
- **Semantic Analysis**: Advanced consensus/debate detection
- **Export Options**: JSON, Markdown, PDF exports
- **User Authentication**: Multi-user support

## License

MIT

## Version

1.0.0 - Phase 1: LLM Council Framework MVP
