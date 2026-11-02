from __future__ import annotations

import os
import subprocess
import wave
from pathlib import Path


def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def normalize_audio(source: str | Path, target: str | Path, raw: dict | None = None) -> float:
    target = Path(target)
    partial = target.with_name(target.stem + ".partial.wav")
    cmd = [ffmpeg_exe(), "-nostdin", "-y", "-v", "error"]
    if raw:
        cmd += ["-f", raw["format"], "-ar", str(raw["rate"]), "-ac", str(raw["channels"])]
    cmd += ["-i", str(source), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(partial)]
    result = subprocess.run(cmd, capture_output=True, creationflags=0x08000000 if os.name == "nt" else 0)
    if result.returncode:
        partial.unlink(missing_ok=True)
        raise ValueError("Cannot read this recording. " + result.stderr.decode("utf-8", "replace")[-1500:])
    with wave.open(str(partial), "rb") as stream:
        duration = stream.getnframes() / stream.getframerate()
    if duration < .25:
        partial.unlink(missing_ok=True)
        raise ValueError("The recording is empty or too short.")
    partial.replace(target)
    return duration


def cut_sample(source: str | Path, target: str | Path, start: float, end: float):
    with wave.open(str(source), "rb") as inp:
        rate = inp.getframerate()
        start_frame = max(0, int(start * rate))
        inp.setpos(min(start_frame, inp.getnframes()))
        frames = inp.readframes(max(0, int((end - start) * rate)))
        params = inp.getparams()
    with wave.open(str(target), "wb") as out:
        out.setparams(params)
        out.writeframes(frames)
