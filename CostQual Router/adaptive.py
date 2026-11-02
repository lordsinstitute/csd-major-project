"""Setup B: adaptive handler -- semantic cache + complexity-based routing."""

import time

from cache import add_to_cache, check_cache
from config import COST_PER_TOKEN, MODEL_TIERS
from ollama_client import call_model
from router import route


def ask_adaptive(query: str) -> dict:
    lookup_start = time.perf_counter()
    cached = check_cache(query)
    lookup_ms = (time.perf_counter() - lookup_start) * 1000

    if cached is not None:
        return {
            "answer": cached["answer"],
            "latency_ms": lookup_ms,
            "tier_used": cached["tier_used"],
            "cache_hit": True,
            "estimated_cost": COST_PER_TOKEN["cache_hit"],
        }

    tier = route(query)
    model = MODEL_TIERS[tier]
    result = call_model(model, query)
    total_tokens = result["input_tokens"] + result["output_tokens"]
    estimated_cost = total_tokens * COST_PER_TOKEN[tier]

    add_to_cache(query, result["answer"], tier)

    return {
        "answer": result["answer"],
        "latency_ms": lookup_ms + result["latency_ms"],
        "tier_used": tier,
        "cache_hit": False,
        "estimated_cost": estimated_cost,
    }
