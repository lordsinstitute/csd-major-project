from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .domain import new_meeting


def default_home() -> Path:
    if os.environ.get("GATHER_HOME"):
        return Path(os.environ["GATHER_HOME"]).resolve()
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "Gather"


class Store:
    def __init__(self, home: Path | str | None = None):
        self.home = Path(home) if home else default_home()
        self.home.mkdir(parents=True, exist_ok=True)
        self.meetings_dir = self.home / "meetings"
        self.meetings_dir.mkdir(exist_ok=True)
        self.models_dir = self.home / "models"
        self.models_dir.mkdir(exist_ok=True)
        self.db = self.home / "gather.sqlite3"
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS meetings (id TEXT PRIMARY KEY, created TEXT, payload TEXT NOT NULL)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=20)
        try:
            db.execute("PRAGMA journal_mode=WAL")
            with db:
                yield db
        finally:
            db.close()

    def create(self, title: str) -> dict:
        meeting = new_meeting(title)
        self.folder(meeting["id"]).mkdir(exist_ok=True)
        self.save(meeting)
        return meeting

    def folder(self, meeting_id: str) -> Path:
        if not meeting_id or any(c not in "0123456789abcdef" for c in meeting_id):
            raise ValueError("Invalid meeting identifier")
        return self.meetings_dir / meeting_id

    def save(self, meeting: dict):
        with self.connect() as db:
            db.execute("INSERT INTO meetings VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                       (meeting["id"], meeting["created"], json.dumps(meeting, ensure_ascii=False)))

    def get(self, meeting_id: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT payload FROM meetings WHERE id=?", (meeting_id,)).fetchone()
        if row is None:
            raise KeyError(meeting_id)
        return json.loads(row[0])

    def list(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM meetings ORDER BY created DESC").fetchall()
        return [json.loads(row[0]) for row in rows]

    def settings(self) -> dict:
        path = self.home / "settings.json"
        return json.loads(path.read_text("utf-8")) if path.exists() else {}

    def set_settings(self, settings: dict):
        path = self.home / "settings.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(settings, indent=2), "utf-8")
        tmp.replace(path)
