from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

from models.schemas import ModelInfo, ServerGroup, SelectionAnalysis
from services.litellm_client import LiteLLMClient
from services.model_processor import process_models_with_health, analyze_selection

router = APIRouter(prefix="/api/config", tags=["config"])

# Global cache for server groups (refresh periodically)
_server_groups_cache = None


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
    global _server_groups_cache

    # Use cache if available (TODO: add expiration logic)
    if _server_groups_cache is not None:
        return _server_groups_cache

    client = LiteLLMClient()
    raw_data = await client.get_model_info()

    server_groups = await process_models_with_health(raw_data)
    _server_groups_cache = server_groups

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
