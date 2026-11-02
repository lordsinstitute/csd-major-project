import json

import numpy as np
import pytest
import soundfile as sf

from gather.storage import Store
from gather.worker import process_job


def test_import_preserves_original_and_saves_prepared_meeting(tmp_path):
    source = tmp_path / "source.wav"
    sf.write(source, np.zeros(16000), 16000)
    store = Store(tmp_path / "data")
    meeting = store.create("Imported meeting")
    meeting["original"] = str(source)
    store.save(meeting)
    process_job(store, meeting["id"], "prepare")
    saved = store.get(meeting["id"])
    assert saved["status"] == "ready"
    assert saved["duration"] == 1
    assert saved["original"] != str(source)
    assert source.exists()


def test_failed_import_retains_source_and_records_retryable_error(tmp_path):
    source = tmp_path / "bad.wav"
    source.write_text("invalid")
    store = Store(tmp_path / "data")
    meeting = store.create("Broken import")
    meeting["original"] = str(source)
    store.save(meeting)
    with pytest.raises(ValueError):
        process_job(store, meeting["id"], "prepare")
    saved = store.get(meeting["id"])
    assert saved["status"] == "error"
    assert saved["stage"] == "prepare"
    assert not saved["audio"]
    assert source.exists()


def test_speech_error_keeps_completed_transcription(tmp_path, monkeypatch):
    from gather import engines
    store = Store(tmp_path)
    meeting = store.create("Retry")
    meeting.update(words=[dict(word="Hello", start=0, end=1)], audio="recorded.wav")
    store.save(meeting)
    def fail(*args):
        raise RuntimeError("speaker model unavailable")
    monkeypatch.setattr(engines, "diarize", fail)
    with pytest.raises(RuntimeError):
        process_job(store, meeting["id"], "speakers")
    assert store.get(meeting["id"])["words"] == meeting["words"]
