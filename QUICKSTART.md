# LLM Council - Quick Start Guide

## System Ready Status ✅

All components have been implemented and are ready to use:
- ✅ Backend FastAPI server with SSE streaming
- ✅ Frontend React application with real-time UI
- ✅ LiteLLM proxy integration
- ✅ Database schema and operations
- ✅ Council orchestration with concurrent model calls
- ✅ Chairman synthesis logic
- ✅ Decision history browser

## Prerequisites Checklist

Before starting, ensure you have:
- [x] Python 3.10+ installed
- [x] Node.js 18+ installed
- [x] LiteLLM proxy running (default: `http://localhost:4000`)
- [ ] At least 2 models available in your LiteLLM proxy

## Quick Start (First Time Setup)

### Option 1: Using the Setup Scripts (Recommended)

```bash
# Setup backend (creates venv and installs dependencies)
./setup-backend.sh

# Setup frontend (installs npm dependencies)
./setup-frontend.sh
```

### Option 2: Manual Setup

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

#### Frontend
```bash
cd frontend
npm install
cd ..
```

## Running the Application

You'll need two terminal windows:

### Terminal 1: Start Backend
```bash
./start-backend.sh
```

This will:
- Activate the Python virtual environment
- Start FastAPI server on `http://localhost:8000`
- Initialize the SQLite database
- Connect to your LiteLLM proxy

You should see:
```
Database initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Start Frontend
```bash
./start-frontend.sh
```

This will:
- Start Vite dev server on `http://localhost:5173`
- Enable hot-reload for development

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Using the Application

1. **Open your browser** to `http://localhost:5173`

2. **Check Available Models**
   - The app will automatically fetch models from your LiteLLM proxy
   - If no models appear, check that your proxy is running

3. **Create Your First Debate**
   - Enter a question (e.g., "What are the pros and cons of microservices architecture?")
   - Select at least 2 models as council members
   - Designate one model as chairman
   - Click "Start Debate"

4. **Watch the Magic**
   - Responses stream in real-time from each model
   - See token counts and response times
   - Wait for the synthesis to appear

5. **Review Synthesis**
   - View consensus points (where models agree)
   - See debates (where models disagree)
   - Read chairman's final synthesis

6. **Browse History**
   - Click "Show History" to see past decisions
   - Click any decision to view details

## Troubleshooting

### Backend Issues

**Problem**: `Module not found` errors
```bash
# Ensure you're in the venv
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: Can't connect to LiteLLM proxy
- Check that your LiteLLM proxy is running and accessible
- Verify the URL in `backend/.env` (default: `http://localhost:4000`)
- Test with: `curl http://localhost:4000/models`

**Problem**: Database errors
```bash
# Delete and reinitialize database
cd backend
rm -f database.db
# Restart backend - it will recreate the database
```

### Frontend Issues

**Problem**: `npm install` fails
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Problem**: Can't connect to backend
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify proxy configuration in `frontend/vite.config.js`

**Problem**: No models showing
- Check browser console for API errors
- Verify LiteLLM proxy is returning models
- Test: `curl http://localhost:8000/api/config/models`

## API Testing

Test the backend directly:

```bash
# Get available models
curl http://localhost:8000/api/config/models

# Start a debate (requires SSE client)
curl -X POST http://localhost:8000/api/council/debate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the meaning of life?",
    "council_members": ["gpt-4", "claude-3-opus"],
    "chairman": "claude-3-opus"
  }'

# Get decision history
curl http://localhost:8000/api/history/

# Get specific decision
curl http://localhost:8000/api/history/1
```

## Development Tips

### Backend Development
- SQLAlchemy echo is enabled (see SQL queries in console)
- Edit files and server auto-reloads (thanks to uvicorn --reload)
- Database is in `backend/database.db` (SQLite)

### Frontend Development
- Vite hot-reload is enabled
- Check browser console for React errors
- TailwindCSS classes apply instantly

## Next Steps

### Try Different Scenarios
1. **Technical Decisions**: "Should we use REST or GraphQL?"
2. **Business Decisions**: "Should we expand to European markets?"
3. **Creative Brainstorming**: "Ideas for a new mobile app feature"
4. **Analysis**: "Compare Python vs Rust for backend development"

### Experiment with Models
- Try different combinations of models
- Compare local vs cloud models
- Test with 2, 3, 4+ council members
- Rotate which model acts as chairman

### Monitor Performance
- Check response times for each model
- Compare token usage
- Observe consensus patterns

## Configuration

### Environment Variables

Backend `.env` (configure with your settings):
```
LITELLM_PROXY_URL=http://localhost:4000
LITELLM_API_KEY=your-api-key-here
DATABASE_URL=sqlite+aiosqlite:///./database.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Customization Ideas
- Adjust temperature in `backend/services/litellm_client.py`
- Modify synthesis prompt in `backend/services/synthesis.py`
- Change UI theme in `frontend/src/styles/index.css`
- Add more debate formats or prompts

## File Structure Reference

```
Multi-AI-Chat/
├── backend/
│   ├── venv/                  # Python virtual environment
│   ├── api/                   # API endpoints
│   ├── models/                # Database models
│   ├── services/              # Business logic
│   ├── main.py               # FastAPI app entry point
│   ├── .env                  # Environment config
│   └── database.db           # SQLite database (created on first run)
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/           # Custom React hooks
│   │   └── styles/          # TailwindCSS styles
│   ├── node_modules/        # npm dependencies
│   └── package.json
├── setup-backend.sh         # Backend setup script
├── setup-frontend.sh        # Frontend setup script
├── start-backend.sh         # Backend startup script
├── start-frontend.sh        # Frontend startup script
└── README.md                # Full documentation
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review console/terminal logs for errors
3. Ensure all prerequisites are met
4. Verify LiteLLM proxy is accessible

## What's Next (Future Phases)

Phase 1 (Current) is complete with:
- ✅ Multi-model council debates
- ✅ Real-time streaming
- ✅ Chairman synthesis
- ✅ Decision history

Future enhancements:
- 🔜 DxO framework (role assignments)
- 🔜 Export to JSON/Markdown/PDF
- 🔜 Custom prompt templates
- 🔜 Semantic analysis for consensus
- 🔜 Model weighting and confidence scores
- 🔜 User authentication
- 🔜 Docker deployment

Enjoy your LLM Council! 🎉
