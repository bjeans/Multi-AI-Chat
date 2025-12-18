from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CouncilDebateRequest(BaseModel):
    query: str = Field(..., description="The question or decision to debate")
    council_members: List[str] = Field(..., min_length=2, description="List of model IDs to participate")
    chairman: str = Field(..., description="Model ID to act as chairman and synthesize")


class ModelInfo(BaseModel):
    id: str
    name: str
    available: bool
    provider: Optional[str] = None


class ModelHealth(BaseModel):
    status: str  # "healthy", "unhealthy", "unknown"
    healthy_count: int
    unhealthy_count: int
    response_time_ms: float
    last_checked: Optional[datetime]
    error_message: Optional[str] = None


class ModelSize(BaseModel):
    parameters: str  # "70B", "32B", "3B", etc.
    parameters_billions: float  # Numeric for sorting
    estimated_memory_gb: int  # Rough estimate for warnings
    size_tier: str  # "tiny" (<2B), "small" (2-10B), "medium" (10-30B), "large" (30B+)


class OllamaServerInfo(BaseModel):
    api_base: str
    host: str
    tpm: int
    rpm: int
    performance_tier: str
    health_status: str = "unknown"
    model_count: int = 0
    selected_model_count: int = 0
    total_selected_memory_gb: int = 0


class ModelInfoDetailed(BaseModel):
    id: str
    display_name: str
    base_model: str
    actual_tag: Optional[str] = None
    is_latest_alias: bool = False
    resolves_to: Optional[str] = None

    # Server information
    api_base: str
    server_host: str
    server_tpm: int
    server_rpm: int

    # Metadata
    provider: str
    model_family: str
    model_category: str

    # Model specs
    size: ModelSize
    health: Optional[ModelHealth] = None
    max_tokens: int = 4096
    supports_function_calling: bool = False

    # Duplication info
    is_duplicate: bool = False
    better_server: Optional[str] = None
    duplicate_count: int = 1


class ServerGroup(BaseModel):
    server: OllamaServerInfo
    models: List[ModelInfoDetailed]
    warnings: List[str] = []
    recommendations: List[str] = []


class SelectionWarning(BaseModel):
    severity: str  # "high", "medium", "info"
    server: str
    message: str
    models: Optional[List[str]] = None
    estimated_total_memory: Optional[str] = None


class SelectionRecommendation(BaseModel):
    type: str
    model: str
    from_server: str
    to_server: str
    reason: str


class SelectionAnalysis(BaseModel):
    warnings: List[SelectionWarning]
    recommendations: List[SelectionRecommendation]
    total_models_selected: int
    servers_used: int
    diversity_score: int


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
