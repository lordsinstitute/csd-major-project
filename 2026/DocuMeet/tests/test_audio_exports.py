import wave
from pathlib import Path

import numpy as np
from pypdf import PdfReader

from gather.audio import cut_sample, normalize_audio
from gather.domain import make_segments, new_meeting
from gather.exports import export_pdf, export_txt


def test_stereo_phone_file_is_converted_to_16khz_mono_and_sample_cut(tmp_path):
    import soundfile as sf
    source = tmp_path / "phone.flac"
    data = np.sin(2 * np.pi * 220 * np.arange(48000 * 3) / 48000) * .1
    sf.write(source, np.column_stack((data, data)), 48000)
    target = tmp_path / "meeting.wav"
    duration = normalize_audio(source, target)
    assert abs(duration - 3) < .01
    with wave.open(str(target)) as stream:
        assert (stream.getframerate(), stream.getnchannels(), stream.getsampwidth()) == (16000, 1, 2)
    cut_sample(target, tmp_path / "sample.wav", .5, 2)
    with wave.open(str(tmp_path / "sample.wav")) as stream:
        assert stream.getnframes() == 24000


def sample_meeting(count=6):
    meeting = new_meeting("Project review & next steps")
    meeting["duration"] = 3600
    meeting["speakers"] = {"s": dict(name="Alex <Team lead>", color=0)}
    words = [dict(start=i * 8, end=i * 8 + 2, word=f"We discussed task {i}. The next step is to check the prototype and share our findings.", speaker="s") for i in range(count)]
    meeting["segments"] = make_segments(words)
    return meeting


def test_txt_and_multipage_pdf_preserve_names_times_and_complete_text(tmp_path):
    meeting = sample_meeting(110)
    export_txt(meeting, tmp_path / "meeting.txt")
    export_pdf(meeting, tmp_path / "meeting.pdf")
    txt = (tmp_path / "meeting.txt").read_text("utf-8")
    pdf = PdfReader(tmp_path / "meeting.pdf")
    text = "\n".join(p.extract_text() for p in pdf.pages)
    assert len(pdf.pages) >= 3
    for token in ["Alex <Team lead>", "task 0.", "task 109.", "Draft"]:
        assert token in txt
        assert token in text
    assert "00:14:24" in text
