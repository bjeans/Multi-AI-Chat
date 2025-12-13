from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager
from typing import List, Optional
import os
from dotenv import load_dotenv

from models.database import Base, Decision, Response, Synthesis

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DecisionService:
    """Service for managing decisions and their responses"""

    @staticmethod
    async def create_decision(db: AsyncSession, query: str, chairman_model: str) -> Decision:
        """Create a new decision"""
        decision = Decision(query=query, chairman_model=chairman_model)
        db.add(decision)
        await db.flush()
        await db.refresh(decision)
        return decision

    @staticmethod
    async def add_response(
        db: AsyncSession,
        decision_id: int,
        model_name: str,
        response_text: str,
        tokens_used: int,
        response_time: float,
    ) -> Response:
        """Add a response to a decision"""
        response = Response(
            decision_id=decision_id,
            model_name=model_name,
            response_text=response_text,
            tokens_used=tokens_used,
            response_time=response_time,
        )
        db.add(response)
        await db.flush()
        await db.refresh(response)
        return response

    @staticmethod
    async def add_synthesis(
        db: AsyncSession,
        decision_id: int,
        consensus_items: List[str],
        debates: List[dict],
        synthesis_text: str,
    ) -> Synthesis:
        """Add synthesis to a decision"""
        synthesis = Synthesis(
            decision_id=decision_id,
            consensus_items=consensus_items,
            debates=debates,
            synthesis_text=synthesis_text,
        )
        db.add(synthesis)
        await db.flush()
        await db.refresh(synthesis)
        return synthesis

    @staticmethod
    async def get_decision(db: AsyncSession, decision_id: int) -> Optional[Decision]:
        """Get a decision by ID with all related data"""
        result = await db.execute(
            select(Decision)
            .options(selectinload(Decision.responses))
            .options(selectinload(Decision.synthesis))
            .where(Decision.id == decision_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_decisions(db: AsyncSession, skip: int = 0, limit: int = 50) -> List[Decision]:
        """List decisions with pagination"""
        result = await db.execute(
            select(Decision)
            .order_by(Decision.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_decision_count(db: AsyncSession, decision_id: int) -> int:
        """Get response count for a decision"""
        result = await db.execute(
            select(func.count(Response.id)).where(Response.decision_id == decision_id)
        )
        return result.scalar_one()

    @staticmethod
    async def get_responses_for_decision(db: AsyncSession, decision_id: int) -> List[Response]:
        """Get all responses for a decision"""
        result = await db.execute(
            select(Response).where(Response.decision_id == decision_id)
        )
        return result.scalars().all()
