from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EnterpriseConfig(Base):
    __tablename__ = "enterprise_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(200), default="Enterprise")
    shares_outstanding_millions: Mapped[float] = mapped_column(Float, default=3000.0)
    earnings_per_share: Mapped[float] = mapped_column(Float, default=7.0)
    annual_tech_investment_billions: Mapped[float] = mapped_column(Float, default=3.0)
    annual_revenue_billions: Mapped[float] = mapped_column(Float, default=50.0)
    ai_compute_budget_millions: Mapped[float] = mapped_column(Float, default=120.0)
    retry_overhead_multiplier: Mapped[float] = mapped_column(Float, default=1.85)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    department: Mapped[str] = mapped_column(String(120), default="Engineering")
    description: Mapped[Optional[str]] = mapped_column(Text)
    default_model: Mapped[str] = mapped_column(String(120), default="gpt-4o-mini")
    manual_baseline_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    expected_value_per_success_usd: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_roi_median: Mapped[Optional[float]] = mapped_column(Float)
    benchmark_cost_per_task_usd: Mapped[Optional[float]] = mapped_column(Float)
    is_strategic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events: Mapped[List["UsageEvent"]] = relationship(back_populates="workflow")


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0)
    prompt_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    completion_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    successful: Mapped[bool] = mapped_column(Boolean, default=True)
    revenue_lift_usd: Mapped[float] = mapped_column(Float, default=0.0)
    hours_saved: Mapped[float] = mapped_column(Float, default=0.0)
    user_id: Mapped[Optional[str]] = mapped_column(String(120))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow: Mapped["Workflow"] = relationship(back_populates="events")


class MonthlySnapshot(Base):
    __tablename__ = "monthly_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[str] = mapped_column(String(7), unique=True, nullable=False)
    total_spend_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_revenue_lift_usd: Mapped[float] = mapped_column(Float, default=0.0)
    successful_tasks: Mapped[int] = mapped_column(Integer, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    cost_per_successful_task_usd: Mapped[float] = mapped_column(Float, default=0.0)
    portfolio_roi: Mapped[float] = mapped_column(Float, default=0.0)
    token_volume_millions: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UsageIngestRecord(Base):
    """Harness-level canonical usage (Ken Huang Cost & Token-Usage Accounting)."""

    __tablename__ = "usage_ingest_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    workflow_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workflows.id"), nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(120))
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(120))
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="canonical")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_creation_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    web_search_requests: Mapped[int] = mapped_column(Integer, default=0)
    input_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    output_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cache_read_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cache_write_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    web_search_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
