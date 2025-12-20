# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM Council is a Multi-Model AI Decision Framework that orchestrates multiple LLMs to collaboratively debate complex decisions. It uses streaming responses via Server-Sent Events (SSE) to show real-time council member responses and chairman synthesis.

**Key Concept**: The chairman model is intentionally separate from council members to avoid bias. The chairman synthesizes responses from council members but doesn't necessarily participate in the initial debate.

## Development Commands

### Backend (FastAPI/Python)
```bash
cd backend
pip install -r requirements.txt
python main.py                    # Start server on http://localhost:8000
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React/Vite)
```bash
cd frontend
npm install
npm run dev                       # Start dev server on http://localhost:5173
npm run build                     # Build for production
npm run preview                   # Preview production build
```

### Both Services
Backend runs on port 8000, frontend on port 5173. If port 8000 is in use:
```bash
lsof -ti:8000 | xargs kill -9    # Kill process on port 8000
```

## Code Validation

**IMPORTANT**: After making code changes, always validate that the Docker image still builds successfully:

```bash
docker compose build
```

This command:
- Validates frontend code compiles (Vite build)
- Validates backend dependencies install correctly
- Ensures production build artifacts are created
- Catches build-time errors before deployment

Common build failures:
- CSS class name errors (invalid Tailwind utilities)
- TypeScript/JavaScript import errors
- Python dependency conflicts
- Missing environment variables in build process

If the build fails, fix the errors before committing. A successful build should complete with:
```
✓ built in XXXms
bjeans/multi-ai-chat:latest  Built
```

## Architecture

### Backend Request Flow

1. **API Endpoint** (`api/council.py`) receives debate request
2. **CouncilOrchestrator** (`services/orchestrator.py`) manages concurrent model execution:
   - Creates database decision record
   - Spawns async tasks for each council member
   - Uses `asyncio.Queue` for real-time event streaming
   - Each model streams tokens immediately via `_stream_model_response()`
   - After all responses complete, chairman synthesizes results
3. **LiteLLMClient** (`services/litellm_client.py`) communicates with LiteLLM proxy
4. **DecisionService** (`services/db.py`) persists to SQLite via async SQLAlchemy
5. **SynthesisService** (`services/synthesis.py`) generates chairman analysis

### Critical Implementation Details

**SSE Streaming Architecture**:
- Use `StreamingResponse` (NOT `EventSourceResponse`) to avoid double-wrapping SSE events
- Events must be formatted: `event: <type>\ndata: <json>\n\n`
- Orchestrator yields events directly from async queue for real-time streaming
- DO NOT collect events in arrays - this breaks real-time streaming

**Async Database Pattern**:
- ALWAYS use `selectinload()` when accessing relationships to avoid `MissingGreenlet` errors
- Use explicit queries (`get_responses_for_decision()`) instead of lazy-loading relationships
- Database operations require `async with get_db() as db:` context manager

**Chairman Independence**:
- Chairman model can be different from council members
- `orchestrator.py:33` explicitly does NOT add chairman to council_members
- This prevents bias in synthesis

### Frontend State Management

**useStreamingDebate Hook** (`hooks/useStreamingDebate.js`):
- Manages SSE connection using ReadableStream and TextDecoder
- Parses SSE events: `event: <type>\ndata: <json>`
- Updates `modelResponses` state incrementally as chunks arrive
- Buffer management splits on `\n\n` to handle partial events

**Historical vs Live Data** (`App.jsx`):
- `historicalData` state stores fetched past decisions
- `displayResponses` and `displaySynthesis` switch between historical/live data
- Historical data is transformed to match streaming format for unified rendering
- Same components (CouncilMemberCard, SynthesisPanel) render both data types

### Database Schema

**Decision** (primary record)
- `chairman_model`: The model that synthesizes responses
- Relationships: `responses` (one-to-many), `synthesis` (one-to-one)

**Response** (council member responses)
- `model_name`: Council member model ID
- `response_text`: Full response text
- `tokens_used`, `response_time`: Metrics

**Synthesis** (chairman's analysis)
- `consensus_items`: JSON array of agreed points
- `debates`: JSON array of disagreements with topic/positions structure
- `synthesis_text`: Full chairman synthesis including formatted sections

## Environment Configuration

Backend requires `.env` with:
```
LITELLM_PROXY_URL=http://localhost:4000
LITELLM_API_KEY=your-api-key-here
DATABASE_URL=sqlite+aiosqlite:///./database.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Common Pitfalls

1. **Lazy Loading Relationships**: Always use `selectinload()` or explicit queries in async contexts
2. **SSE Event Format**: Must use `StreamingResponse` with proper event/data format
3. **Real-time Streaming**: Never collect events in arrays before yielding
4. **Chairman Bias**: Don't automatically add chairman to council members
5. **Port Conflicts**: Backend port 8000 may be in use from previous sessions

## Synthesis Prompt Format

The chairman receives a structured prompt (`services/synthesis.py:37-73`) requesting:
1. **CONSENSUS**: Bullet points of agreement (prefix: `• `)
2. **DEBATES**: Bullet points of disagreements with format `topic: positions` (prefix: `• `)
3. **SYNTHESIS**: Final balanced conclusion

Parser (`_parse_synthesis()`) extracts these sections by detecting uppercase headers and bullet points.

## SSE Event Types

- `debate_start`: Includes decision_id, query, council_members, chairman
- `model_start`: Model begins responding
- `model_chunk`: Single token/chunk from model (critical for real-time display)
- `model_complete`: Model finished, includes tokens and response_time
- `model_error`: Model encountered error
- `synthesis_start`: Chairman begins analysis
- `synthesis_complete`: Includes consensus_items, debates, synthesis_text
- `debate_complete`: Entire debate finished

## Testing Streaming

Test SSE endpoint directly:
```bash
curl -N -H "Content-Type: application/json" \
  -d '{"query":"test","council_members":["model1","model2"],"chairman":"model1"}' \
  http://localhost:8000/api/council/debate
```

Should see properly formatted SSE events, NOT nested `data: event:` structures.
