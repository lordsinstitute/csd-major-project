"""Lightweight quality sanity check (Step 9 of the build plan).

Not a rigorous eval -- just enough to say "quality held up" in the demo.
Full BERTScore-style evaluation belongs in the real month-long project.

For queries where the adaptive system routed to a smaller model than the
baseline and produced a different answer, ask the baseline model to act as
a judge and rate whether the adaptive answer is an acceptable answer to the
question, given the baseline answer as a reference.
"""

import csv
import random

from config import BASELINE_MODEL
from ollama_client import call_model

RESULTS_PATH = "benchmark_results.csv"
OUTPUT_PATH = "quality_check_results.csv"
SAMPLE_SIZE = 10

JUDGE_PROMPT_TEMPLATE = """You are grading answer quality. A question was answered by two systems.

Question: {query}

Reference answer (from a larger/default model): {baseline_answer}

Candidate answer (from a smaller, routed model): {adaptive_answer}

Is the candidate answer an acceptable, factually consistent answer to the question,
even if worded differently or less detailed than the reference? Reply with exactly
one word: PASS or FAIL."""


def load_rows() -> list[dict]:
    with open(RESULTS_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_candidates(rows: list[dict]) -> list[dict]:
    by_id = {}
    for row in rows:
        by_id.setdefault(row["query_id"], {})[row["system"]] = row

    candidates = []
    for query_id, systems in by_id.items():
        baseline = systems.get("baseline")
        adaptive = systems.get("adaptive")
        if not baseline or not adaptive:
            continue
        if adaptive["cache_hit"].strip().lower() == "true":
            continue
        if adaptive["tier_used"] not in ("small", "medium"):
            continue
        if adaptive["answer"].strip() == baseline["answer"].strip():
            continue
        candidates.append(
            {
                "query_id": query_id,
                "query": baseline["query"],
                "baseline_answer": baseline["answer"],
                "adaptive_answer": adaptive["answer"],
                "tier_used": adaptive["tier_used"],
            }
        )
    return candidates


def judge(candidate: dict) -> str:
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        query=candidate["query"],
        baseline_answer=candidate["baseline_answer"],
        adaptive_answer=candidate["adaptive_answer"],
    )
    result = call_model(BASELINE_MODEL, prompt)
    verdict = result["answer"].strip().upper()
    return "PASS" if "PASS" in verdict else "FAIL"


def main() -> None:
    rows = load_rows()
    candidates = find_candidates(rows)
    print(f"Found {len(candidates)} candidate queries with a differing, smaller-model answer.")

    sample = random.sample(candidates, min(SAMPLE_SIZE, len(candidates)))

    results = []
    for i, candidate in enumerate(sample, start=1):
        verdict = judge(candidate)
        results.append({**candidate, "verdict": verdict})
        print(f"  [{i}/{len(sample)}] query_id={candidate['query_id']} tier={candidate['tier_used']} -> {verdict}")

    if results:
        pass_count = sum(1 for r in results if r["verdict"] == "PASS")
        pass_rate = pass_count / len(results)
    else:
        pass_rate = 0

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["query_id", "query", "tier_used", "baseline_answer", "adaptive_answer", "verdict"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nPass rate: {pass_rate:.0%} ({len(results)} sampled)")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
