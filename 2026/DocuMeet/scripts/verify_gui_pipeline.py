"""Exercise the GUI's actual import -> QProcess -> ASR -> speakers chain.

The file picker is supplied a public fixture path so the test is repeatable.
Model inference, worker processes, persistence, corrections and exports are real.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import argparse
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PySide6.QtCore import QTimer, QCoreApplication, QEvent
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QFileDialog
from gather.storage import Store
from gather.ui import MainWindow
from gather.exports import export_pdf, export_txt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    args = parser.parse_args()
    app = QApplication([])
    for font in ['segoeui.ttf', 'seguisb.ttf', 'seguisym.ttf']:
        QFontDatabase.addApplicationFont('C:/Windows/Fonts/' + font)
    window = MainWindow(Store(args.home))
    output = Path('output/gui-runtime')
    output.mkdir(parents=True, exist_ok=True)
    window.show()
    state = dict(stage='import', ok=False)

    def start():
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(args.audio.resolve()), '')):
            window.import_audio()

    def done(ok, message):
        if not ok:
            state.update(error=message)
            app.exit(1)
            return
        # MainWindow.on_finished is connected first and may already have chained
        # the speakers process; rely on the persisted meeting status, not job text.
        if state['stage'] == 'import':
            state['stage'] = 'transcribing'
            QTimer.singleShot(100, window.start_transcription)
        elif window.meeting.get('speakers'):
            state['stage'] = 'review'
            QTimer.singleShot(100, review)

    def review():
        try:
            meeting = window.meeting
            ids = list(meeting['speakers'])
            assert len(ids) >= 2
            window.save_speaker_name(ids[0], 'Participant A')
            window.merge_voice(ids[-1], ids[0])
            assert len(window.meeting['speakers']) == len(ids) - 1
            window.undo_merge()
            assert len(window.meeting['speakers']) == len(ids)
            window.table.selectRow(0)
            window.assign_combo.setCurrentIndex(1)
            window.assign_selected()
            window.finish_review()
            window.tabs.setCurrentIndex(2)
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
            visible_cards = [window.speaker_grid.itemAt(i).widget() for i in range(window.speaker_grid.count())]
            assert sum(bool(card and card.isVisible()) for card in visible_cards) == len(ids)
            window.grab().save(str(output / 'speakers.png'))
            window.tabs.setCurrentIndex(1)
            app.processEvents()
            window.grab().save(str(output / 'transcript.png'))
            export_txt(window.meeting, output / 'transcript.txt')
            export_pdf(window.meeting, output / 'transcript.pdf')
            saved = Store(args.home).get(meeting['id'])
            assert saved['reviewed'] and saved['speakers'][ids[0]]['name'] == 'Participant A'
            state.update(ok=True, meeting_id=meeting['id'], words=len(saved['words']), speakers=len(ids))
            app.quit()
        except Exception as exc:
            state.update(error=repr(exc))
            app.exit(1)

    window.jobs.finished.connect(done)
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(lambda: (state.update(error='GUI pipeline timed out'), window.jobs.cancel(), app.exit(2)))
    deadline.start(300000)
    QTimer.singleShot(200, start)
    result = app.exec()
    (output / 'verification.json').write_text(json.dumps(state, indent=2), 'utf-8')
    print(json.dumps(state, indent=2))
    return result


if __name__ == '__main__':
    raise SystemExit(main())
