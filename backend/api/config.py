from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel
import asyncio
import time
import os
import logging

from models.schemas import ModelInfo, ServerGroup, SelectionAnalysis
from services.litellm_client import LiteLLMClient
from services.model_processor import process_models_with_health, analyze_selection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])

# Global cache for server groups with expiration
_server_groups_cache: Optional[List[ServerGroup]] = None
_cache_timestamp: Optional[float] = None
_cache_lock = asyncio.Lock()

# Parse cache TTL with error handling
def _get_cache_ttl() -> int:
    """Get cache TTL from environment with validation"""
    default_ttl = 120
    try:
        ttl_str = os.getenv("CACHE_TTL_SECONDS", str(default_ttl))
        ttl = int(ttl_str)
        if ttl <= 0:
            logger.warning(f"Invalid CACHE_TTL_SECONDS={ttl_str} (must be > 0), using default {default_ttl}")
            return default_ttl
        return ttl
    except ValueError:
        logger.warning(f"Invalid CACHE_TTL_SECONDS={os.getenv('CACHE_TTL_SECONDS')} (must be integer), using default {default_ttl}")
        return default_ttl

CACHE_TTL_SECONDS = _get_cache_ttl()


class TestModelRequest(BaseModel):
    model_id: str


class TestModelResponse(BaseModel):
    model_id: str
    available: bool


@router.get("/models", response_model=List[ModelInfo])
async def get_models():
    """
    Get list of available models from LiteLLM proxy
    """
    client = LiteLLMClient()
    models = await client.get_available_models()
    return models


@router.post("/test-model", response_model=TestModelResponse)
async def test_model(request: TestModelRequest):
    """
    Test if a specific model is available and responding
    """
    client = LiteLLMClient()
    available = await client.test_model(request.model_id)

    return TestModelResponse(
        model_id=request.model_id,
        available=available,
    )


@router.get("/models/by-server", response_model=List[ServerGroup])
async def get_models_by_server():
    """
    Get models grouped by Ollama server with health status and size info
    """
    global _server_groups_cache, _cache_timestamp

    # Use lock to prevent race conditions on cache access
    async with _cache_lock:
        now = time.time()

        # Return cached data if valid and not expired
        if _server_groups_cache is not None and _cache_timestamp is not None:
            if now - _cache_timestamp < CACHE_TTL_SECONDS:
                return _server_groups_cache

        # Fetch fresh data
        client = LiteLLMClient()
        raw_data = await client.get_model_info()

        server_groups = await process_models_with_health(raw_data)

        # Update cache with timestamp
        _server_groups_cache = server_groups
        _cache_timestamp = now

        return server_groups


class AnalyzeSelectionRequest(BaseModel):
    model_ids: List[str]


@router.post("/models/analyze-selection", response_model=SelectionAnalysis)
async def analyze_model_selection(request: AnalyzeSelectionRequest):
    """
    Analyze selected models for resource conflicts and provide recommendations
    """
    # Get current server groups
    server_groups = await get_models_by_server()

    # Analyze selection
    analysis = await analyze_selection(request.model_ids, server_groups)

    return analysis
