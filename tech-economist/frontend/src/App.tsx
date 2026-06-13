import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  BenchmarksResponse,
  DashboardSummary,
  EnterpriseConfig,
  ForecastPoint,
  MonthlyTrend,
  RoiScenarioResponse,
  WorkflowEconomics,
} from "./api";

type Tab = "overview" | "workflows" | "benchmarks" | "scenario";

function fmtUsd(n: number, compact = false): string {
  if (compact && Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (compact && Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(n);
}

function fmtRoi(n: number): string {
  return `${n.toFixed(1)}×`;
}

function KpiCard({ label, value, delta, deltaType }: {
  label: string;
  value: string;
  delta?: string;
  deltaType?: "positive" | "negative" | "neutral";
}) {
  return (
    <div className="card">
      <h3>{label}</h3>
      <div className="value">{value}</div>
      {delta && <div className={`delta ${deltaType ?? "neutral"}`}>{delta}</div>}
    </div>
  );
}

function OverviewTab({
  summary,
  trends,
  forecast,
  config,
}: {
  summary: DashboardSummary;
  trends: MonthlyTrend[];
  forecast: ForecastPoint[];
  config: EnterpriseConfig;
}) {
  const chartData = trends.map((t) => ({
    month: t.month,
    spend: t.total_spend_usd,
    lift: t.total_revenue_lift_usd,
    roi: t.portfolio_roi,
  }));

  const forecastData = forecast.map((f) => ({
    month: f.month.slice(5),
    projected: f.projected_spend_usd,
    low: f.confidence_low_usd,
    high: f.confidence_high_usd,
  }));

  const epsAtRisk = config.earnings_per_share * (summary.eps_at_risk_pct / 100);
  const epsIfNoValue = config.earnings_per_share - epsAtRisk;

  return (
    <>
      <div className="grid grid-4">
        <KpiCard
          label="MTD Token Spend"
          value={fmtUsd(summary.total_spend_mtd_usd)}
          delta={`YTD: ${fmtUsd(summary.total_spend_ytd_usd, true)}`}
        />
        <KpiCard
          label="Portfolio ROI"
          value={fmtRoi(summary.portfolio_roi)}
          delta={`Industry median: ${fmtRoi(summary.benchmark_median_roi)}`}
          deltaType={summary.portfolio_roi >= summary.benchmark_median_roi ? "positive" : "negative"}
        />
        <KpiCard
          label="Cost / Successful Task"
          value={fmtUsd(summary.cost_per_successful_task_usd)}
          delta={`${summary.success_rate_pct}% success rate`}
        />
        <KpiCard
          label="Net Value (MTD)"
          value={fmtUsd(summary.net_value_mtd_usd)}
          delta={`Revenue lift: ${fmtUsd(summary.revenue_lift_mtd_usd, true)}`}
          deltaType={summary.net_value_mtd_usd >= 0 ? "positive" : "negative"}
        />
        <KpiCard
          label="AI Budget Utilization"
          value={`${summary.ai_budget_utilization_pct.toFixed(0)}%`}
          delta={`Projected annual: $${summary.projected_annual_spend_millions}M`}
          deltaType={summary.ai_budget_utilization_pct > 90 ? "negative" : "neutral"}
        />
        <KpiCard
          label="High-Leverage Workflows"
          value={String(summary.workflows_high_leverage)}
          delta={`${summary.workflows_underwater} underwater`}
          deltaType="positive"
        />
      </div>

      <div className="eps-callout">
        <h3>Shareholder Value Lens</h3>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1rem" }}>
          {config.company_name} — {config.shares_outstanding_millions.toLocaleString()}M shares @ ${config.earnings_per_share} EPS.
          ${config.annual_tech_investment_billions}B tech portfolio places ${(config.annual_tech_investment_billions / config.shares_outstanding_millions).toFixed(2)}/share load on the stock.
        </p>
        <div className="eps-grid">
          <div className="eps-item">
            <div className="label">EPS at Risk</div>
            <div className="num" style={{ color: "var(--amber)" }}>{summary.eps_at_risk_pct}%</div>
          </div>
          <div className="eps-item">
            <div className="label">EPS if No Value Generated</div>
            <div className="num" style={{ color: "var(--red)" }}>${epsIfNoValue.toFixed(2)}</div>
          </div>
          <div className="eps-item">
            <div className="label">MTD EPS Impact</div>
            <div className="num" style={{ color: summary.eps_impact_per_share_usd >= 0 ? "var(--green)" : "var(--red)" }}>
              {summary.eps_impact_per_share_usd >= 0 ? "+" : ""}{summary.eps_impact_per_share_usd.toFixed(4)}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginTop: "1rem" }}>
        <div className="panel">
          <h2>Spend vs. Value Lift</h2>
          <p className="panel-desc">Longitudinal tracking — cost-per-outcome, not cost-per-token</p>
          <div className="chart-wrap">
            <ResponsiveContainer>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3444" />
                <XAxis dataKey="month" stroke="#8b9bb4" tick={{ fontSize: 11 }} />
                <YAxis stroke="#8b9bb4" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
                <Tooltip
                  contentStyle={{ background: "#141a22", border: "1px solid #2a3444", borderRadius: 8 }}
                  formatter={(v: number) => fmtUsd(v)}
                />
                <Legend />
                <Area type="monotone" dataKey="spend" name="Token Spend" stroke="#f87171" fill="#7f1d1d33" />
                <Area type="monotone" dataKey="lift" name="Revenue Lift" stroke="#34d399" fill="#065f4633" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <h2>Portfolio ROI Trend</h2>
          <p className="panel-desc">Attributed value divided by token spend per month</p>
          <div className="chart-wrap">
            <ResponsiveContainer>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3444" />
                <XAxis dataKey="month" stroke="#8b9bb4" tick={{ fontSize: 11 }} />
                <YAxis stroke="#8b9bb4" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}×`} />
                <Tooltip
                  contentStyle={{ background: "#141a22", border: "1px solid #2a3444", borderRadius: 8 }}
                  formatter={(v: number) => `${v.toFixed(2)}×`}
                />
                <Bar dataKey="roi" name="ROI Multiple" fill="#3d8bfd" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {forecastData.length > 0 && (
        <div className="panel">
          <h2>Spend Forecast</h2>
          <p className="panel-desc">6-month projection with 1.7–2.0× retry overhead (Deloitte guidance)</p>
          <div className="chart-wrap">
            <ResponsiveContainer>
              <AreaChart data={forecastData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3444" />
                <XAxis dataKey="month" stroke="#8b9bb4" />
                <YAxis stroke="#8b9bb4" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
                <Tooltip contentStyle={{ background: "#141a22", border: "1px solid #2a3444" }} />
                <Area type="monotone" dataKey="high" stackId="1" stroke="none" fill="#3d8bfd22" name="High" />
                <Area type="monotone" dataKey="projected" stroke="#3d8bfd" fill="#2563c444" name="Projected" />
                <Area type="monotone" dataKey="low" stackId="1" stroke="none" fill="#141a22" name="Low" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </>
  );
}

function WorkflowsTab({ economics }: { economics: WorkflowEconomics[] }) {
  return (
    <div className="panel">
      <h2>Workflow Unit Economics</h2>
      <p className="panel-desc">
        Cost-per-successful-task vs. attributed revenue lift — the discipline Bain and FinOps Foundation recommend
      </p>
      <table>
        <thead>
          <tr>
            <th>Workflow</th>
            <th>Category</th>
            <th>Spend</th>
            <th>Value Lift</th>
            <th>Cost/Task</th>
            <th>ROI</th>
            <th>vs Benchmark</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {economics.map((e) => (
            <tr key={e.workflow.id}>
              <td>
                <strong>{e.workflow.name}</strong>
                {e.workflow.is_strategic && (
                  <span style={{ marginLeft: 6, fontSize: "0.7rem", color: "var(--accent)" }}>STRATEGIC</span>
                )}
              </td>
              <td>{e.workflow.category}</td>
              <td>{fmtUsd(e.total_spend_usd)}</td>
              <td>{fmtUsd(e.total_revenue_lift_usd)}</td>
              <td>{fmtUsd(e.cost_per_successful_task_usd)}</td>
              <td style={{ fontWeight: 600 }}>{fmtRoi(e.roi_multiple)}</td>
              <td>
                {e.vs_benchmark_roi != null
                  ? `${e.vs_benchmark_roi >= 0 ? "+" : ""}${e.vs_benchmark_roi}%`
                  : "—"}
              </td>
              <td><span className={`status-pill ${e.status}`}>{e.status.replace("_", " ")}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BenchmarksTab({ data }: { data: BenchmarksResponse }) {
  return (
    <>
      <div className="market-signals">
        {Object.entries(data.market_signals).map(([key, val]) => (
          <div key={key} className="signal">
            <strong>{String(val)}</strong>
            {key.replace(/_/g, " ")}
          </div>
        ))}
      </div>

      <div className="panel">
        <h2>Industry Benchmarks</h2>
        <p className="panel-desc">Synthesized from Deloitte, Bain, FinOps Foundation, Digital Applied (2025–2026)</p>
        <table>
          <thead>
            <tr>
              <th>Workflow</th>
              <th>Category</th>
              <th>Median Cost</th>
              <th>Median ROI</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {data.workflows.map((b) => (
              <tr key={b.name}>
                <td><strong>{b.name}</strong></td>
                <td>{b.category}</td>
                <td>{fmtUsd(b.median_cost_usd)}</td>
                <td style={{ fontWeight: 600, color: b.median_roi >= 5 ? "var(--green)" : undefined }}>{fmtRoi(b.median_roi)}</td>
                <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>{b.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h2>FinOps for AI — Governing Principles</h2>
        <div className="grid grid-2">
          {data.principles.map((p) => (
            <div key={p.title} className="principle-card">
              <h4>{p.title}</h4>
              <div className="source">{p.source}</div>
              <p>{p.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function ScenarioTab() {
  const [result, setResult] = useState<RoiScenarioResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    workflow_name: "SEO Audit Pipeline",
    annual_runs: 1200,
    success_rate: 0.88,
    avg_revenue_lift_usd: 48,
    avg_hours_saved: 2.5,
    hourly_cost_usd: 150,
    model: "gpt-4o",
    avg_prompt_tokens: 4000,
    avg_completion_tokens: 2000,
    manual_baseline_cost_usd: 120,
  });

  const runScenario = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.roiScenario(form);
      setResult(res);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [form]);

  useEffect(() => {
    runScenario();
  }, []);

  return (
    <div className="panel">
      <h2>ROI Scenario Modeler</h2>
      <p className="panel-desc">
        Model annual token cost vs. attributed value using tokencost pricing + Deloitte retry overhead (1.85×)
      </p>

      <div className="scenario-form">
        {([
          ["workflow_name", "Workflow Name", "text"],
          ["annual_runs", "Annual Runs", "number"],
          ["success_rate", "Success Rate (0-1)", "number"],
          ["avg_revenue_lift_usd", "Avg Revenue Lift ($)", "number"],
          ["avg_hours_saved", "Avg Hours Saved", "number"],
          ["hourly_cost_usd", "Hourly Labor Cost ($)", "number"],
          ["avg_prompt_tokens", "Avg Prompt Tokens", "number"],
          ["avg_completion_tokens", "Avg Completion Tokens", "number"],
          ["manual_baseline_cost_usd", "Manual Baseline ($)", "number"],
        ] as const).map(([key, label, type]) => (
          <label key={key}>
            {label}
            <input
              type={type}
              value={form[key]}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  [key]: type === "number" ? Number(e.target.value) : e.target.value,
                }))
              }
            />
          </label>
        ))}
        <label>
          Model
          <select
            value={form.model}
            onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
          >
            <option value="gpt-4o">gpt-4o</option>
            <option value="gpt-4o-mini">gpt-4o-mini</option>
            <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet</option>
            <option value="o1-mini">o1-mini</option>
          </select>
        </label>
        <button className="btn" onClick={runScenario} disabled={loading}>
          {loading ? "Calculating…" : "Recalculate"}
        </button>
      </div>

      {result && (
        <div className="scenario-result">
          <KpiCard label="Annual Token Cost" value={fmtUsd(result.annual_token_cost_usd)} />
          <KpiCard label="Annual Value" value={fmtUsd(result.annual_value_usd)} deltaType="positive" />
          <KpiCard label="Net Value" value={fmtUsd(result.annual_net_value_usd)} deltaType={result.annual_net_value_usd >= 0 ? "positive" : "negative"} />
          <KpiCard label="ROI Multiple" value={fmtRoi(result.roi_multiple)} />
          <KpiCard label="Cost / Task" value={fmtUsd(result.cost_per_successful_task_usd)} />
          <KpiCard
            label="Payback"
            value={result.payback_months ? `${result.payback_months} mo` : "N/A"}
          />
          <div className="recommendation">{result.recommendation}</div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [economics, setEconomics] = useState<WorkflowEconomics[]>([]);
  const [trends, setTrends] = useState<MonthlyTrend[]>([]);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarksResponse | null>(null);
  const [config, setConfig] = useState<EnterpriseConfig | null>(null);

  useEffect(() => {
    Promise.all([
      api.dashboard(),
      api.workflowEconomics(),
      api.trends(),
      api.forecast(),
      api.benchmarks(),
      api.config(),
    ])
      .then(([s, e, t, f, b, c]) => {
        setSummary(s);
        setEconomics(e);
        setTrends(t);
        setForecast(f);
        setBenchmarks(b);
        setConfig(c);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading Tech Economist dashboard…</div>;
  if (error) return <div className="error">Failed to load: {error}. Is the API running on port 8000?</div>;
  if (!summary || !config || !benchmarks) return null;

  return (
    <div className="app">
      <header className="header">
        <h1>Tech Economist</h1>
        <p className="subtitle">
          AI token economics for CFOs — measure cost-per-successful-task, not tokens-per-human.
          Powered by <a href="https://github.com/AgentOps-AI/tokencost" style={{ color: "var(--accent)" }}>tokencost</a> with longitudinal SQLite tracking.
        </p>
        <div className="header-meta">
          <span className="badge accent">{config.company_name}</span>
          <span className="badge">AI Compute Budget: ${config.ai_compute_budget_millions}M/yr</span>
          <span className="badge">Tech Portfolio: ${config.annual_tech_investment_billions}B</span>
        </div>
      </header>

      <nav className="tabs">
        {([
          ["overview", "Executive Overview"],
          ["workflows", "Workflow Economics"],
          ["benchmarks", "Industry Benchmarks"],
          ["scenario", "ROI Modeler"],
        ] as const).map(([id, label]) => (
          <button
            key={id}
            className={`tab ${tab === id ? "active" : ""}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === "overview" && <OverviewTab summary={summary} trends={trends} forecast={forecast} config={config} />}
      {tab === "workflows" && <WorkflowsTab economics={economics} />}
      {tab === "benchmarks" && <BenchmarksTab data={benchmarks} />}
      {tab === "scenario" && <ScenarioTab />}
    </div>
  );
}
