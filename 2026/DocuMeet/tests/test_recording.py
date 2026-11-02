import numpy as np
from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtWidgets import QApplication

from gather.audio import normalize_audio
from gather.recording import Recorder


def test_capture_stream_writes_all_pcm_bytes_and_normalizes(tmp_path):
    app = QApplication.instance() or QApplication([])
    recorder = Recorder()
    pcm = (np.sin(2 * np.pi * 220 * np.arange(96000) / 48000) * 1000).astype("int16").tobytes()
    buffer = QBuffer()
    buffer.setData(QByteArray(pcm))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    recorder.stream = buffer
    recorder.dtype = "int16"
    path = tmp_path / "capture.pcm"
    recorder.file = path.open("wb")
    levels = []
    recorder.level.connect(levels.append)
    recorder._consume()
    recorder.stop()
    assert path.read_bytes() == pcm
    assert levels and 0 < levels[0] < 1
    duration = normalize_audio(path, tmp_path / "audio.wav", dict(format="s16le", rate=48000, channels=1))
    assert duration == 2
