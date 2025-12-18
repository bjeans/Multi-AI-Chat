"""
Model processing service for organizing and analyzing LiteLLM models
"""
import re
from typing import Dict, List, Tuple
from datetime import datetime

from models.schemas import (
    ModelInfoDetailed,
    ModelHealth,
    ModelSize,
    OllamaServerInfo,
    ServerGroup,
    SelectionWarning,
    SelectionRecommendation,
    SelectionAnalysis,
)
from services.litellm_client import LiteLLMClient


def parse_model_name(model_name: str, litellm_model: str) -> Dict[str, any]:
    """
    Parse model_name and litellm_params.model to extract metadata

    Examples:
    - model_name="gpt-oss:latest", litellm_model="ollama_chat/gpt-oss:20b"
      → base="gpt-oss", tag="latest", actual_tag="20b", is_latest=True

    - model_name="llama3.2:3b", litellm_model="ollama_chat/llama3.2:3b"
      → base="llama3.2", tag="3b", actual_tag="3b", is_latest=False
    """
    # Split model_name on ":"
    parts = model_name.split(":")
    base = parts[0]
    tag = parts[1] if len(parts) > 1 else None

    # Extract actual tag from litellm_model
    # "ollama_chat/gpt-oss:20b" → "20b"
    litellm_parts = litellm_model.split("/")[-1].split(":")
    actual_tag = litellm_parts[1] if len(litellm_parts) > 1 else None

    return {
        "base_model": base,
        "tag": tag,
        "actual_tag": actual_tag,
        "is_latest_alias": tag == "latest",
        "display_name": model_name
    }


def parse_model_size(model_name: str, litellm_model: str) -> ModelSize:
    """
    Extract model size from name

    Examples:
    - llama3.3:70b → 70B
    - deepseek-r1:32b → 32B
    - llama3.2:3b → 3B
    - tinyllama:1.1b → 1.1B
    """
    # Try to find pattern like "70b", "32b", "3b", "1.1b"
    patterns = [model_name, litellm_model]
    for pattern in patterns:
        match = re.search(r'(\d+\.?\d*)b', pattern.lower())
        if match:
            size_b = float(match.group(1))

            # Determine tier
            if size_b < 2:
                tier = "tiny"
            elif size_b < 10:
                tier = "small"
            elif size_b < 30:
                tier = "medium"
            else:
                tier = "large"

            # Estimate memory (rough approximation)
            # Rule of thumb: ~1.2-1.5 GB per billion parameters for float16
            memory_gb = int(size_b * 1.5)

            return ModelSize(
                parameters=f"{size_b}B",
                parameters_billions=size_b,
                estimated_memory_gb=memory_gb,
                size_tier=tier
            )

    # Default if size not found in name
    return ModelSize(
        parameters="Unknown",
        parameters_billions=0,
        estimated_memory_gb=4,
        size_tier="small"
    )


def infer_provider(model_name: str) -> str:
    """Infer provider from model name"""
    lower = model_name.lower()

    if "llama" in lower:
        return "Meta"
    elif "mistral" in lower or "codestral" in lower:
        return "Mistral AI"
    elif "gemma" in lower or "codegemma" in lower:
        return "Google"
    elif "deepseek" in lower:
        return "DeepSeek"
    elif "qwen" in lower:
        return "Alibaba (Qwen)"
    elif "phi" in lower:
        return "Microsoft"
    elif "granite" in lower:
        return "IBM"
    elif "gpt-oss" in lower:
        return "GPT-OSS"
    else:
        return "Other"


def infer_category(model_name: str) -> str:
    """Infer model category from name"""
    lower = model_name.lower()

    if "coder" in lower or "code" in lower:
        return "code"
    elif "vision" in lower:
        return "vision"
    elif "r1" in lower or "reasoning" in lower:
        return "reasoning"
    else:
        return "chat"


def get_performance_tier(tpm: int) -> str:
    """Determine performance tier based on TPM"""
    if tpm >= 50000:
        return "high"
    elif tpm >= 20000:
        return "medium"
    else:
        return "low"


async def process_models_with_health(raw_data: dict) -> List[ServerGroup]:
    """
    Process models with health checks and group by server
    """
    client = LiteLLMClient()

    # Fetch health data
    health_data = await client.get_health_status()
    health_map = health_data.get("latest_health_checks", {})

    # Step 1: Group models by server
    server_map = {}  # Key: api_base, Value: {server_info, models}

    for item in raw_data["data"]:
        model_name = item["model_name"]
        litellm_params = item["litellm_params"]
        api_base = litellm_params["api_base"]

        # Initialize server if first time seeing it
        if api_base not in server_map:
            host = api_base.split("//")[1].split(":")[0]
            server_map[api_base] = {
                "server_info": OllamaServerInfo(
                    api_base=api_base,
                    host=host,
                    tpm=litellm_params.get("tpm", 0),
                    rpm=litellm_params.get("rpm", 0),
                    performance_tier=get_performance_tier(litellm_params.get("tpm", 0)),
                    health_status="unknown",
                    model_count=0
                ),
                "models": []
            }

        # Parse model info
        parsed = parse_model_name(model_name, litellm_params["model"])
        size = parse_model_size(model_name, litellm_params["model"])

        # Get health info for this model
        health = None
        if model_name in health_map:
            h = health_map[model_name]
            health = ModelHealth(
                status=h.get("status", "unknown"),
                healthy_count=h.get("healthy_count", 0),
                unhealthy_count=h.get("unhealthy_count", 0),
                response_time_ms=h.get("response_time_ms", 0),
                last_checked=h.get("checked_at"),
                error_message=h.get("error_message")
            )

        # Extract host from api_base
        host = api_base.split("//")[1].split(":")[0]

        # Infer model family from base_model
        base_parts = parsed["base_model"].split(".")[0].split("-")[0]
        model_family = base_parts.capitalize()

        # Create model info
        model = ModelInfoDetailed(
            id=f"{model_name}_{host}",
            display_name=model_name,
            base_model=parsed["base_model"],
            actual_tag=parsed["actual_tag"],
            is_latest_alias=parsed["is_latest_alias"],
            resolves_to=f"{parsed['base_model']}:{parsed['actual_tag']}" if parsed["is_latest_alias"] and parsed["actual_tag"] else None,
            api_base=api_base,
            server_host=host,
            server_tpm=litellm_params.get("tpm", 0),
            server_rpm=litellm_params.get("rpm", 0),
            provider=infer_provider(parsed["base_model"]),
            model_family=model_family,
            model_category=infer_category(model_name),
            size=size,
            health=health,
            max_tokens=litellm_params.get("max_tokens", 4096),
            supports_function_calling=litellm_params.get("supports_function_calling", False)
        )

        server_map[api_base]["models"].append(model)
        server_map[api_base]["server_info"].model_count += 1

    # Step 2: Detect duplicates and find better servers
    all_models = []
    for server_data in server_map.values():
        all_models.extend(server_data["models"])

    # Group by base_model:actual_tag to find duplicates
    model_groups = {}
    for model in all_models:
        key = f"{model.base_model}:{model.actual_tag}"
        if key not in model_groups:
            model_groups[key] = []
        model_groups[key].append(model)

    # Mark duplicates and set better_server
    for key, models in model_groups.items():
        if len(models) > 1:
            # Sort by TPM (descending) to find best server
            models_sorted = sorted(
                models,
                key=lambda m: m.server_tpm,
                reverse=True
            )
            best_server = models_sorted[0].api_base

            for model in models:
                model.is_duplicate = True
                model.duplicate_count = len(models)
                if model.api_base != best_server:
                    model.better_server = best_server

    # Step 3: Create ServerGroup list
    result = []
    for api_base in sorted(server_map.keys()):
        server_data = server_map[api_base]
        models = sorted(server_data["models"], key=lambda m: m.display_name.lower())

        result.append(ServerGroup(
            server=server_data["server_info"],
            models=models,
            warnings=[],
            recommendations=[]
        ))

    return result


async def analyze_selection(selected_model_ids: List[str], all_server_groups: List[ServerGroup]) -> SelectionAnalysis:
    """
    Analyze selected models for resource conflicts

    Returns warnings and recommendations
    """
    # Build a map of model_id -> model
    model_map = {}
    for group in all_server_groups:
        for model in group.models:
            model_map[model.id] = model

    # Get selected models
    selected_models = [model_map.get(mid) for mid in selected_model_ids if mid in model_map]
    selected_models = [m for m in selected_models if m is not None]

    # Group by server
    by_server = {}
    for model in selected_models:
        if model.api_base not in by_server:
            by_server[model.api_base] = []
        by_server[model.api_base].append(model)

    warnings = []
    recommendations = []

    # Check each server for resource conflicts
    for api_base, server_models in by_server.items():
        total_memory = sum(m.size.estimated_memory_gb for m in server_models)
        large_models = [m for m in server_models if m.size.size_tier == "large"]
        medium_models = [m for m in server_models if m.size.size_tier == "medium"]

        # Warning: Multiple large models on same server
        if len(large_models) > 1:
            warnings.append(SelectionWarning(
                severity="high",
                server=api_base,
                message=f"⚠️ {len(large_models)} large models selected on {api_base.split('//')[1]}. Expect significant delays during model swapping.",
                models=[m.display_name for m in large_models],
                estimated_total_memory=f"{total_memory}GB"
            ))

            # Recommend moving one to another server
            for model in large_models[1:]:  # Skip first one
                if model.is_duplicate and model.better_server:
                    recommendations.append(SelectionRecommendation(
                        type="move_to_better_server",
                        model=model.display_name,
                        from_server=api_base,
                        to_server=model.better_server,
                        reason="Higher TPM and avoids memory contention"
                    ))

        # Warning: Large + medium models
        if len(large_models) >= 1 and len(medium_models) >= 1:
            warnings.append(SelectionWarning(
                severity="medium",
                server=api_base,
                message=f"⚠️ Large model + medium model on {api_base.split('//')[1]}. May cause delays.",
                estimated_total_memory=f"{total_memory}GB"
            ))

        # Info: High memory usage
        if total_memory > 50:
            warnings.append(SelectionWarning(
                severity="info",
                server=api_base,
                message=f"ℹ️ Selected models require ~{total_memory}GB on {api_base.split('//')[1]}"
            ))

    # Calculate diversity score
    providers = set(m.provider for m in selected_models)
    categories = set(m.model_category for m in selected_models)
    unique_base_models = set(m.base_model for m in selected_models)

    diversity_score = calculate_diversity_score(len(providers), len(categories), len(unique_base_models))

    return SelectionAnalysis(
        warnings=warnings,
        recommendations=recommendations,
        total_models_selected=len(selected_models),
        servers_used=len(by_server),
        diversity_score=diversity_score
    )


def calculate_diversity_score(providers: int, categories: int, unique_models: int) -> int:
    """Calculate diversity score (0-100)"""
    score = 0

    if providers >= 3:
        score += 40
    elif providers >= 2:
        score += 25

    if categories >= 2:
        score += 30

    if unique_models >= 3:
        score += 30
    elif unique_models >= 2:
        score += 15

    return min(score, 100)
