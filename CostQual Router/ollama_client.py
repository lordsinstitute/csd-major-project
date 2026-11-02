"""Thin wrapper around the local Ollama HTTP API."""

import time

import requests

from config import OLLAMA_URL


def call_model(model: str, prompt: str, timeout: int = 240, retries: int = 2) -> dict:
    """Call a local Ollama model and return timing + token-count info.

    Returns a dict with: answer, latency_ms, input_tokens, output_tokens.

    Long sequential benchmark runs occasionally hit a slow/stalled response
    from the local Ollama server (GPU/CPU contention, not a real error), so
    a timeout is retried a couple of times before giving up for real.
    """
    last_error = None
    for attempt in range(retries + 1):
        start = time.perf_counter()
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            last_error = exc
            print(f"    (retrying {model} call after error: {exc})")
            continue

        elapsed_ms = (time.perf_counter() - start) * 1000
        data = response.json()
        return {
            "answer": data.get("response", "").strip(),
            "latency_ms": elapsed_ms,
            "input_tokens": data.get("prompt_eval_count", 0),
            "output_tokens": data.get("eval_count", 0),
        }

    raise last_error
