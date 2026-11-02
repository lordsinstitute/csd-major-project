"""Model-independent transcript operations. Times are seconds in original audio."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4


def new_meeting(title: str) -> dict:
    return dict(id=uuid4().hex, title=title.strip() or "Untitled meeting",
                created=datetime.now(timezone.utc).isoformat(), status="empty",
                duration=0.0, original="", audio="", words=[], segments=[],
                intervals=[], speakers={}, error="", stage="", reviewed=False)


def timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


def join_words(words: list[dict]) -> str:
    text = " ".join(w["word"].strip() for w in words if w["word"].strip())
    text = re.sub(r"\s+([,.;:!?%\)\]])", r"\1", text)
    return re.sub(r"([\(\[])\s+", r"\1", text)


def normalize_asr(result: dict) -> list[dict]:
    """Require real word timings; never invent word offsets from sentence length."""
    words = []
    for segment in result.get("segments", []):
        if segment.get("text", "").strip() and not segment.get("words"):
            raise ValueError("ASR returned no word timestamps. Speaker alignment requires word timings.")
        for word in segment.get("words", []):
            start, end = float(word["start"]), float(word["end"])
            if end < start or start < 0:
                raise ValueError("ASR returned invalid word timestamps.")
            text = word.get("word", word.get("text", "")).strip()
            if text:
                words.append(dict(start=start, end=end, word=text))
    return sorted(words, key=lambda w: w["start"])


def align_words(words: list[dict], intervals: list[dict]) -> list[dict]:
    """Assign by temporal overlap, flag simultaneous speech, leave gaps unknown.

    Sweep only intervals near each word, avoiding quadratic scans on hour-long audio.
    This aligns ASR words, it does not separate the audio of simultaneous talkers.
    """
    spans = sorted(intervals, key=lambda i: i["start"])
    active, cursor, output = [], 0, []
    for original in sorted(words, key=lambda w: w["start"]):
        word = dict(original)
        lo, hi = word["start"], word["end"]
        hi = max(hi, lo + .01)
        active = [s for s in active if s["end"] > lo]
        while cursor < len(spans) and spans[cursor]["start"] < hi:
            if spans[cursor]["end"] > lo:
                active.append(spans[cursor])
            cursor += 1
        scores = defaultdict(float)
        for span in active:
            scores[span["speaker"]] += max(0, min(hi, span["end"]) - max(lo, span["start"]))
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        word["speaker"] = ranked[0][0] if ranked else "unknown"
        word["overlap"] = len(ranked) > 1 and ranked[1][1] >= .25 * (hi - lo)
        output.append(word)
    return output


def make_segments(words: list[dict]) -> list[dict]:
    groups = []
    for word in words:
        speaker = word.get("speaker", "unknown")
        if (not groups or groups[-1]["speaker"] != speaker
                or word["start"] - groups[-1]["end"] > 1.2
                or word["end"] - groups[-1]["start"] > 25):
            groups.append(dict(id=uuid4().hex, speaker=speaker, start=word["start"],
                               end=word["end"], words=[], overlap=False))
        group = groups[-1]
        group["words"].append(dict(word))
        group["end"] = max(group["end"], word["end"])
        group["overlap"] |= word.get("overlap", False)
    for group in groups:
        group["text"] = join_words(group["words"])
    return groups


def merge_speakers(meeting: dict, source: str, target: str) -> None:
    if source == target or source not in meeting["speakers"] or target not in meeting["speakers"]:
        raise ValueError("Choose two different detected speakers.")
    for collection in [meeting["intervals"], meeting["words"], meeting["segments"]]:
        for item in collection:
            if item.get("speaker") == source:
                item["speaker"] = target
            for word in item.get("words", []):
                if word.get("speaker") == source:
                    word["speaker"] = target
    del meeting["speakers"][source]
    meeting["reviewed"] = False


def sample_ranges(intervals: list[dict], speaker: str, limit: int = 3) -> list[tuple[float, float]]:
    """Prefer clean, long speech away from overlapping speaker intervals."""
    candidates = []
    others = [i for i in intervals if i["speaker"] != speaker]
    for span in intervals:
        if span["speaker"] != speaker:
            continue
        pieces = [(span["start"], span["end"])]
        for other in others:
            if other["end"] <= span["start"] or other["start"] >= span["end"]:
                continue
            pieces = [(a, b) for lo, hi in pieces for a, b in
                      [(lo, min(hi, other["start"])), (max(lo, other["end"]), hi)] if b - a >= .5]
        candidates.extend((lo, min(hi, lo + 7)) for lo, hi in pieces if hi - lo >= 1)
    return sorted(candidates, key=lambda p: p[1] - p[0], reverse=True)[:limit]


def reassign_segment(meeting: dict, segment_id: str, speaker: str) -> None:
    if speaker != "unknown" and speaker not in meeting["speakers"]:
        raise ValueError("Unknown speaker")
    segment = next(s for s in meeting["segments"] if s["id"] == segment_id)
    segment["speaker"] = speaker
    for word in segment["words"]:
        word["speaker"] = speaker
    # ASR words and reviewed segment words are both retained consistently.
    for word in meeting["words"]:
        if segment["start"] <= word["start"] < segment["end"]:
            word["speaker"] = speaker
    meeting["reviewed"] = False


def speaker_name(meeting: dict, speaker: str) -> str:
    return meeting["speakers"].get(speaker, {}).get("name", "Unassigned")
