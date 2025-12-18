from fastapi import APIRouter
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from models.schemas import ModelInfo
from services.litellm_client import LiteLLMClient

router = APIRouter(prefix="/api/config", tags=["config"])


class TestModelRequest(BaseModel):
    model_id: str


class TestModelResponse(BaseModel):
    model_id: str
    available: bool


class MCPToolInfo(BaseModel):
    name: str
    description: str
    server_label: str
    input_schema: Optional[Dict[str, Any]] = None


@router.get("/models", response_model=List[ModelInfo])
async def get_models():
    """
    Get list of available models from LiteLLM proxy
    """
    client = LiteLLMClient()
    models = await client.get_available_models()
    return models


@router.get("/mcp-tools", response_model=List[MCPToolInfo])
async def get_mcp_tools():
    """
    Get list of available MCP tools from LiteLLM proxy
    """
    client = LiteLLMClient()
    tools = await client.get_mcp_tools()
    return [tool.to_dict() for tool in tools]


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
