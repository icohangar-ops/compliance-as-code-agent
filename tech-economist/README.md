# Tech Economist

**AI token economics dashboard for CFOs** — justify ROI on AI spend using industry benchmarks, unit economics, and longitudinal tracking.

Built on [AgentOps-AI/tokencost](https://github.com/AgentOps-AI/tokencost) for real-time LLM cost estimation across 400+ models.

## The Problem

Technologists lack capital allocation training; finance lacks technical fluency. Billions flow into AI, cloud, and infrastructure with no consistent economic framework. This dashboard implements the emerging **Technology Economist** discipline:

- **Cost per successful task**, not cost per token (FinOps Foundation, SHI)
- **Dedicated AI compute budget** with governance (Bain & Company)
- **Model routing** by workflow complexity (Deloitte, Digital Applied)
- **EPS impact modeling** for shareholder value alignment

## Research Foundation

Benchmarks and principles synthesized from:

| Source | Key Finding |
|--------|-------------|
| [Deloitte — CFO Guide to AI Token Economics](https://www.deloitte.com/us/en/services/consulting/articles/cfo-guide-ai-token-economics.html) | Token costs must factor into TCO, margins, and forecasts; use 1.7–2.0× retry overhead |
| [Bain — How Token Economics Will Change Opex](https://www.bain.com/insights/how-token-economics-will-change-opex/) | Token prices fell 50% YoY while consumption grew 4.5×; instrument cost-per-task now |
| [Digital Applied — 50 Agency Workflows](https://www.digitalapplied.com/blog/token-cost-roi-50-agency-workflows-measured) | ROI ranges 1.6×–11.4×; $/successful-task is the right unit, not $/1M tokens |
| [FinOps Foundation / SHI](https://blog.shi.com/business-of-it/finops-for-ai/) | Compete on value-per-token; shift metrics from consumption to outcomes |
| [CFO Connect Summit 2025](https://www.cfoconnect.eu/resources/event-recaps/summit-2025-recap-3-the-cfos-transformation-playbook-how-to-drive-ai-adoption-and-cultural-change-across-your-enterprise/) | Three budget categories: power-user, per-seat, outcome-based |

## Architecture

```
┌─────────────────────┐     ┌──────────────────────────────┐
│  React Dashboard    │────▶│  FastAPI Backend (Python)    │
│  (Vite + Recharts)  │     │  ├── tokencost integration   │
└─────────────────────┘     │  ├── ROI analytics engine    │
                            │  └── SQLite (longitudinal)   │
                            └──────────────────────────────┘
```

## Quick Start

### 1. Backend

```bash
cd tech-economist/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On first start, the API seeds 8 demo workflows with 6 months of instrumented usage data.

### 2. Frontend

```bash
cd tech-economist/frontend
npm install
npm run dev
```

Open http://localhost:5173

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard` | GET | Executive KPIs: spend, ROI, EPS impact |
| `/api/workflows/economics` | GET | Per-workflow unit economics |
| `/api/trends` | GET | Monthly longitudinal snapshots |
| `/api/forecast` | GET | 6-month spend projection |
| `/api/benchmarks` | GET | Industry benchmarks + FinOps principles |
| `/api/roi-scenario` | POST | Interactive ROI modeler |
| `/api/cost-estimate` | POST | Real-time tokencost pricing |
| `/api/usage-events` | POST | Record instrumented usage events |

## Recording Usage Events

```python
import requests

requests.post("http://localhost:8000/api/usage-events", json={
    "workflow_id": 1,
    "model": "gpt-4o",
    "prompt": "Analyze Q4 revenue trends...",
    "completion": "Revenue grew 12%...",
    "successful": True,
    "revenue_lift_usd": 48.0,
    "hours_saved": 2.5,
    "user_id": "analyst_42"
})
```

Costs are computed via `tokencost` and stored in SQLite for trend analysis.

## Database

SQLite database at `backend/data/tech_economist.db`:

- `workflows` — instrumented AI workflows with benchmark references
- `usage_events` — per-run token costs, success labels, revenue attribution
- `monthly_snapshots` — aggregated longitudinal metrics
- `enterprise_config` — EPS, shares, tech portfolio for shareholder modeling

## License

MIT
