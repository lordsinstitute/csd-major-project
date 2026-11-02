"""Runs the fixed test-query set through Setup A (baseline) and Setup B
(adaptive), logging per-query metrics to benchmark_results.csv.

Both systems get a fair, un-warmed start: no cache is pre-populated before
the adaptive pass begins (it only builds up as duplicate/paraphrase queries
are naturally encountered during the run). Ollama model *loading* is warmed
up once before either pass so first-call model-load time doesn't dominate
the latency numbers for one system over the other.
"""

import csv
import json
import time

from adaptive import ask_adaptive
from baseline import ask_baseline
from cache import clear_cache
from config import BASELINE_MODEL, MODEL_TIERS
from ollama_client import call_model

QUERIES_PATH = "test_queries.json"
RESULTS_PATH = "benchmark_results.csv"

FIELDNAMES = [
    "query_id",
    "query",
    "category",
    "group",
    "system",
    "latency_ms",
    "cache_hit",
    "tier_used",
    "estimated_cost",
    "answer",
]


def warm_up_models() -> None:
    models = set(MODEL_TIERS.values()) | {BASELINE_MODEL}
    for model in models:
        print(f"  warming up {model} ...")
        call_model(model, "Hello")


def run_pass(queries: list[dict], system: str, handler) -> list[dict]:
    rows = []
    for i, q in enumerate(queries, start=1):
        result = handler(q["query"])
        rows.append(
            {
                "query_id": q["id"],
                "query": q["query"],
                "category": q["category"],
                "group": q["group"],
                "system": system,
                "latency_ms": round(result["latency_ms"], 2),
                "cache_hit": result["cache_hit"],
                "tier_used": result["tier_used"],
                "estimated_cost": result["estimated_cost"],
                "answer": result["answer"],
            }
        )
        print(
            f"  [{system}] {i}/{len(queries)} "
            f"tier={result['tier_used']} cache_hit={result['cache_hit']} "
            f"latency={result['latency_ms']:.0f}ms"
        )
    return rows


def main() -> None:
    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries = json.load(f)

    print(f"Loaded {len(queries)} queries from {QUERIES_PATH}")

    print("Warming up models (loads them into Ollama memory once)...")
    warm_up_models()

    print("\nRunning BASELINE pass (Setup A)...")
    start = time.perf_counter()
    baseline_rows = run_pass(queries, "baseline", ask_baseline)
    print(f"Baseline pass done in {time.perf_counter() - start:.1f}s")

    print("\nClearing cache to guarantee a cold start for the adaptive pass...")
    clear_cache()

    print("\nRunning ADAPTIVE pass (Setup B)...")
    start = time.perf_counter()
    adaptive_rows = run_pass(queries, "adaptive", ask_adaptive)
    print(f"Adaptive pass done in {time.perf_counter() - start:.1f}s")

    all_rows = baseline_rows + adaptive_rows
    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} result rows to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
