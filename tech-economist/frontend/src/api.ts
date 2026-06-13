export interface DashboardSummary {
  total_spend_mtd_usd: number;
  total_spend_ytd_usd: number;
  portfolio_roi: number;
  cost_per_successful_task_usd: number;
  successful_tasks_mtd: number;
  failed_tasks_mtd: number;
  success_rate_pct: number;
  ai_budget_utilization_pct: number;
  revenue_lift_mtd_usd: number;
  net_value_mtd_usd: number;
  eps_impact_per_share_usd: number;
  eps_at_risk_pct: number;
  projected_annual_spend_millions: number;
  benchmark_median_roi: number;
  workflows_underwater: number;
  workflows_high_leverage: number;
}

export interface WorkflowEconomics {
  workflow: {
    id: number;
    name: string;
    category: string;
    department: string;
    default_model: string;
    benchmark_roi_median: number | null;
    is_strategic: boolean;
  };
  total_spend_usd: number;
  total_revenue_lift_usd: number;
  successful_runs: number;
  failed_runs: number;
  cost_per_successful_task_usd: number;
  roi_multiple: number;
  vs_benchmark_roi: number | null;
  status: string;
}

export interface MonthlyTrend {
  month: string;
  total_spend_usd: number;
  total_revenue_lift_usd: number;
  portfolio_roi: number;
  cost_per_successful_task_usd: number;
  successful_tasks: number;
  token_volume_millions: number;
}

export interface ForecastPoint {
  month: string;
  projected_spend_usd: number;
  projected_roi: number;
  confidence_low_usd: number;
  confidence_high_usd: number;
}

export interface BenchmarkWorkflow {
  name: string;
  category: string;
  median_cost_usd: number;
  median_roi: number;
  source: string;
  insight: string;
}

export interface BenchmarksResponse {
  workflows: BenchmarkWorkflow[];
  principles: { title: string; source: string; detail: string }[];
  market_signals: Record<string, string | number>;
}

export interface EnterpriseConfig {
  company_name: string;
  shares_outstanding_millions: number;
  earnings_per_share: number;
  annual_tech_investment_billions: number;
  annual_revenue_billions: number;
  ai_compute_budget_millions: number;
  retry_overhead_multiplier: number;
}

export interface RoiScenarioResponse {
  annual_token_cost_usd: number;
  annual_value_usd: number;
  annual_net_value_usd: number;
  roi_multiple: number;
  payback_months: number | null;
  cost_per_successful_task_usd: number;
  recommendation: string;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  dashboard: () => fetchJson<DashboardSummary>("/api/dashboard"),
  workflowEconomics: () => fetchJson<WorkflowEconomics[]>("/api/workflows/economics"),
  trends: () => fetchJson<MonthlyTrend[]>("/api/trends"),
  forecast: () => fetchJson<ForecastPoint[]>("/api/forecast"),
  benchmarks: () => fetchJson<BenchmarksResponse>("/api/benchmarks"),
  config: () => fetchJson<EnterpriseConfig>("/api/config"),
  roiScenario: (body: Record<string, unknown>) =>
    fetchJson<RoiScenarioResponse>("/api/roi-scenario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
