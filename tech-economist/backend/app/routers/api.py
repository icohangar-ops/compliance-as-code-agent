from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EnterpriseConfig, UsageEvent, Workflow
from app.schemas import (
    CostEstimateRequest,
    CostEstimateResponse,
    DashboardSummary,
    EnterpriseConfigOut,
    EnterpriseConfigUpdate,
    ForecastPoint,
    MonthlyTrend,
    RoiScenarioRequest,
    RoiScenarioResponse,
    SessionCostSummary,
    UsageEventCreate,
    UsageEventOut,
    UsageIngestRequest,
    UsageIngestResponse,
    WorkflowCreate,
    WorkflowEconomics,
    WorkflowOut,
)
from app.services.analytics import (
    generate_forecast,
    get_dashboard_summary,
    get_monthly_trends,
    get_workflow_economics,
    refresh_monthly_snapshot,
    run_roi_scenario,
)
from app.services.benchmarks import get_benchmarks, get_finops_principles, get_market_signals
from app.services.tokencost_service import estimate_cost
from app.services.usage_ingest import ingest_usage, session_cost_summary

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)


@router.get("/workflows", response_model=list[WorkflowOut])
def list_workflows(db: Session = Depends(get_db)):
    return db.query(Workflow).order_by(Workflow.name).all()


@router.post("/workflows", response_model=WorkflowOut)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    wf = Workflow(**payload.model_dump())
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return wf


@router.get("/workflows/economics", response_model=list[WorkflowEconomics])
def workflow_economics(db: Session = Depends(get_db)):
    return get_workflow_economics(db)


@router.post("/cost-estimate", response_model=CostEstimateResponse)
def cost_estimate(payload: CostEstimateRequest):
    try:
        result = estimate_cost(payload.model, payload.prompt, payload.completion)
        return CostEstimateResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/usage-events", response_model=list[UsageEventOut])
def list_usage_events(limit: int = 100, db: Session = Depends(get_db)):
    events = (
        db.query(UsageEvent)
        .order_by(UsageEvent.recorded_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for e in events:
        item = UsageEventOut.model_validate(e)
        item.workflow_name = e.workflow.name if e.workflow else None
        item.roi_multiple = round(e.revenue_lift_usd / e.total_cost_usd, 2) if e.total_cost_usd and e.successful else None
        out.append(item)
    return out


@router.post("/usage-events", response_model=UsageEventOut)
def record_usage_event(payload: UsageEventCreate, db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(Workflow.id == payload.workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    costs = estimate_cost(payload.model, payload.prompt, payload.completion)
    event = UsageEvent(
        workflow_id=payload.workflow_id,
        model=payload.model,
        prompt_tokens=costs["prompt_tokens"],
        completion_tokens=costs["completion_tokens"],
        cached_tokens=payload.cached_tokens,
        prompt_cost_usd=costs["prompt_cost_usd"],
        completion_cost_usd=costs["completion_cost_usd"],
        total_cost_usd=costs["total_cost_usd"],
        successful=payload.successful,
        revenue_lift_usd=payload.revenue_lift_usd,
        hours_saved=payload.hours_saved,
        user_id=payload.user_id,
        notes=payload.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    month = event.recorded_at.strftime("%Y-%m")
    refresh_monthly_snapshot(db, month)

    out = UsageEventOut.model_validate(event)
    out.workflow_name = wf.name
    out.roi_multiple = round(event.revenue_lift_usd / event.total_cost_usd, 2) if event.total_cost_usd and event.successful else None
    return out


@router.post("/usage-ingest", response_model=UsageIngestResponse)
def usage_ingest(payload: UsageIngestRequest, db: Session = Depends(get_db)):
    if payload.workflow_id is not None:
        wf = db.query(Workflow).filter(Workflow.id == payload.workflow_id).first()
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")

    record, priced = ingest_usage(
        db,
        session_id=payload.session_id,
        source=payload.source,
        model=payload.model,
        provider=payload.provider,
        usage=payload.usage,
        workflow_id=payload.workflow_id,
        agent_id=payload.agent_id,
        tool_call_id=payload.tool_call_id,
    )
    return UsageIngestResponse(
        id=record.id,
        session_id=record.session_id,
        source=record.source,
        model=record.model,
        provider=record.provider,
        total_cost_usd=record.total_cost_usd,
        cost_breakdown=priced.to_dict(),
        recorded_at=record.recorded_at,
    )


@router.get("/sessions/{session_id}/cost", response_model=SessionCostSummary)
def session_cost(session_id: str, db: Session = Depends(get_db)):
    summary = session_cost_summary(db, session_id)
    return SessionCostSummary(**summary)


@router.get("/trends", response_model=list[MonthlyTrend])
def trends(db: Session = Depends(get_db)):
    return get_monthly_trends(db)


@router.get("/forecast", response_model=list[ForecastPoint])
def forecast(months: int = 6, db: Session = Depends(get_db)):
    return generate_forecast(db, months)


@router.post("/roi-scenario", response_model=RoiScenarioResponse)
def roi_scenario(payload: RoiScenarioRequest):
    return run_roi_scenario(payload)


@router.get("/benchmarks")
def benchmarks():
    return {
        "workflows": get_benchmarks(),
        "principles": get_finops_principles(),
        "market_signals": get_market_signals(),
    }


@router.get("/config", response_model=EnterpriseConfigOut)
def get_config(db: Session = Depends(get_db)):
    config = db.query(EnterpriseConfig).first()
    if not config:
        config = EnterpriseConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.put("/config", response_model=EnterpriseConfigOut)
def update_config(payload: EnterpriseConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(EnterpriseConfig).first()
    if not config:
        config = EnterpriseConfig()
        db.add(config)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config
