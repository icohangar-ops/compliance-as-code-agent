import random
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import EnterpriseConfig, MonthlySnapshot, UsageEvent, Workflow
from app.services.analytics import refresh_monthly_snapshot
from app.services.benchmarks import INDUSTRY_BENCHMARKS
from app.services.tokencost_service import estimate_cost

DEMO_WORKFLOWS = [
    ("SEO Audit Pipeline", "Marketing", "gpt-4o", 4.20, 48.0, 11.4, True),
    ("Lead Enrichment Agent", "Sales", "gpt-4o-mini", 1.85, 16.5, 8.9, True),
    ("Code Review Assistant", "Engineering", "gpt-4o-mini", 3.40, 19.0, 5.8, True),
    ("Contract Drafting", "Legal", "gpt-4o", 8.50, 12.0, 1.4, False),
    ("Tier-1 Support Triage", "Operations", "gpt-4o-mini", 0.07, 0.15, 2.1, False),
    ("Competitor Analysis", "Strategy", "gpt-4o", 12.40, 40.0, 3.2, True),
    ("Client Report Generator", "Finance", "gpt-4o-mini", 2.30, 3.7, 1.6, False),
    ("Ad Copy Iteration", "Marketing", "gpt-4o-mini", 0.45, 2.0, 4.5, False),
]

MODELS = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022"]


def seed_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Workflow).count() > 0:
            print("Database already seeded.")
            return

        config = EnterpriseConfig(
            company_name="Acme Financial Services",
            shares_outstanding_millions=3000.0,
            earnings_per_share=7.0,
            annual_tech_investment_billions=3.0,
            annual_revenue_billions=50.0,
            ai_compute_budget_millions=120.0,
            retry_overhead_multiplier=1.85,
        )
        db.add(config)

        workflows = []
        for name, category, model, bench_cost, bench_value, bench_roi, strategic in DEMO_WORKFLOWS:
            wf = Workflow(
                name=name,
                category=category,
                department=category,
                default_model=model,
                manual_baseline_cost_usd=bench_cost * 3,
                expected_value_per_success_usd=bench_value,
                benchmark_roi_median=bench_roi,
                benchmark_cost_per_task_usd=bench_cost,
                is_strategic=strategic,
                description=f"Instrumented workflow — benchmark ROI {bench_roi}×",
            )
            db.add(wf)
            workflows.append(wf)
        db.commit()

        now = datetime.utcnow()
        for month_offset in range(5, -1, -1):
            month_start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                           - relativedelta(months=month_offset))
            runs_per_workflow = random.randint(80, 200)

            for wf in workflows:
                for _ in range(runs_per_workflow):
                    model = wf.default_model
                    prompt_tokens = random.randint(5000, 50000)
                    completion_tokens = random.randint(1000, 8000)
                    prompt = "x" * prompt_tokens
                    completion = "x" * completion_tokens
                    costs = estimate_cost(model, prompt, completion)
                    # Enterprise volume multiplier (concurrent users, agent loops)
                    scale = random.uniform(8.0, 25.0)
                    costs["total_cost_usd"] *= scale
                    costs["prompt_cost_usd"] *= scale
                    costs["completion_cost_usd"] *= scale

                    success_rate = 0.88 if wf.benchmark_roi_median and wf.benchmark_roi_median >= 3 else 0.72
                    successful = random.random() < success_rate
                    revenue_lift = (
                        wf.expected_value_per_success_usd * random.uniform(0.7, 1.3)
                        if successful
                        else 0.0
                    )

                    event = UsageEvent(
                        workflow_id=wf.id,
                        model=model,
                        prompt_tokens=costs["prompt_tokens"],
                        completion_tokens=costs["completion_tokens"],
                        prompt_cost_usd=costs["prompt_cost_usd"],
                        completion_cost_usd=costs["completion_cost_usd"],
                        total_cost_usd=costs["total_cost_usd"],
                        successful=successful,
                        revenue_lift_usd=revenue_lift,
                        hours_saved=random.uniform(0.5, 4.0) if successful else 0,
                        user_id=f"user_{random.randint(1, 50)}",
                        recorded_at=month_start + timedelta(
                            days=random.randint(0, 27),
                            hours=random.randint(0, 23),
                        ),
                    )
                    db.add(event)
            db.commit()

            month_label = month_start.strftime("%Y-%m")
            refresh_monthly_snapshot(db, month_label)

        print(f"Seeded {len(workflows)} workflows with 6 months of usage data.")
        print(f"Benchmarks loaded: {len(INDUSTRY_BENCHMARKS)} industry references.")
    finally:
        db.close()


def ensure_platform_workflows(db: Session) -> None:
    """Idempotent workflows for Cubiczan stack producers."""
    if db.query(Workflow).filter(Workflow.name == "Operational Intelligence Crew").first():
        return
    wf = Workflow(
        name="Operational Intelligence Crew",
        category="Platform",
        department="Engineering",
        default_model="gpt-4o-mini",
        manual_baseline_cost_usd=12.0,
        expected_value_per_success_usd=45.0,
        benchmark_roi_median=6.0,
        benchmark_cost_per_task_usd=2.5,
        is_strategic=True,
        description="oi crew + hiring — reports canonical usage to /api/usage-ingest",
    )
    db.add(wf)
    db.commit()
    print(f"Added platform workflow: Operational Intelligence Crew (id={wf.id})")


if __name__ == "__main__":
    seed_database()
