from app.schemas import BenchmarkWorkflow

# Synthesized from Deloitte, Bain, FinOps Foundation, Digital Applied (2025–2026)
INDUSTRY_BENCHMARKS: list[BenchmarkWorkflow] = [
    BenchmarkWorkflow(
        name="SEO Audit (full site)",
        category="Marketing",
        median_cost_usd=4.20,
        median_roi=11.4,
        source="Digital Applied — 50 Agency Workflows",
        insight="Highest-leverage agentic workflow; retainer expansion drives attributed lift.",
    ),
    BenchmarkWorkflow(
        name="Lead Enrichment",
        category="Hybrid",
        median_cost_usd=1.85,
        median_roi=8.9,
        source="Digital Applied — 50 Agency Workflows",
        insight="Strong ROI when input is one-shot; limited cache benefit.",
    ),
    BenchmarkWorkflow(
        name="PR Backlink Outreach",
        category="Marketing",
        median_cost_usd=2.10,
        median_roi=6.2,
        source="Digital Applied — 50 Agency Workflows",
        insight="Outbound automation with clear revenue attribution.",
    ),
    BenchmarkWorkflow(
        name="Code Refactor (multi-file)",
        category="Engineering",
        median_cost_usd=3.40,
        median_roi=5.8,
        source="Digital Applied — 50 Agency Workflows",
        insight="Open-weight models reduce cost floor; route by complexity.",
    ),
    BenchmarkWorkflow(
        name="Ad Copy Iteration",
        category="Marketing",
        median_cost_usd=0.45,
        median_roi=4.5,
        source="Digital Applied — 50 Agency Workflows",
        insight="High-volume, low-cost; GPT-class models win at scale.",
    ),
    BenchmarkWorkflow(
        name="Email Triage",
        category="Operations",
        median_cost_usd=0.07,
        median_roi=2.1,
        source="Digital Applied — 50 Agency Workflows",
        insight="Cheap per run but low attributed revenue lift.",
    ),
    BenchmarkWorkflow(
        name="Client Report Generation",
        category="Hybrid",
        median_cost_usd=2.30,
        median_roi=1.6,
        source="Digital Applied — 50 Agency Workflows",
        insight="Replaces operational cost without unlocking new revenue.",
    ),
    BenchmarkWorkflow(
        name="Competitor Analysis (long-context)",
        category="Strategy",
        median_cost_usd=12.40,
        median_roi=3.2,
        source="Digital Applied — 50 Agency Workflows",
        insight="Premium frontier models justified for 1M context tasks.",
    ),
    BenchmarkWorkflow(
        name="AI Coding Platform (startup)",
        category="Engineering",
        median_cost_usd=2000.0,
        median_roi=50.0,
        source="Deloitte — CFO Guide to AI Token Economics",
        insight="15-person startup: $2K tokens → 300K LOC; broad adoption justified.",
    ),
    BenchmarkWorkflow(
        name="Power-User Engineering",
        category="Engineering",
        median_cost_usd=10000.0,
        median_roi=100.0,
        source="Deloitte / Vercel CEO commentary",
        insight="$10K/day token spend can save millions in delivery; track productivity not volume.",
    ),
]

FINOPS_PRINCIPLES = [
    {
        "title": "Cost per successful task, not per token",
        "source": "FinOps Foundation / SHI",
        "detail": "Measure shippable artifacts against attributed revenue lift. $/1M tokens is a vanity metric.",
    },
    {
        "title": "Dedicated AI compute budget",
        "source": "Bain & Company",
        "detail": "Stop funding tokens from existing line items. Treat AI spend as protected transformation capital.",
    },
    {
        "title": "Model routing by workflow",
        "source": "Bain / Digital Applied",
        "detail": "Frontier models for high-stakes; smaller/open models for volume. Single-model stacks leave 30–50% margin.",
    },
    {
        "title": "1.7–2.0× retry overhead multiplier",
        "source": "Deloitte CFO Guide",
        "detail": "Forecast with (tokens/user × volume × cost/token) × overhead for retries and agent loops.",
    },
    {
        "title": "Three budget categories",
        "source": "CFO Connect Summit 2025",
        "detail": "Power-user consumption, per-seat productivity tools, and outcome-based strategic initiatives.",
    },
    {
        "title": "Dual-cost transition planning",
        "source": "Bain & Company",
        "detail": "Model overlap period paying legacy workforce + scaling token bill. Build into board narrative early.",
    },
]

MARKET_SIGNALS = {
    "token_price_decline_yoy_pct": 50,
    "token_consumption_growth_yoy_x": 4.5,
    "prompt_cache_savings_pct_range": "38–72%",
    "high_reasoning_cost_multiplier": "6–9×",
    "median_agency_roi_range": "1.6×–11.4×",
    "ai_investment_increase_pct_orgs": 67,
}


def get_benchmarks() -> list[BenchmarkWorkflow]:
    return INDUSTRY_BENCHMARKS


def get_finops_principles() -> list[dict]:
    return FINOPS_PRINCIPLES


def get_market_signals() -> dict:
    return MARKET_SIGNALS
