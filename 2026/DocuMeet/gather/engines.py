"""Real local model adapters. Only setup_models may contact the network."""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable
from .domain import timestamp

ASR_ID = "moondream/parakeet-redux"
DIAR_ID = "nvidia/Nemotron-3-Diarization"
Progress = Callable[[str, int], None]


def environment(home: Path, online: bool = False):
    os.environ["HF_HOME"] = str(home / "models" / "huggingface")
    os.environ["HF_HUB_CACHE"] = str(home / "models" / "huggingface" / "hub")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_OFFLINE"] = "0" if online else "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "0" if online else "1"
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


def manifest(home: Path) -> dict:
    path = home / "models" / "ready.json"
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def require_ready(home: Path):
    ready = manifest(home)
    if not ready.get("asr") or not ready.get("diarization"):
        raise RuntimeError("Models are not ready. Open Model setup and download both offline models first.")
    return ready


def _torch_threads(torch):
    torch.set_num_threads(max(1, min(8, (os.cpu_count() or 4) - 1)))


@contextmanager
def photon_cpu(progress: Progress, checkpoint: str | None = None):
    """Use the same Redux weights on Windows wheels without packed CPU kernels.

    Kestrel's reference dense materializer exists for CUDA but its default CPU
    policy raises when the native wheel reports 'scalar'. Opt into that exact
    dequantization on CPU deliberately. This changes storage/execution form only,
    not the checkpoint, transcription model, or tokenizer. Scoped to this worker.
    """
    import moondream as md
    import torch
    import kestrel_kernels.ternary as ternary
    from kestrel.photon import PhotonReporter
    original = ternary.resident_form
    original_flush = PhotonReporter._flush_window
    async def no_telemetry(self, **kwargs):
        return None
    # This SDK version sends anonymous usage rollups even without an API key.
    # DocuMeet's offline contract excludes those calls as well as cloud inference.
    PhotonReporter._flush_window = no_telemetry
    compatibility = not ternary.ternary_gemm_ready()
    if compatibility:
        progress("Using CPU compatibility mode (expanded Redux weights; more RAM)…", 15)
        def execution_form(device):
            return "dense" if torch.device(device).type == "cpu" else original(device)
        ternary.resident_form = execution_form
    try:
        threads = max(1, min(8, (os.cpu_count() or 4) // 2))
        options = dict(device="cpu", cpu_threads=threads, api_key="")
        if checkpoint:
            options["model_path"] = checkpoint
        with md.photon(ASR_ID, **options) as speech:
            yield speech, "dense CPU compatibility" if compatibility else "packed CPU"
    finally:
        ternary.resident_form = original
        PhotonReporter._flush_window = original_flush


def setup_models(home: Path, progress: Progress):
    environment(home, online=True)
    from huggingface_hub import snapshot_download
    import moondream as md
    import torch
    from transformers import AutoModelForAudioFrameClassification, AutoProcessor
    _torch_threads(torch)
    ready_file = home / "models" / "ready.json"
    progress("Downloading Parakeet Redux (about 178 MB)…", 10)
    asr_path = snapshot_download(ASR_ID, allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model"])
    progress("Downloading Nemotron speaker model (about 400 MB)…", 40)
    diar_path = snapshot_download(DIAR_ID, allow_patterns=["*.json", "*.safetensors", "*.txt"])
    progress("Preparing the CPU speech runtime…", 70)
    # Photon resolves the repository ID in the pre-populated local HF cache.
    with photon_cpu(progress, asr_path) as (speech, asr_mode):
        import numpy as np
        import soundfile as sf
        silence = home / "models" / "warmup.wav"
        sf.write(str(silence), np.zeros(16000, dtype=np.float32), 16000)
        speech.transcribe(audio=str(silence), timestamps="word")
        silence.unlink(missing_ok=True)
    progress("Verifying the speaker model on CPU…", 85)
    processor = AutoProcessor.from_pretrained(diar_path, local_files_only=True)
    model = AutoModelForAudioFrameClassification.from_pretrained(diar_path, local_files_only=True).to("cpu").eval()
    with torch.inference_mode():
        inputs = processor(np.zeros(16000, dtype=np.float32), sampling_rate=16000, return_tensors="pt")
        model(**inputs)
    ready = dict(asr=asr_path, diarization=diar_path, asr_id=ASR_ID, diarization_id=DIAR_ID, asr_mode=asr_mode)
    temp = ready_file.with_suffix(".tmp")
    temp.write_text(json.dumps(ready, indent=2), "utf-8")
    temp.replace(ready_file)
    progress("Both models are ready for offline use.", 100)


def transcribe(home: Path, audio: Path, progress: Progress) -> dict:
    environment(home)
    ready = require_ready(home)
    import moondream as md
    import torch
    _torch_threads(torch)
    progress("Loading Parakeet Redux on CPU…", 8)
    with photon_cpu(progress, ready["asr"]) as (speech, asr_mode):
        progress("Transcribing the recording locally…", 20)
        import soundfile as sf
        duration = sf.info(str(audio)).duration
        # Progressive snapshots replace prior text. The final result is authoritative.
        stream = speech.transcribe(audio=str(audio), timestamps="word", stream=True)
        count = 0
        for update in stream:
            count += 1
            segments = update.get("segments", [])
            if segments:
                elapsed = min(duration, float(segments[-1]["end"]))
                progress(f"Transcribing locally · {timestamp(elapsed)} of {timestamp(duration)}", 20 + int(70 * elapsed / max(.01, duration)))
            else:
                progress(f"Transcribing locally · {count} updates received", -1)
        result = stream.result()
    progress("Saving word timestamps…", 95)
    return result


def diarize(home: Path, audio: Path, progress: Progress) -> list[dict]:
    environment(home)
    ready = require_ready(home)
    import torch
    import soundfile as sf
    from transformers import AutoModelForAudioFrameClassification, AutoProcessor
    _torch_threads(torch)
    progress("Loading Nemotron speaker model on CPU…", 6)
    processor = AutoProcessor.from_pretrained(ready["diarization"], local_files_only=True)
    model = AutoModelForAudioFrameClassification.from_pretrained(ready["diarization"], local_files_only=True).to("cpu").eval()
    # NVIDIA's offline-style chunk size; retained speaker_cache links identities
    # across the WHOLE meeting instead of restarting labels on every chunk.
    processor.streaming_modes["meeting"] = (340, 40)
    processor.set_streaming_mode("meeting")
    cache, pieces = None, []
    with sf.SoundFile(str(audio)) as source, torch.inference_mode():
        if source.samplerate != 16000 or source.channels != 1:
            raise ValueError("Diarization requires normalized 16 kHz mono audio.")
        frames = len(source)
        offset, mel_cursor, first = 0, 0, True
        while offset < frames:
            size = processor.num_samples_first_audio_chunk if first else processor.num_samples_per_audio_chunk
            last = offset + size >= frames
            source.seek(max(0, offset))
            chunk = source.read(min(size, frames - offset), dtype="float32")
            inputs = processor(chunk, sampling_rate=16000, is_streaming=True,
                               is_first_audio_chunk=first, is_last_audio_chunk=last, return_tensors="pt")
            outputs = model(**inputs, speaker_cache=cache)
            pieces.append(outputs.logits.cpu())
            cache = outputs.speaker_cache
            progress(f"Detecting speaker turns · {min(100, round((offset + len(chunk)) / frames * 100))}% of audio", 10 + int(80 * (offset + len(chunk)) / frames))
            if last:
                break
            mel_cursor += processor.num_mel_frames_per_step
            offset = processor.audio_chunk_start(mel_cursor)
            first = False
    decoded = processor.extract_speaker_dict(torch.cat(pieces, dim=1))[0]
    duration = frames / 16000
    intervals = [dict(start=max(0.0, float(s["Start"])), end=min(duration, float(s["End"])),
                      speaker=f"speaker_{s['Speaker']}") for s in decoded if s["End"] > s["Start"]]
    progress("Aligning speaker turns with words…", 94)
    return intervals
