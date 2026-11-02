"""Setup A: naive baseline handler -- always calls one fixed model.

No cache, no routing. This is the "reasonable middle-ground default" a
naive implementation would ship with.
"""

from config import BASELINE_MODEL, COST_PER_TOKEN
from ollama_client import call_model


def ask_baseline(query: str) -> dict:
    result = call_model(BASELINE_MODEL, query)
    total_tokens = result["input_tokens"] + result["output_tokens"]
    estimated_cost = total_tokens * COST_PER_TOKEN["baseline"]

    return {
        "answer": result["answer"],
        "latency_ms": result["latency_ms"],
        "tier_used": "baseline",
        "cache_hit": False,
        "estimated_cost": estimated_cost,
    }
