"""Per-million token pricing tiers (Ken Huang / Claude Code style)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ModelCosts:
    input_tokens: float
    output_tokens: float
    prompt_cache_write_tokens: float
    prompt_cache_read_tokens: float
    web_search_requests: float = 0.01


# Standard tiers — USD per million tokens
COST_TIER_0_15_0_60 = ModelCosts(0.15, 0.60, 0.19, 0.015)
COST_TIER_2_5_10 = ModelCosts(2.5, 10.0, 3.125, 0.25)
COST_TIER_3_15 = ModelCosts(3.0, 15.0, 3.75, 0.30)
COST_TIER_15_75 = ModelCosts(15.0, 75.0, 18.75, 1.5)

DEFAULT_UNKNOWN = COST_TIER_3_15

MODEL_COSTS: Dict[str, ModelCosts] = {
    "gpt-4o-mini": COST_TIER_0_15_0_60,
    "gpt-4o": COST_TIER_2_5_10,
    "gpt-4.1": COST_TIER_2_5_10,
    "gpt-4.1-mini": COST_TIER_0_15_0_60,
    "claude-3-5-sonnet-20241022": COST_TIER_3_15,
    "claude-3-5-sonnet-latest": COST_TIER_3_15,
    "claude-sonnet-4-20250514": COST_TIER_3_15,
    "claude-opus-4-20250514": COST_TIER_15_75,
    "o1-mini": ModelCosts(1.1, 4.4, 1.375, 0.11),
}


def canonical_model_name(model: str) -> str:
    return model.strip().lower()


def get_model_costs(model: str) -> ModelCosts:
    key = canonical_model_name(model)
    if key in MODEL_COSTS:
        return MODEL_COSTS[key]
    for prefix, costs in MODEL_COSTS.items():
        if key.startswith(prefix) or prefix in key:
            return costs
    return DEFAULT_UNKNOWN
