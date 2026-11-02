from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal

from .worker import PREFIX


class Jobs(QObject):
    progress = Signal(str, int)
    finished = Signal(bool, str)

    def __init__(self, home: Path, parent=None):
        super().__init__(parent)
        self.home = home
        self.process = None
        self.buffer = ""
        self.errors = ""
        self.cancelled = False
        self.last_error = ""
        self.meeting_id = None
        self.job = ""

    @property
    def busy(self):
        return self.process is not None

    def start(self, job: str, meeting_id: str | None = None):
        if self.busy:
            raise RuntimeError("Another task is already running.")
        self.job, self.meeting_id = job, meeting_id
        self.buffer = self.errors = self.last_error = ""
        self.cancelled = False
        self.process = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PYTHONUTF8", "1")
        self.process.setProcessEnvironment(env)
        args = ["--worker", job] if getattr(sys, "frozen", False) else ["-m", "gather.worker", job]
        args += ["--home", str(self.home)]
        if meeting_id:
            args += ["--meeting", meeting_id]
        self.process.setWorkingDirectory(str(Path(__file__).resolve().parent.parent))
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.readyReadStandardError.connect(self._stderr)
        self.process.finished.connect(self._done)
        self.process.errorOccurred.connect(self._error)
        program = sys.executable
        if getattr(sys, "frozen", False):
            program = str(Path(sys.executable).with_name("DocuMeetWorker.exe"))
        elif Path(program).name.lower() == "pythonw.exe":
            program = str(Path(program).with_name("python.exe"))
        self.process.start(program, args)

    def _read(self):
        self.buffer += bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if PREFIX in line:
                try:
                    event = json.loads(line.split(PREFIX, 1)[1])
                    if event["kind"] == "error":
                        self.last_error = event["message"]
                    self.progress.emit(event["message"], event["percent"])
                except (ValueError, KeyError):
                    pass

    def _stderr(self):
        self.errors = (self.errors + bytes(self.process.readAllStandardError()).decode("utf-8", "replace"))[-30000:]

    def _error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.last_error = "Could not start the processing worker. Check the application installation."
            self._done(1, QProcess.ExitStatus.CrashExit)

    def _done(self, code, status):
        if not self.process:
            return
        self._read()
        self._stderr()
        (self.home / "last-worker.log").write_text(self.errors, "utf-8")
        self.process.deleteLater()
        self.process = None
        message = "Processing cancelled. Saved audio and completed stages are retained." if self.cancelled else self.last_error or self.errors[-1500:]
        self.finished.emit(code == 0 and not self.cancelled, message)

    def cancel(self):
        if self.process:
            self.cancelled = True
            self.process.kill()
