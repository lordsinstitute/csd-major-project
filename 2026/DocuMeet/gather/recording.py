from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSource


class Recorder(QObject):
    level = Signal(float)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source = None
        self.stream = None
        self.file = None
        self.raw_format = None

    @property
    def active(self):
        return self.source is not None

    def start(self, device, path: Path) -> dict:
        import numpy as np
        if device.isNull():
            raise RuntimeError("No microphone is available. Connect one or import a phone recording.")
        fmt = QAudioFormat()
        fmt.setSampleRate(48000)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        if not device.isFormatSupported(fmt):
            fmt = device.preferredFormat()
        formats = {QAudioFormat.SampleFormat.Int16: ("s16le", "int16"),
                   QAudioFormat.SampleFormat.Int32: ("s32le", "int32"),
                   QAudioFormat.SampleFormat.Float: ("f32le", "float32"),
                   QAudioFormat.SampleFormat.UInt8: ("u8", "uint8")}
        if fmt.sampleFormat() not in formats:
            raise RuntimeError("This microphone's audio format is unsupported. Please choose another microphone.")
        encoding, self.dtype = formats[fmt.sampleFormat()]
        self.raw_format = dict(format=encoding, rate=fmt.sampleRate(), channels=fmt.channelCount())
        self.file = path.open("wb")
        self.source = QAudioSource(device, fmt, self)
        self.source.stateChanged.connect(self._state)
        self.stream = self.source.start()
        if self.stream is None or self.source.error() != QAudio.Error.NoError:
            self.stop()
            raise RuntimeError("Cannot access the microphone. Check Windows microphone permissions and device selection.")
        self.stream.readyRead.connect(self._consume)
        return self.raw_format

    def _consume(self):
        if self.stream is None or self.file is None:
            return
        import numpy as np
        data = bytes(self.stream.readAll())
        self.file.write(data)
        # Flush continuously so interrupted recordings can be recovered.
        self.file.flush()
        size = np.dtype(self.dtype).itemsize
        if len(data) >= size:
            values = np.frombuffer(data[:len(data) // size * size], dtype=self.dtype).astype(float)
            if self.dtype == "uint8":
                values = (values - 128) / 128
            elif self.dtype != "float32":
                values /= np.iinfo(self.dtype).max
            self.level.emit(float(min(1, np.sqrt(np.mean(values ** 2)) * 3)))

    def _state(self, state):
        if self.source and self.source.error() not in (QAudio.Error.NoError, QAudio.Error.UnderrunError):
            self.failed.emit("Microphone capture stopped unexpectedly. The audio received so far has been preserved.")

    def stop(self):
        source = self.source
        if source:
            source.stateChanged.disconnect(self._state)
            self._consume()
            source.stop()
            self._consume()
            self.source = None
            source.deleteLater()
        self.stream = None
        if self.file:
            self.file.close()
            self.file = None
        return self.raw_format
