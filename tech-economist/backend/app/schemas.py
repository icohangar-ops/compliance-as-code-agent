from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class EnterpriseConfigOut(BaseModel):
    company_name: str
    shares_outstanding_millions: float
    earnings_per_share: float
    annual_tech_investment_billions: float
    annual_revenue_billions: float
    ai_compute_budget_millions: float
    retry_overhead_multiplier: float

    model_config = {"from_attributes": True}


class EnterpriseConfigUpdate(BaseModel):
    company_name: Optional[str] = None
    shares_outstanding_millions: Optional[float] = None
    earnings_per_share: Optional[float] = None
    annual_tech_investment_billions: Optional[float] = None
    annual_revenue_billions: Optional[float] = None
    ai_compute_budget_millions: Optional[float] = None
    retry_overhead_multiplier: Optional[float] = None


class WorkflowCreate(BaseModel):
    name: str
    category: str
    department: str = "Engineering"
    description: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    manual_baseline_cost_usd: float = 0.0
    expected_value_per_success_usd: float = 0.0
    is_strategic: bool = False


class WorkflowOut(BaseModel):
    id: int
    name: str
    category: str
    department: str
    description: Optional[str]
    default_model: str
    manual_baseline_cost_usd: float
    expected_value_per_success_usd: float
    benchmark_roi_median: Optional[float]
    benchmark_cost_per_task_usd: Optional[float]
    is_strategic: bool

    model_config = {"from_attributes": True}


class CostEstimateRequest(BaseModel):
    model: str
    prompt: Union[str, List[Dict]]
    completion: str = ""
    cached_tokens: int = 0


class CostEstimateResponse(BaseModel):
    model: str
    prompt_tokens: int
    completion_tokens: int
    prompt_cost_usd: float
    completion_cost_usd: float
    total_cost_usd: float
    cost_per_1m_tokens_usd: Optional[float] = None


class UsageEventCreate(BaseModel):
    workflow_id: int
    model: str
    prompt: Union[str, List[Dict]]
    completion: str = ""
    cached_tokens: int = 0
    successful: bool = True
    revenue_lift_usd: float = 0.0
    hours_saved: float = 0.0
    user_id: Optional[str] = None
    notes: Optional[str] = None


class UsageEventOut(BaseModel):
    id: int
    workflow_id: int
    workflow_name: Optional[str] = None
    model: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    prompt_cost_usd: float
    completion_cost_usd: float
    total_cost_usd: float
    successful: bool
    revenue_lift_usd: float
    hours_saved: float
    user_id: Optional[str]
    notes: Optional[str]
    recorded_at: datetime
    roi_multiple: Optional[float] = None

    model_config = {"from_attributes": True}


class BenchmarkWorkflow(BaseModel):
    name: str
    category: str
    median_cost_usd: float
    median_roi: float
    source: str
    insight: str


class DashboardSummary(BaseModel):
    total_spend_mtd_usd: float
    total_spend_ytd_usd: float
    portfolio_roi: float
    cost_per_successful_task_usd: float
    successful_tasks_mtd: int
    failed_tasks_mtd: int
    success_rate_pct: float
    ai_budget_utilization_pct: float
    revenue_lift_mtd_usd: float
    net_value_mtd_usd: float
    eps_impact_per_share_usd: float
    eps_at_risk_pct: float
    projected_annual_spend_millions: float
    benchmark_median_roi: float
    workflows_underwater: int
    workflows_high_leverage: int


class WorkflowEconomics(BaseModel):
    workflow: WorkflowOut
    total_spend_usd: float
    total_revenue_lift_usd: float
    successful_runs: int
    failed_runs: int
    cost_per_successful_task_usd: float
    roi_multiple: float
    vs_benchmark_roi: Optional[float]
    status: str


class MonthlyTrend(BaseModel):
    month: str
    total_spend_usd: float
    total_revenue_lift_usd: float
    portfolio_roi: float
    cost_per_successful_task_usd: float
    successful_tasks: int
    token_volume_millions: float


class ForecastPoint(BaseModel):
    month: str
    projected_spend_usd: float
    projected_roi: float
    confidence_low_usd: float
    confidence_high_usd: float


class RoiScenarioRequest(BaseModel):
    workflow_name: str
    annual_runs: int = 1000
    success_rate: float = Field(0.85, ge=0, le=1)
    avg_revenue_lift_usd: float = 0.0
    avg_hours_saved: float = 0.0
    hourly_cost_usd: float = 150.0
    model: str = "gpt-4o-mini"
    avg_prompt_tokens: int = 2000
    avg_completion_tokens: int = 800
    manual_baseline_cost_usd: float = 0.0


class RoiScenarioResponse(BaseModel):
    annual_token_cost_usd: float
    annual_value_usd: float
    annual_net_value_usd: float
    roi_multiple: float
    payback_months: Optional[float]
    cost_per_successful_task_usd: float
    recommendation: str
