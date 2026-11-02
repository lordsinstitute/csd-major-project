"""Rule-based complexity classifier for the adaptive handler (Setup B).

Deliberately simple and readable -- no ML model. Three checks, in order:
  1. Short + matches a "simple question" pattern -> small model.
  2. Contains reasoning/explanation keywords, or is long -> large model.
  3. Otherwise -> medium model.
"""

import re

SIMPLE_WORD_LIMIT = 8
LONG_QUERY_WORD_LIMIT = 25

SIMPLE_PATTERNS = [
    r"^what is\b",
    r"^what are\b",
    r"^define\b",
    r"^calculate\b",
    r"^who is\b",
    r"^when (is|was|did)\b",
    r"^where is\b",
    r"^is\b.*\?$",
    r"^are\b.*\?$",
    r"^does\b.*\?$",
    r"^do\b.*\?$",
    r"^can\b.*\?$",
]

REASONING_KEYWORDS = [
    "explain",
    "why",
    "compare",
    "analyze",
    "analyse",
    "write a",
    "prove",
    "describe in detail",
    "pros and cons",
    "step by step",
    "walk me through",
]


def _word_count(query: str) -> int:
    return len(query.strip().split())


def _matches_simple_pattern(query: str) -> bool:
    text = query.strip().lower()
    return any(re.search(pattern, text) for pattern in SIMPLE_PATTERNS)


def _matches_reasoning_keyword(query: str) -> bool:
    text = query.strip().lower()
    return any(keyword in text for keyword in REASONING_KEYWORDS)


def route(query: str) -> str:
    """Return the tier name ("small", "medium", or "large") for a query."""
    word_count = _word_count(query)

    if word_count < SIMPLE_WORD_LIMIT and _matches_simple_pattern(query):
        return "small"

    if _matches_reasoning_keyword(query) or word_count > LONG_QUERY_WORD_LIMIT:
        return "large"

    return "medium"
