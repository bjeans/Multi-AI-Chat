from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    chairman_model = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    responses = relationship("Response", back_populates="decision", cascade="all, delete-orphan")
    synthesis = relationship("Synthesis", back_populates="decision", uselist=False, cascade="all, delete-orphan")


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decisions.id"), nullable=False)
    model_name = Column(String, nullable=False)
    response_text = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    response_time = Column(Float, default=0.0)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    decision = relationship("Decision", back_populates="responses")


class Synthesis(Base):
    __tablename__ = "synthesis"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decisions.id"), nullable=False)
    consensus_items = Column(JSON, default=list)  # List of consensus points
    debates = Column(JSON, default=list)  # List of debate points with disagreements
    synthesis_text = Column(Text, nullable=False)  # Chairman's synthesis
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    decision = relationship("Decision", back_populates="synthesis")
