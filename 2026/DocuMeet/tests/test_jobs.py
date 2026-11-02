import numpy as np
import soundfile as sf
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from gather.jobs import Jobs
from gather.storage import Store


def test_qprocess_runs_real_import_worker_and_delivers_progress(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path)
    source = tmp_path / "source.wav"
    sf.write(source, np.zeros(16000), 16000)
    meeting = store.create("Worker process test")
    meeting["original"] = str(source)
    store.save(meeting)
    jobs = Jobs(store.home)
    loop = QEventLoop()
    result, progress = [], []
    jobs.progress.connect(lambda msg, pct: progress.append((msg, pct)))
    jobs.finished.connect(lambda ok, msg: (result.append((ok, msg)), loop.quit()))
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(lambda: (jobs.cancel(), loop.quit()))
    timeout.start(20000)
    jobs.start("prepare", meeting["id"])
    loop.exec()
    timeout.stop()
    assert result and result[0][0], result
    assert not jobs.busy
    assert progress[-1][1] == 100
    assert store.get(meeting["id"])["status"] == "ready"
