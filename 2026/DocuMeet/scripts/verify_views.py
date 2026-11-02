"""Render populated Qt views with explicitly labeled synthetic UI fixtures."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
import numpy as np
import soundfile as sf

from gather.domain import make_segments
from gather.storage import Store
from gather.ui import MainWindow

app = QApplication([])
QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
QFontDatabase.addApplicationFont('C:/Windows/Fonts/seguisb.ttf')
QFontDatabase.addApplicationFont('C:/Windows/Fonts/seguisym.ttf')
store = Store(Path(".data/ui-verification"))
m = store.create("Interface test · Six-person project review")
names = ["Alex", "Priya", "Sam", "Jordan", "Taylor", "Morgan"]
m["speakers"] = {f"s{i}": dict(name=name, color=i) for i, name in enumerate(names)}
m["intervals"] = [dict(start=i * 5, end=i * 5 + 4, speaker=f"s{i % 6}") for i in range(18)]
m["words"] = [dict(start=i * 5, end=i * 5 + 4, speaker=f"s{i % 6}", word="This is a synthetic statement used to verify the interface layout and speaker corrections.") for i in range(18)]
m["segments"] = make_segments(m["words"])
m.update(duration=90, status="review", audio=str(store.folder(m["id"]) / "meeting.wav"))
sf.write(m["audio"], np.zeros(90 * 16000, dtype=np.float32), 16000)
store.save(m)
window = MainWindow(store)
window.open_meeting(m["id"])
window.refresh_library()
window.resize(1200, 850)
window.show()
output = Path("output/views")
output.mkdir(parents=True, exist_ok=True)


def render():
    for index, name in [(0, "recording"), (1, "transcript"), (2, "speakers")]:
        window.tabs.setCurrentIndex(index)
        app.processEvents()
        window.grab().save(str(output / f"{name}.png"))
    window.show_models()
    app.processEvents()
    window.grab().save(str(output / "models.png"))
    app.quit()


QTimer.singleShot(1000, render)
app.exec()
