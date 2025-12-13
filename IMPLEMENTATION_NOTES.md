# LLM Council - Implementation Notes

## Architecture Decisions

### Why These Technologies?

**FastAPI + Async/Await**
- Native async support for concurrent model calls
- Built-in OpenAPI documentation
- Easy SSE streaming with sse-starlette
- Production-ready with uvicorn

**LiteLLM Proxy Integration**
- Unified interface for 100+ LLM providers
- Already running in your environment
- Handles API keys and rate limiting
- OpenAI-compatible endpoints

**Server-Sent Events (SSE) vs WebSockets**
- SSE is simpler for request-response patterns
- Built-in browser EventSource API
- Automatic reconnection
- HTTP/2 compatible
- No need for bidirectional communication

**SQLite + SQLAlchemy**
- Zero configuration database
- Async support with aiosqlite
- Easy to inspect (`.db` file)
- Can upgrade to PostgreSQL without code changes
- Perfect for local/single-instance deployments

**React + Vite**
- Fast hot-reload development
- Modern build tooling
- Simple component model
- No complex state management needed

**TailwindCSS**
- Rapid UI development
- Consistent design system
- Dark mode support built-in
- Small bundle size with purging

## Key Implementation Details

### Concurrent Model Orchestration

Located in `backend/services/orchestrator.py`

The orchestrator uses `asyncio.as_completed()` to run all model calls concurrently while streaming results as they arrive:

```python
tasks = [
    self._get_model_response(model_id, query, decision_id)
    for model_id in council_members
]

for coro in asyncio.as_completed(tasks):
    model_id, events = await coro
    for event in events:
        yield event  # Stream to frontend immediately
```

This ensures:
- Models run in parallel (not sequential)
- Fastest models appear first
- No blocking on slow models
- Real-time user feedback

### SSE Event Flow

The streaming debate follows this event sequence:

1. `debate_start` - Signals debate initialization
2. `model_start` - Each model begins responding
3. `model_chunk` - Individual tokens stream in
4. `model_complete` - Model finishes with metadata
5. `synthesis_start` - Chairman begins synthesis
6. `synthesis_complete` - Final synthesis ready
7. `debate_complete` - Entire debate finished

Error events (`model_error`, `synthesis_error`) can occur at any point.

### Frontend State Management

Located in `frontend/src/hooks/useStreamingDebate.js`

The custom hook manages streaming state:
- Maintains `modelResponses` object keyed by model ID
- Updates state on each SSE event
- Handles partial text accumulation
- Tracks model status (pending → streaming → complete)

```javascript
case 'model_chunk':
  setModelResponses(prev => ({
    ...prev,
    [data.model_id]: {
      ...prev[data.model_id],
      text: prev[data.model_id].text + data.chunk,
    },
  }));
  break;
```

### Synthesis Algorithm

Located in `backend/services/synthesis.py`

The chairman model receives a structured prompt:
1. Original question
2. All council member responses
3. Instructions to identify consensus and debates
4. Required output format

The chairman's response is parsed to extract:
- Consensus items (bullet points under CONSENSUS section)
- Debates (topic:positions pairs under DEBATES section)
- Full synthesis text

This leverages the LLM's reasoning rather than simple keyword matching.

### Database Relationships

```
Decision (1) ─┬─ (many) Responses
              └─ (1) Synthesis
```

- One decision has many responses (one per council member)
- One decision has one synthesis (from chairman)
- Cascade delete ensures cleanup

### Error Handling Philosophy

**Graceful Degradation**
- If one model fails, others continue
- Minimum 2 successful responses required for synthesis
- Errors displayed inline but don't block progress

**User Feedback**
- All errors shown in UI
- Status indicators on each response card
- Network issues don't crash the app

## Performance Considerations

### Concurrent Requests
- All models called simultaneously via asyncio
- No sequential bottleneck
- Response time = slowest model (not sum of all)

### Database
- Async SQLAlchemy prevents blocking
- Eager loading of relationships where needed
- Indexes on decision_id foreign keys

### Frontend
- React memo could be added for heavy components
- Streaming text updates are optimized (single state update per chunk)
- Virtual scrolling not needed (typical debates have 2-5 models)

## Security Considerations

### Current Implementation
- **Local deployment only** (no authentication)
- CORS restricted to localhost
- LiteLLM proxy handles API keys
- No user input sanitization needed (LLMs handle arbitrary text)
- SQLite file permissions inherit from process

### Production Recommendations
- Add authentication (OAuth, JWT)
- Rate limiting on debate endpoint
- Input validation on query length
- HTTPS required
- PostgreSQL with connection pooling
- Environment-based configuration
- Audit logging

## Scalability Notes

### Current Limits
- Single instance (no load balancing)
- SQLite (concurrent writes limited)
- In-memory SSE connections
- No caching layer

### Scaling Path
1. **Add Redis** for shared state
2. **PostgreSQL** for concurrent writes
3. **Background workers** (Celery) for debates
4. **Message queue** (RabbitMQ) for event distribution
5. **Load balancer** for multiple backend instances
6. **CDN** for frontend assets

For most use cases, current implementation handles:
- ~10 concurrent debates
- ~100 decisions in history
- ~5 models per debate
- Response times under 30 seconds

## Testing Strategy

### Manual Testing
- Try different model combinations
- Test with unavailable models
- Interrupt network mid-stream
- Rapid successive debates
- Long queries (1000+ words)

### Automated Testing (Future)
- Unit tests for synthesis parsing
- Integration tests for orchestration
- E2E tests with mock LiteLLM responses
- Load testing with concurrent debates

## Code Organization Principles

### Backend
- **Separation of concerns**: API routes, business logic, data access
- **Dependency injection**: Services initialized in routes
- **Type hints**: Pydantic models for validation
- **Async throughout**: No blocking operations

### Frontend
- **Custom hooks**: Reusable stateful logic
- **Presentational components**: Pure UI components
- **Container pattern**: App.jsx orchestrates data flow
- **CSS utility classes**: TailwindCSS for consistency

## Extension Points

### Adding New Features

**Custom Debate Formats**
- Modify `synthesis.py:_build_synthesis_prompt()`
- Add prompt templates
- Create debate format selector in UI

**Model Roles (DxO Framework)**
- Add `role` field to Response model
- Extend council member selection with role assignment
- Customize prompts based on role

**Export Functionality**
- Add route in `api/history.py`
- Implement formatters (JSON, MD, PDF)
- Add download button in HistoryBrowser

**Semantic Analysis**
- Use embedding models for similarity
- Cluster similar responses
- Detect actual consensus vs keyword overlap

## Known Limitations

### Current Version
1. **No authentication** - single user only
2. **No model cost tracking** - just token counts
3. **Simple consensus detection** - relies on chairman parsing
4. **No debate interruption** - can't cancel mid-stream
5. **Limited history UI** - no search, filter, or pagination
6. **No export** - can only view in browser

### Technical Debt
- No automated tests
- Console logging instead of proper logger
- Hard-coded timeouts
- No retry logic for failed models
- Frontend error boundaries not implemented

## Debugging Tips

### Backend
```bash
# Watch database changes
sqlite3 backend/database.db "SELECT * FROM decisions;"

# Test LiteLLM connection
curl https://litellm.home.jeans.family/models

# Monitor logs
tail -f backend/logs.txt  # if logging to file
```

### Frontend
```javascript
// In browser console
localStorage.setItem('debug', 'true')

// Watch SSE events
const evtSource = new EventSource('/api/council/debate')
evtSource.onmessage = e => console.log(e)
```

### Network
```bash
# Test SSE endpoint
curl -N -H "Accept: text/event-stream" \
  -X POST http://localhost:8000/api/council/debate \
  -d '{"query":"test","council_members":["model1","model2"],"chairman":"model1"}'
```

## Contribution Guidelines

### Code Style
- **Python**: Black formatter, 100 char line length
- **JavaScript**: Prettier with default settings
- **Commits**: Conventional commits (feat:, fix:, docs:)

### Pull Request Process
1. Create feature branch
2. Implement changes
3. Update documentation
4. Test manually
5. Submit PR with description

## License & Attribution

This implementation is based on the Multi-Model AI Decision Framework specification, inspired by Satya Nadella's demonstration of collaborative AI decision-making.

Built with:
- FastAPI (MIT)
- React (MIT)
- SQLAlchemy (MIT)
- TailwindCSS (MIT)
- All other dependencies as per their licenses

---

**Version**: 1.0.0 (Phase 1 Complete)
**Last Updated**: 2025-12-13
**Status**: Production Ready for Local Use
