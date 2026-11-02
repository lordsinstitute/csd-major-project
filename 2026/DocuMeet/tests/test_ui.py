import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from gather.storage import Store
from gather.ui import MainWindow


def test_window_empty_and_saved_meeting_views(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path)
    window = MainWindow(store)
    assert window.pages.currentWidget() == window.welcome
    meeting = store.create("Weekly review")
    window.open_meeting(meeting["id"])
    assert window.title_label.text() == "Weekly review"
    assert not window.export_btn.isEnabled()
    assert not window.transcribe_btn.isEnabled()
    assert not window.tabs.isTabEnabled(3)
    window.close()


def test_speaker_names_merge_undo_and_review_persist(tmp_path):
    from gather.domain import make_segments
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path)
    meeting = store.create("Speaker review test")
    meeting["speakers"] = {"a": dict(name="Voice 1", color=0), "b": dict(name="Voice 2", color=1)}
    meeting["intervals"] = [dict(start=0, end=3, speaker="a"), dict(start=4, end=7, speaker="b")]
    meeting["words"] = [dict(word="Hello", start=0, end=1, speaker="a"), dict(word="Again", start=4, end=5, speaker="b")]
    meeting["segments"] = make_segments(meeting["words"])
    store.save(meeting)
    window = MainWindow(store)
    window.open_meeting(meeting["id"])
    window.save_speaker_name("a", "Alex")
    assert store.get(meeting["id"])["speakers"]["a"]["name"] == "Alex"
    window.merge_voice("b", "a")
    assert len(store.get(meeting["id"])["speakers"]) == 1
    assert window.undo_btn.isEnabled()
    window.undo_merge()
    assert len(store.get(meeting["id"])["speakers"]) == 2
    window.finish_review()
    assert store.get(meeting["id"])["reviewed"]
    window.close()


def test_interrupted_recording_is_recoverable(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path)
    meeting = store.create("Interrupted")
    meeting.update(status="recording", original=str(store.folder(meeting["id"]) / "capture.pcm"))
    store.save(meeting)
    window = MainWindow(store)
    window.open_meeting(meeting["id"])
    assert store.get(meeting["id"])["status"] == "error"
    assert window.prepare_btn.isEnabled()
    assert "retained" in window.banner.text()
    window.close()
