from fastapi import APIRouter, HTTPException
from typing import List
from sqlalchemy import func, select

from models.schemas import DecisionSchema, DecisionListItem
from models.database import Decision, Response
from services.db import DecisionService, get_db

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/", response_model=List[DecisionListItem])
async def list_decisions(skip: int = 0, limit: int = 50):
    """
    List all decisions with pagination
    Returns summary information for each decision
    """
    async with get_db() as db:
        decisions = await DecisionService.list_decisions(db, skip, limit)

        # Build response with response counts
        result = []
        for decision in decisions:
            # Count responses for this decision
            count_result = await db.execute(
                select(func.count(Response.id)).where(Response.decision_id == decision.id)
            )
            response_count = count_result.scalar_one()

            result.append(
                DecisionListItem(
                    id=decision.id,
                    query=decision.query,
                    chairman_model=decision.chairman_model,
                    created_at=decision.created_at,
                    response_count=response_count,
                )
            )

        return result


@router.get("/{decision_id}", response_model=DecisionSchema)
async def get_decision(decision_id: int):
    """
    Get full decision details including all responses and synthesis
    """
    async with get_db() as db:
        decision = await DecisionService.get_decision(db, decision_id)

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        return decision
