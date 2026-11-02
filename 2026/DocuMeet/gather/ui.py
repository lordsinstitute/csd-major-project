from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, QElapsedTimer
from PySide6.QtGui import QColor, QPainter, QPen, QDesktopServices, QShortcut, QKeySequence
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QSlider, QStackedWidget, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from .audio import cut_sample
from .domain import merge_speakers, reassign_segment, sample_ranges, speaker_name, timestamp
from .engines import manifest
from .exports import export_pdf, export_txt
from .jobs import Jobs
from .recording import Recorder
from .storage import Store
from .theme import STYLE

COLORS = ["#706bd4", "#349b88", "#ce8a45", "#b96588", "#5894c7", "#9271b5", "#849c50", "#bd6b52"]


def label(text, name="", wrap=False):
    obj = QLabel(text)
    obj.setTextFormat(Qt.TextFormat.PlainText)
    obj.setObjectName(name)
    obj.setWordWrap(wrap)
    return obj


def button(text, callback=None, kind="", tooltip=""):
    obj = QPushButton(text)
    obj.setObjectName(kind)
    obj.setCursor(Qt.CursorShape.PointingHandCursor)
    if callback:
        obj.clicked.connect(callback)
    if tooltip:
        obj.setToolTip(tooltip)
    return obj


def card():
    obj = QFrame()
    obj.setObjectName("card")
    layout = QVBoxLayout(obj)
    layout.setContentsMargins(24, 22, 24, 22)
    layout.setSpacing(13)
    return obj, layout


class Waveform(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = []
        self.recording = False
        self.setMinimumHeight(105)

    def add_level(self, value):
        self.values = (self.values + [value])[-130:]
        self.update()

    def load(self, path):
        import wave
        import numpy as np
        self.values = []
        if path and Path(path).exists():
            with wave.open(str(path), "rb") as source:
                frames = source.getnframes()
                for idx in range(150):
                    source.setpos(min(int(idx * frames / 150), frames))
                    data = source.readframes(min(1600, max(0, frames - source.tell())))
                    samples = np.frombuffer(data, dtype="int16").astype(float) / 32768
                    self.values.append(min(1, float(np.sqrt(np.mean(samples ** 2))) * 4) if len(samples) else 0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        values = self.values or [0] * 130
        step = self.width() / max(len(values), 1)
        painter.setPen(QPen(QColor("#b65065" if self.recording else "#8581da"), max(2, min(4, step - 2)), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        center = self.height() / 2
        for idx, value in enumerate(values):
            height = max(2, value * (self.height() - 16))
            x = int((idx + .5) * step)
            painter.drawLine(x, int(center - height / 2), x, int(center + height / 2))


class MainWindow(QMainWindow):
    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.meeting = None
        self.chain_speakers = False
        self.sample_end = None
        self.selected_segment = None
        self.setWindowTitle("DocuMeet · Local meeting workspace")
        self.resize(1360, 900)
        self.setMinimumSize(1100, 760)
        self.setStyleSheet(STYLE)
        self.jobs = Jobs(store.home, self)
        self.jobs.progress.connect(self.on_progress)
        self.jobs.finished.connect(self.on_finished)
        self.recorder = Recorder(self)
        self.recorder.level.connect(self.on_level)
        self.recorder.failed.connect(self.on_recording_error)
        self.clock = QElapsedTimer()
        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(250)
        self.clock_timer.timeout.connect(self.update_clock)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(.8)
        self.player.positionChanged.connect(self.on_position)
        self.player.durationChanged.connect(self.on_duration)
        self.player.playbackStateChanged.connect(self.on_play_state)
        self.player.errorOccurred.connect(lambda *args: self.notice("Playback: " + self.player.errorString()))
        self.media_devices = QMediaDevices(self)
        self.media_devices.audioInputsChanged.connect(self.refresh_devices)
        self._recover_interrupted()
        self._build()
        self.refresh_library()
        QShortcut(QKeySequence("Ctrl+N"), self, self.new_meeting)
        QShortcut(QKeySequence("Ctrl+O"), self, self.import_audio)
        QShortcut(QKeySequence("Ctrl+F"), self, self.focus_search)

    def _recover_interrupted(self):
        for meeting in self.store.list():
            if meeting["status"] in ("processing", "recording"):
                meeting.update(status="error", error="The previous session ended before processing finished. Your saved recording is retained; retry to continue.")
                self.store.save(meeting)

    def _build(self):
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setCentralWidget(root)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(22, 28, 22, 22)
        side.setSpacing(14)
        side.addWidget(label("◒  DocuMeet", "brand"))
        side.addWidget(label("A local meeting workspace", "muted"))
        side.addSpacing(16)
        self.new_btn = button("＋  New meeting", self.new_meeting, "primary")
        side.addWidget(self.new_btn)
        self.library_search = QLineEdit()
        self.library_search.setPlaceholderText("Search meetings…")
        self.library_search.setClearButtonEnabled(True)
        self.library_search.textChanged.connect(self.filter_library)
        side.addWidget(self.library_search)
        side.addSpacing(10)
        side.addWidget(label("YOUR MEETINGS", "eyebrow"))
        self.library = QListWidget()
        self.library.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.library.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.library.currentItemChanged.connect(self.choose_meeting)
        side.addWidget(self.library, 1)
        side.addWidget(button("◇  Offline models", self.show_models, "quiet"))
        side.addWidget(button("↗  Open local files", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.home))), "quiet"))
        side.addWidget(label("●  Audio stays on this computer", "muted", True))
        side.addWidget(label("College demo · v0.1", "muted"))
        outer.addWidget(sidebar)

        canvas = QWidget()
        canvas.setObjectName("canvas")
        column = QVBoxLayout(canvas)
        column.setContentsMargins(36, 27, 36, 22)
        column.setSpacing(16)
        top = QHBoxLayout()
        top.addWidget(label("WORKSPACE  /  MEETINGS", "eyebrow"))
        top.addStretch()
        top.addWidget(label("●  Local processing", "badge"))
        column.addLayout(top)
        self.banner = label("", "error", True)
        self.banner.hide()
        column.addWidget(self.banner)
        self.progress_box = QWidget()
        pb = QVBoxLayout(self.progress_box)
        pb.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.progress_label = label("Preparing…", "muted", True)
        row.addWidget(self.progress_label, 1)
        self.cancel_btn = button("Cancel", self.jobs.cancel)
        row.addWidget(self.cancel_btn)
        pb.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        pb.addWidget(self.progress)
        self.progress_box.hide()
        column.addWidget(self.progress_box)
        self.pages = QStackedWidget()
        column.addWidget(self.pages, 1)
        self.welcome = self.build_welcome()
        self.pages.addWidget(self.welcome)
        self.detail = self.build_detail()
        self.pages.addWidget(self.detail)
        self.models_page = self.build_models()
        self.pages.addWidget(self.models_page)
        outer.addWidget(canvas, 1)

    def build_welcome(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(0, 20, 0, 0)
        box.setSpacing(20)
        box.addWidget(label("Be present. Keep every word.", "heading"))
        box.addWidget(label("Record your next meeting or bring a recording from your phone.\nTurn the conversation into a transcript you can review, name, and keep.", "muted", True))
        box.addSpacing(16)
        row = QHBoxLayout()
        row.setSpacing(18)
        for title, number, description, action, callback in [
            ("Record a meeting", "01 / CAPTURE", "Use a connected microphone. Your recording is saved directly to this computer.", "＋  Start a new meeting", self.new_meeting),
            ("Bring a recording", "02 / IMPORT", "Transfer a voice recording from your phone, then import the audio file here.", "↥  Import audio", self.import_audio),
        ]:
            panel, layout = card()
            layout.addWidget(label(number, "eyebrow"))
            layout.addSpacing(13)
            layout.addWidget(label(title, "subheading"))
            layout.addWidget(label(description, "muted", True))
            layout.addSpacing(14)
            layout.addWidget(button(action, callback, "primary" if "Record" in title else ""))
            row.addWidget(panel, 1)
        box.addLayout(row)
        panel, layout = card()
        layout.addWidget(label("A clear path from conversation to transcript", "subheading"))
        layout.addWidget(label("1  Record or import       →       2  Transcribe locally       →       3  Listen & name speakers       →       4  Export", "muted", True))
        layout.addWidget(label("English meetings · 4–6 people · Designed for 30–60 minute recordings", "muted"))
        box.addWidget(panel)
        box.addStretch()
        box.addWidget(label("First time here? Set up the offline models before your first transcription.\nSummarization is deferred for this version.", "muted", True))
        box.addWidget(button("Set up offline models →", self.show_models, "quiet"))
        return page

    def build_detail(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(0, 5, 0, 0)
        box.setSpacing(14)
        title_row = QHBoxLayout()
        self.title_label = label("New meeting", "heading")
        self.title_label.setWordWrap(True)
        title_row.addWidget(self.title_label, 1)
        title_row.addWidget(button("Rename", self.rename_meeting))
        self.export_btn = button("Export transcript ↓", self.export_dialog)
        title_row.addWidget(self.export_btn)
        box.addLayout(title_row)
        self.meta_label = label("", "muted")
        box.addWidget(self.meta_label)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_audio_tab(), "Recording")
        self.tabs.addTab(self.build_transcript_tab(), "Transcript")
        self.tabs.addTab(self.build_speakers_tab(), "Speakers")
        summary = QWidget()
        summary.setToolTip("Summarization will be added in a later version.")
        self.tabs.addTab(summary, "Summary · Later")
        self.tabs.setTabEnabled(3, False)
        box.addWidget(self.tabs, 1)
        return page

    def build_audio_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(0, 22, 0, 0)
        box.setSpacing(16)
        panel, layout = card()
        row = QHBoxLayout()
        row.addWidget(label("MEETING AUDIO", "eyebrow"))
        row.addStretch()
        self.audio_state = label("Ready to record", "muted")
        row.addWidget(self.audio_state)
        layout.addLayout(row)
        self.clock_label = label("00:00:00", "heading")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.clock_label)
        self.wave = Waveform()
        layout.addWidget(self.wave)
        playback = QHBoxLayout()
        self.play_btn = button("▶  Play", self.toggle_play)
        playback.addWidget(self.play_btn)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.sliderMoved.connect(self.seek_audio)
        playback.addWidget(self.seek, 1)
        self.position_label = label("00:00:00 / 00:00:00", "muted")
        playback.addWidget(self.position_label)
        layout.addLayout(playback)
        box.addWidget(panel)
        row = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(240)
        self.device_combo.setAccessibleName("Recording microphone")
        row.addWidget(self.device_combo, 1)
        self.record_btn = button("●  Start recording", self.toggle_record, "primary")
        self.import_btn = button("↥  Import recording", self.import_audio)
        row.addWidget(self.record_btn)
        row.addWidget(self.import_btn)
        box.addLayout(row)
        self.audio_help = label("Place the microphone near everyone. A quiet room and clear turn-taking improve results.\nYou can also import WAV, MP3, M4A, FLAC, OGG, WebM, or MP4 recordings.", "muted", True)
        box.addWidget(self.audio_help)
        box.addStretch()
        panel, layout = card()
        row = QHBoxLayout()
        text = QVBoxLayout()
        text.addWidget(label("Ready when your meeting is.", "subheading"))
        text.addWidget(label("Generate a transcript, then listen to samples and name each speaker.", "muted", True))
        row.addLayout(text, 1)
        self.transcribe_btn = button("Transcribe meeting →", self.start_transcription, "primary")
        row.addWidget(self.transcribe_btn)
        layout.addLayout(row)
        box.addWidget(panel)
        self.prepare_btn = button("Recover / prepare saved recording", lambda: self.start_job("prepare"))
        box.addWidget(self.prepare_btn)
        self.refresh_devices()
        return page

    def build_transcript_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(0, 20, 0, 0)
        row = QHBoxLayout()
        self.transcript_search = QLineEdit()
        self.transcript_search.setPlaceholderText("Search the transcript…")
        self.transcript_search.setClearButtonEnabled(True)
        self.transcript_search.textChanged.connect(self.filter_transcript)
        row.addWidget(self.transcript_search, 1)
        self.edit_btn = button("Edit selected text", self.edit_segment)
        row.addWidget(self.edit_btn)
        box.addLayout(row)
        self.transcript_note = label("Transcribe a recording to see its words here.", "muted", True)
        box.addWidget(self.transcript_note)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["TIME", "SPEAKER", "TRANSCRIPT", "REVIEW"])
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 105)
        self.table.setColumnWidth(1, 145)
        self.table.setColumnWidth(3, 90)
        self.table.cellDoubleClicked.connect(self.play_segment)
        box.addWidget(self.table, 1)
        row = QHBoxLayout()
        row.addWidget(label("Double-click a row to listen at its timestamp.", "muted"), 1)
        self.assign_combo = QComboBox()
        self.assign_combo.setAccessibleName("Assign selected transcript row to speaker")
        row.addWidget(self.assign_combo)
        self.assign_btn = button("Assign speaker", self.assign_selected)
        row.addWidget(self.assign_btn)
        box.addLayout(row)
        return page

    def build_speakers_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(0, 20, 0, 0)
        box.setSpacing(14)
        box.addWidget(label("Put a name to each voice.", "subheading"))
        box.addWidget(label("Listen to a few samples, then enter a name. If two voices belong to one person, merge them.\nFor a mixed-up statement, select its transcript row and assign the right speaker.", "muted", True))
        self.speaker_scroll = QScrollArea()
        self.speaker_scroll.setWidgetResizable(True)
        self.speaker_container = QWidget()
        self.speaker_container.setObjectName("canvas")
        self.speaker_grid = QGridLayout(self.speaker_container)
        self.speaker_grid.setContentsMargins(0, 6, 0, 6)
        self.speaker_grid.setSpacing(15)
        self.speaker_scroll.setWidget(self.speaker_container)
        box.addWidget(self.speaker_scroll, 1)
        row = QHBoxLayout()
        self.detect_btn = button("Detect speakers", self.detect_speakers)
        row.addWidget(self.detect_btn)
        self.undo_btn = button("Undo last merge", self.undo_merge)
        row.addWidget(self.undo_btn)
        row.addStretch()
        self.review_btn = button("Finish review ✓", self.finish_review, "primary")
        row.addWidget(self.review_btn)
        box.addLayout(row)
        return page

    def build_models(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(0, 15, 0, 0)
        box.setSpacing(18)
        box.addWidget(label("Set up once. Work offline.", "heading"))
        box.addWidget(label("The models run on your computer. Setup downloads the weights and prepares the CPU runtimes.\nNo meeting recordings are uploaded. Keep an internet connection during this step.", "muted", True))
        for name, caption in [("Parakeet Redux", "SPEECH TO TEXT  /  About 178 MB of model weights"), ("Nemotron 3 Diarization", "WHO SPOKE WHEN  /  About 400 MB of model weights")]:
            panel, layout = card()
            layout.addWidget(label(caption, "eyebrow"))
            layout.addWidget(label(name, "subheading"))
            box.addWidget(panel)
        self.models_status = label("", "muted", True)
        box.addWidget(self.models_status)
        row = QHBoxLayout()
        self.setup_btn = button("Download & verify models", lambda: self.start_job("setup"), "primary")
        row.addWidget(self.setup_btn)
        row.addStretch()
        box.addLayout(row)
        box.addWidget(label("Allow several GB of disk space for the application, runtimes, models, and recordings.\nThe 5–15 minute processing window is a target; actual speed depends on your laptop.", "muted", True))
        box.addStretch()
        box.addWidget(button("← Back to meeting", self.back_to_meeting, "quiet"))
        return page

    def focus_search(self):
        if self.pages.currentWidget() == self.detail and self.tabs.currentIndex() == 1:
            self.transcript_search.setFocus()
        else:
            self.library_search.setFocus()

    def notice(self, text=""):
        self.banner.setText(text)
        self.banner.setVisible(bool(text))

    def refresh_devices(self):
        if not hasattr(self, "device_combo") or self.recorder.active:
            return
        self.device_combo.clear()
        devices = QMediaDevices.audioInputs()
        self.devices = devices
        default = QMediaDevices.defaultAudioInput()
        for idx, device in enumerate(devices):
            self.device_combo.addItem(device.description(), idx)
            if device.id() == default.id():
                self.device_combo.setCurrentIndex(idx)
        if not devices:
            self.device_combo.addItem("No microphone found — import a recording")

    def refresh_library(self):
        selected = self.meeting["id"] if self.meeting else None
        self.library.blockSignals(True)
        self.library.clear()
        for meeting in self.store.list():
            created = datetime.fromisoformat(meeting["created"]).astimezone().strftime("%d %b · %H:%M")
            item = QListWidgetItem(f"{meeting['title']}\n{created}  ·  {timestamp(meeting['duration'])}")
            item.setData(Qt.ItemDataRole.UserRole, meeting["id"])
            self.library.addItem(item)
            if selected == meeting["id"]:
                self.library.setCurrentItem(item)
        self.library.blockSignals(False)
        self.filter_library(self.library_search.text())

    def filter_library(self, text):
        for idx in range(self.library.count()):
            item = self.library.item(idx)
            item.setHidden(text.casefold() not in item.text().casefold())

    def choose_meeting(self, current, previous):
        if current and not self.recorder.active:
            self.open_meeting(current.data(Qt.ItemDataRole.UserRole))

    def new_meeting(self):
        if self.jobs.busy or self.recorder.active:
            return
        title, ok = QInputDialog.getText(self, "New meeting", "Meeting title", text=datetime.now().strftime("Meeting · %d %b"))
        if ok:
            self.meeting = self.store.create(title)
            self.refresh_library()
            self.open_meeting(self.meeting["id"])
            self.tabs.setCurrentIndex(0)

    def open_meeting(self, meeting_id):
        self.player.stop()
        self.sample_end = None
        self.meeting = self.store.get(meeting_id)
        self.player.setSource(QUrl.fromLocalFile(self.meeting["audio"]) if self.meeting["audio"] else QUrl())
        self.pages.setCurrentWidget(self.detail)
        self.refresh_detail()

    def refresh_detail(self):
        if not self.meeting:
            return
        meeting = self.meeting
        self.title_label.setText(meeting["title"])
        created = datetime.fromisoformat(meeting["created"]).astimezone().strftime("%d %B %Y · %I:%M %p")
        state = {"empty": "New meeting", "ready": "Audio ready", "recording": "Recording", "processing": "Processing", "transcribed": "Transcript ready", "review": "Speaker review", "complete": "Reviewed", "error": "Needs attention"}.get(meeting["status"], meeting["status"])
        self.meta_label.setText(f"{created}    /    {timestamp(meeting['duration'])}    /    {state}")
        self.audio_state.setText("Recording saved locally" if meeting["audio"] else "Ready to record")
        self.clock_label.setText(timestamp(meeting["duration"]))
        self.wave.load(meeting["audio"])
        self.notice(meeting.get("error", ""))
        self.refresh_transcript()
        self.refresh_speakers()
        self.update_controls()

    def update_controls(self):
        busy, recording = self.jobs.busy, self.recorder.active
        locked = busy or recording
        meeting = self.meeting or {}
        self.new_btn.setEnabled(not locked)
        self.library.setEnabled(not locked)
        self.import_btn.setEnabled(not locked and not meeting.get("original"))
        self.record_btn.setEnabled(not busy and (recording or not meeting.get("original")) and bool(self.devices))
        self.device_combo.setEnabled(not locked)
        self.transcribe_btn.setEnabled(not locked and bool(meeting.get("audio")))
        self.transcribe_btn.setText("Review transcript →" if meeting.get("speakers") else "Transcribe meeting →")
        self.play_btn.setEnabled(not recording and bool(meeting.get("audio")))
        self.seek.setEnabled(not recording and bool(meeting.get("audio")))
        self.export_btn.setEnabled(not locked and bool(meeting.get("segments")))
        self.setup_btn.setEnabled(not locked)
        self.prepare_btn.setVisible(bool(meeting.get("original")) and not meeting.get("audio"))
        self.prepare_btn.setEnabled(not locked)
        self.detect_btn.setEnabled(not locked and bool(meeting.get("words")))
        self.undo_btn.setEnabled(not locked and bool(meeting.get("undo_merge")))
        self.detect_btn.setText("Detect speakers again" if meeting.get("speakers") else "Detect speakers")
        self.review_btn.setEnabled(not locked and bool(meeting.get("speakers")))
        self.assign_btn.setEnabled(not locked and bool(meeting.get("speakers")))
        self.edit_btn.setEnabled(not locked and bool(meeting.get("segments")))
        self.table.setEnabled(not locked)
        self.speaker_container.setEnabled(not locked)

    def import_audio(self):
        if self.jobs.busy or self.recorder.active:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import a meeting recording", "", "Recordings (*.wav *.mp3 *.m4a *.flac *.ogg *.aac *.webm *.mp4 *.mov *.mkv);;All files (*)")
        if not path:
            return
        if not self.meeting or self.meeting.get("original"):
            self.meeting = self.store.create(Path(path).stem)
        self.meeting["original"] = path
        self.store.save(self.meeting)
        self.refresh_library()
        self.open_meeting(self.meeting["id"])
        self.tabs.setCurrentIndex(0)
        self.start_job("prepare")

    def toggle_record(self):
        if self.recorder.active:
            self.stop_recording()
            return
        if not self.meeting or not self.devices:
            return
        try:
            self.player.stop()
            path = self.store.folder(self.meeting["id"]) / "capture.pcm"
            raw = self.recorder.start(self.devices[self.device_combo.currentIndex()], path)
            self.meeting.update(original=str(path), raw=raw, status="recording")
            self.store.save(self.meeting)
            self.wave.values = []
            self.wave.recording = True
            self.record_btn.setText("■  Stop & save recording")
            self.record_btn.setObjectName("danger")
            self.record_btn.setStyleSheet("background:#b5495b;color:white;")
            self.clock.start()
            self.clock_timer.start()
            self.audio_state.setText("● Recording · saved continuously")
            self.notice("")
            self.update_controls()
        except Exception as exc:
            self.recorder.stop()
            self.notice(str(exc))

    def stop_recording(self):
        self.recorder.stop()
        self.clock_timer.stop()
        self.wave.recording = False
        self.record_btn.setText("●  Start recording")
        self.record_btn.setObjectName("primary")
        self.record_btn.setStyleSheet("")
        self.meeting["duration"] = self.clock.elapsed() / 1000
        self.store.save(self.meeting)
        self.start_job("prepare")

    def on_recording_error(self, message):
        if self.recorder.active:
            self.stop_recording()
        self.notice(message)

    def on_level(self, value):
        self.wave.add_level(value)

    def update_clock(self):
        self.clock_label.setText(timestamp(self.clock.elapsed() / 1000))

    def start_job(self, job):
        if self.jobs.busy or self.recorder.active:
            return
        self.notice("")
        self.progress_box.show()
        self.progress_label.setText("Preparing…")
        self.progress.setRange(0, 0)
        self.jobs.start(job, self.meeting["id"] if job != "setup" and self.meeting else None)
        self.update_controls()

    def on_progress(self, message, percent):
        self.progress_label.setText(message)
        self.progress.setRange(0, 100 if percent >= 0 else 0)
        if percent >= 0:
            self.progress.setValue(percent)

    def on_finished(self, success, message):
        job, meeting_id = self.jobs.job, self.jobs.meeting_id
        self.progress_box.hide()
        if meeting_id:
            meeting = self.store.get(meeting_id)
            if not success:
                meeting.update(status="error", error=message or "The worker stopped unexpectedly. You can retry.")
                self.store.save(meeting)
            if self.meeting and self.meeting["id"] == meeting_id:
                self.meeting = meeting
                self.player.setSource(QUrl.fromLocalFile(meeting["audio"]) if meeting["audio"] else QUrl())
                self.refresh_detail()
        elif not success:
            self.notice(message or "Model setup failed. Check the connection and retry; cached downloads will be reused.")
        self.refresh_library()
        self.refresh_model_status()
        self.update_controls()
        if success and job == "transcribe" and self.chain_speakers:
            self.chain_speakers = False
            self.start_job("speakers")
        elif success and job == "speakers":
            self.pages.setCurrentWidget(self.detail)
            self.tabs.setCurrentIndex(2)
        elif success and job == "setup":
            self.notice("")
        elif not success:
            self.chain_speakers = False

    def start_transcription(self):
        if self.meeting.get("speakers"):
            self.tabs.setCurrentIndex(1)
            return
        if not manifest(self.store.home):
            self.show_models()
            self.notice("Set up the offline models, then return to your meeting and click Transcribe.")
            return
        self.chain_speakers = True
        if self.meeting["words"]:
            self.chain_speakers = False
            self.start_job("speakers")
        else:
            self.start_job("transcribe")

    def detect_speakers(self):
        if not manifest(self.store.home):
            self.show_models()
            return
        if self.meeting.get("speakers"):
            result = QMessageBox.question(self, "Detect speakers again?", "This replaces speaker names, merges, transcript edits, and assignment corrections. The saved audio is retained.")
            if result != QMessageBox.StandardButton.Yes:
                return
        self.start_job("speakers")

    def refresh_transcript(self):
        meeting = self.meeting
        self.table.setRowCount(0)
        self.assign_combo.clear()
        self.assign_combo.addItem("Unassigned", "unknown")
        for sid, speaker in meeting["speakers"].items():
            self.assign_combo.addItem(speaker["name"], sid)
        segments = meeting["segments"]
        self.table.setRowCount(len(segments))
        for row, segment in enumerate(segments):
            cells = [timestamp(segment["start"]), speaker_name(meeting, segment["speaker"]), segment["text"], "Overlap" if segment.get("overlap") else ""]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, segment["id"])
                if col == 1 and segment["speaker"] in meeting["speakers"]:
                    item.setForeground(QColor(COLORS[meeting["speakers"][segment["speaker"]]["color"]]))
                if col == 3 and text:
                    item.setForeground(QColor("#ad7441"))
                    item.setToolTip("More than one voice was active. A single-channel transcript may omit simultaneous words; listen and correct this row.")
                self.table.setItem(row, col, item)
        self.table.resizeRowsToContents()
        for row in range(len(segments)):
            self.table.setRowHeight(row, max(60, self.table.rowHeight(row)))
        self.filter_transcript(self.transcript_search.text())
        if not segments:
            message = "Transcribe a recording to see its words here."
        elif not meeting["speakers"]:
            message = "Words are saved. Detect speakers to assign names."
        elif meeting["reviewed"]:
            message = "✓ Reviewed transcript. Changes to names or assignments reopen the review."
        else:
            message = "Draft transcript · Name the voices in Speakers, then check uncertain statements."
        self.transcript_note.setText(message)

    def filter_transcript(self, text):
        for row in range(self.table.rowCount()):
            content = " ".join(self.table.item(row, col).text() for col in (1, 2))
            self.table.setRowHidden(row, text.casefold() not in content.casefold())

    def refresh_speakers(self):
        self.speaker_fields = {}
        for row in range(self.speaker_grid.rowCount()):
            self.speaker_grid.setRowStretch(row, 0)
        while self.speaker_grid.count():
            item = self.speaker_grid.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        speakers = self.meeting["speakers"]
        if not speakers:
            self.speaker_grid.addWidget(label("Detected voices will appear here after transcription and speaker detection.", "muted", True), 0, 0)
            return
        for idx, (sid, speaker) in enumerate(speakers.items()):
            panel, layout = card()
            top = QHBoxLayout()
            avatar = label(f"●  VOICE {idx + 1:02d}", "eyebrow")
            avatar.setStyleSheet(f"color: {COLORS[speaker['color']]};")
            top.addWidget(avatar)
            top.addStretch()
            duration = sum(s["end"] - s["start"] for s in self.meeting["intervals"] if s["speaker"] == sid)
            top.addWidget(label(timestamp(duration) + " speaking", "muted"))
            layout.addLayout(top)
            field = QLineEdit(speaker["name"])
            field.setObjectName("speaker-name-" + sid)
            self.speaker_fields[sid] = field
            field.setPlaceholderText("Enter this person's name")
            field.setAccessibleName(f"Name for voice {idx + 1}")
            field.editingFinished.connect(lambda key=sid, widget=field: self.save_speaker_name(key, widget.text()))
            layout.addWidget(field)
            samples = sample_ranges(self.meeting["intervals"], sid)
            mixed_sample = False
            if not samples:
                fragments = sorted([i for i in self.meeting['intervals'] if i['speaker'] == sid],
                                   key=lambda i: i['end'] - i['start'], reverse=True)
                if fragments:
                    fragment = fragments[0]
                    samples = [(max(0, fragment['start'] - .3), min(self.meeting['duration'], fragment['end'] + .3))]
                    mixed_sample = True
            row = QHBoxLayout()
            for n, (start, end) in enumerate(samples):
                row.addWidget(button(f"▶ {n + 1} · {end-start:.0f}s", lambda checked=False, a=start, b=end: self.play_range(a, b), tooltip=f"Voice sample {n + 1}: {timestamp(start)} – {timestamp(end)}"))
            if not samples:
                row.addWidget(label("No clean sample. Listen in the transcript.", "muted", True))
            layout.addLayout(row)
            if mixed_sample:
                layout.addWidget(label("Short or overlapping voice. Sample includes surrounding audio; check it in context.", "muted", True))
            merge = QHBoxLayout()
            combo = QComboBox()
            combo.setAccessibleName(f"Merge voice {idx + 1} into")
            combo.addItem("Same person as…", "")
            for other_id, other in speakers.items():
                if other_id != sid:
                    combo.addItem(other["name"], other_id)
            merge.addWidget(combo, 1)
            merge.addWidget(button("Merge", lambda checked=False, source=sid, picker=combo: self.merge_voice(source, picker.currentData())))
            layout.addLayout(merge)
            self.speaker_grid.addWidget(panel, idx // 2, idx % 2)
            panel.show()
        self.speaker_grid.setRowStretch((len(speakers) + 1) // 2, 1)

    def save_speaker_name(self, sid, name):
        if sid not in self.meeting["speakers"]:
            return
        name = name.strip() or self.meeting["speakers"][sid]["name"]
        field = self.speaker_fields.get(sid)
        if field:
            field.setText(name)
        if name != self.meeting["speakers"][sid]["name"]:
            self.meeting["speakers"][sid]["name"] = name
            self.meeting.pop("undo_merge", None)
            self.meeting["reviewed"] = False
            self.meeting["status"] = "review"
            self.store.save(self.meeting)
            self.refresh_transcript()
            self.update_controls()
            QTimer.singleShot(0, self.refresh_speakers)

    def merge_voice(self, source, target):
        if not target:
            self.notice("Choose which voice belongs to the same person, then click Merge.")
            return
        # Keep the pre-merge state for a reversible correction.
        import json
        self.meeting["undo_merge"] = json.loads(json.dumps({key: self.meeting[key] for key in ("speakers", "segments", "words", "intervals")}))
        merge_speakers(self.meeting, source, target)
        self.meeting["status"] = "review"
        self.store.save(self.meeting)
        self.refresh_detail()
        self.notice("Voices merged. Use Undo last merge if these were different people.")

    def undo_merge(self):
        if self.meeting and self.meeting.get("undo_merge"):
            self.meeting.update(self.meeting.pop("undo_merge"))
            self.meeting.update(reviewed=False, status="review")
            self.store.save(self.meeting)
            self.refresh_detail()
            self.notice("Last merge undone.")

    def assign_selected(self):
        row = self.table.currentRow()
        if row < 0:
            self.notice("Select a transcript row first.")
            return
        reassign_segment(self.meeting, self.meeting["segments"][row]["id"], self.assign_combo.currentData())
        self.meeting.pop("undo_merge", None)
        self.meeting["status"] = "review"
        self.store.save(self.meeting)
        self.refresh_transcript()
        self.update_controls()

    def edit_segment(self):
        row = self.table.currentRow()
        if row < 0:
            self.notice("Select a transcript row to edit its text.")
            return
        segment = self.meeting["segments"][row]
        dialog = QDialog(self)
        dialog.setWindowTitle("Correct transcript text")
        dialog.resize(560, 300)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label("Correct words while keeping this statement's audio timestamps.", "muted", True))
        editor = QTextEdit()
        editor.setPlainText(segment["text"])
        layout.addWidget(editor)
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(dialog.accept)
        controls.rejected.connect(dialog.reject)
        layout.addWidget(controls)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            segment["text"] = editor.toPlainText().strip()
            self.meeting.pop("undo_merge", None)
            self.meeting["reviewed"] = False
            self.meeting["status"] = "review" if self.meeting["speakers"] else "transcribed"
            self.store.save(self.meeting)
            self.refresh_transcript()
            self.update_controls()

    def finish_review(self):
        self.meeting.pop("undo_merge", None)
        self.meeting.update(reviewed=True, status="complete")
        self.store.save(self.meeting)
        self.refresh_detail()
        self.tabs.setCurrentIndex(1)
        self.notice("")

    def rename_meeting(self):
        if not self.meeting or self.jobs.busy or self.recorder.active:
            return
        title, ok = QInputDialog.getText(self, "Rename meeting", "Meeting title", text=self.meeting["title"])
        if ok and title.strip():
            self.meeting["title"] = title.strip()
            self.store.save(self.meeting)
            self.title_label.setText(title.strip())
            self.refresh_library()

    def toggle_play(self):
        self.sample_end = None
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def play_range(self, start, end):
        self.sample_end = round(end * 1000)
        self.player.setPosition(round(start * 1000))
        self.player.play()

    def play_segment(self, row, col):
        segment = self.meeting["segments"][row]
        self.play_range(segment["start"], segment["end"])

    def seek_audio(self, position):
        self.sample_end = None
        self.player.setPosition(position)

    def on_position(self, value):
        if hasattr(self, "seek"):
            if not self.seek.isSliderDown():
                self.seek.setValue(value)
            self.position_label.setText(f"{timestamp(value / 1000)} / {timestamp(self.player.duration() / 1000)}")
        if self.sample_end is not None and value >= self.sample_end:
            self.sample_end = None
            self.player.pause()

    def on_duration(self, value):
        if hasattr(self, "seek"):
            self.seek.setRange(0, value)
            self.on_position(self.player.position())

    def on_play_state(self, state):
        if hasattr(self, "play_btn"):
            self.play_btn.setText("Ⅱ  Pause" if state == QMediaPlayer.PlaybackState.PlayingState else "▶  Play")

    def export_dialog(self):
        if not self.meeting or not self.meeting["segments"]:
            return
        choice, ok = QInputDialog.getItem(self, "Export transcript", "Choose a format", ["Text (.txt)", "PDF (.pdf)"], 0, False)
        if not ok:
            return
        import re
        stem = re.sub(r'[<>:"/\\|?*]', "-", self.meeting["title"]).strip(". ") or "transcript"
        extension = ".pdf" if choice.startswith("PDF") else ".txt"
        path, _ = QFileDialog.getSaveFileName(self, "Save transcript", stem + extension, f"{'PDF' if extension == '.pdf' else 'Text'} (*{extension})")
        if path:
            if not path.lower().endswith(extension):
                path += extension
            try:
                (export_pdf if extension == ".pdf" else export_txt)(self.meeting, path)
                self.notice("")
                QMessageBox.information(self, "Transcript saved", f"Your transcript has been saved to:\n{path}")
            except Exception as exc:
                self.notice("Export failed: " + str(exc))

    def show_models(self):
        self.refresh_model_status()
        self.pages.setCurrentWidget(self.models_page)

    def refresh_model_status(self):
        ready = manifest(self.store.home)
        self.models_status.setText(f"✓ Both models have been downloaded and verified.\nASR execution: {ready.get('asr_mode', 'CPU')}. Meeting processing works offline." if ready else "Models are not installed yet. Downloads can be retried if interrupted.")

    def back_to_meeting(self):
        self.pages.setCurrentWidget(self.detail if self.meeting else self.welcome)

    def closeEvent(self, event):
        if self.recorder.active:
            answer = QMessageBox.question(self, "Save recording before closing?", "Stop and save your recording before closing DocuMeet? Choose No to keep recording.")
            if answer == QMessageBox.StandardButton.Yes:
                self.stop_recording()
            event.ignore()
            return
        if self.jobs.busy:
            answer = QMessageBox.question(self, "Processing is running", "Cancel processing and close? Saved audio and completed stages will be kept.")
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.jobs.cancel()
            self.jobs.process.waitForFinished(3000) if self.jobs.process else None
        self.player.stop()
        event.accept()
