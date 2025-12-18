from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MCPConfig(BaseModel):
    """Configuration for MCP tools usage"""
    enabled: bool = Field(default=False, description="Whether to enable MCP tools")
    server_labels: List[str] = Field(default=[], description="Specific MCP server labels to use (empty = all)")
    allowed_tools: List[str] = Field(default=[], description="Specific tool names to allow (empty = all)")


class CouncilDebateRequest(BaseModel):
    query: str = Field(..., description="The question or decision to debate")
    council_members: List[str] = Field(..., min_length=2, description="List of model IDs to participate")
    chairman: str = Field(..., description="Model ID to act as chairman and synthesize")
    mcp_config: Optional[MCPConfig] = Field(default=None, description="Optional MCP tools configuration")


class ModelInfo(BaseModel):
    id: str
    name: str
    available: bool
    provider: Optional[str] = None


class ResponseSchema(BaseModel):
    id: int
    decision_id: int
    model_name: str
    response_text: str
    tokens_used: int
    response_time: float
    created_at: datetime

    class Config:
        from_attributes = True


class SynthesisSchema(BaseModel):
    id: int
    decision_id: int
    consensus_items: List[str]
    debates: List[dict]
    synthesis_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionSchema(BaseModel):
    id: int
    query: str
    chairman_model: str
    created_at: datetime
    updated_at: datetime
    responses: List[ResponseSchema] = []
    synthesis: Optional[SynthesisSchema] = None

    class Config:
        from_attributes = True


class DecisionListItem(BaseModel):
    id: int
    query: str
    chairman_model: str
    created_at: datetime
    response_count: int

    class Config:
        from_attributes = True
