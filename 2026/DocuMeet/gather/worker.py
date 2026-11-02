"""Isolated, cancellable workers, invoked by QProcess or from the CLI."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import traceback
from pathlib import Path

from .audio import normalize_audio
from .domain import align_words, make_segments, normalize_asr
from .storage import Store

PREFIX = "@@GATHER@@"


def emit(message: str, percent: int = -1, kind: str = "progress"):
    print(PREFIX + json.dumps(dict(kind=kind, message=message, percent=percent), ensure_ascii=True), flush=True)


def process_job(store: Store, meeting_id: str, job: str):
    from . import engines
    meeting = store.get(meeting_id)
    meeting.update(status="processing", stage=job, error="")
    store.save(meeting)
    try:
        if job == "prepare":
            emit("Preparing the meeting recording…", 10)
            original = Path(meeting["original"])
            folder = store.folder(meeting_id)
            if original.parent.resolve() != folder.resolve():
                target = folder / ("original" + original.suffix.lower())
                shutil.copy2(original, target)
                original = target
            meeting["original"] = str(original)
            audio = folder / "meeting.wav"
            meeting["duration"] = normalize_audio(original, audio, meeting.get("raw"))
            meeting["audio"] = str(audio)
            meeting["status"] = "ready"
        elif job == "transcribe":
            if not meeting["audio"]:
                raise ValueError("Prepare a recording before transcription.")
            result = engines.transcribe(store.home, Path(meeting["audio"]), emit)
            words = normalize_asr(result)
            if not words:
                raise ValueError("No speech was detected. Check the recording volume and try another file.")
            meeting["words"] = words
            meeting["segments"] = make_segments(words)
            meeting["status"] = "transcribed"
        elif job == "speakers":
            if not meeting["words"]:
                raise ValueError("Transcribe the recording first.")
            intervals = engines.diarize(store.home, Path(meeting["audio"]), emit)
            if not intervals:
                raise ValueError("No speaker turns were detected. You can still export the unassigned transcript.")
            meeting["intervals"] = intervals
            meeting["words"] = align_words(meeting["words"], intervals)
            meeting["segments"] = make_segments(meeting["words"])
            ids = sorted({i["speaker"] for i in intervals}, key=lambda s: int(s.split("_")[-1]))
            meeting["speakers"] = {sid: dict(name=f"Speaker {idx + 1}", color=idx % 8) for idx, sid in enumerate(ids)}
            meeting["reviewed"] = False
            meeting["status"] = "review"
        else:
            raise ValueError(f"Unknown job: {job}")
        meeting.update(error="", stage="")
        store.save(meeting)
        emit("Done", 100, "done")
    except BaseException as exc:
        meeting.update(status="error", error=str(exc), stage=job)
        store.save(meeting)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job", choices=["prepare", "transcribe", "speakers", "setup"])
    parser.add_argument("--home", required=True)
    parser.add_argument("--meeting")
    args = parser.parse_args()
    try:
        store = Store(args.home)
        if args.job == "setup":
            from .engines import setup_models
            setup_models(store.home, emit)
            emit("Offline models installed", 100, "done")
        else:
            process_job(store, args.meeting, args.job)
    except BaseException as exc:
        traceback.print_exc(file=sys.stderr)
        emit(str(exc), -1, "error")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
