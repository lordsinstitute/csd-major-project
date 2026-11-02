from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main():
    # A frozen executable launches itself for workers; no GUI or Qt imported there.
    if "--worker" in sys.argv:
        sys.argv.remove("--worker")
        from .worker import main as worker_main
        return worker_main()
    parser = argparse.ArgumentParser(description="DocuMeet offline meeting workspace")
    parser.add_argument("--home", type=Path, help="Custom local data folder")
    parser.add_argument("--smoke-screenshot", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from .storage import Store
    from .ui import MainWindow
    app = QApplication(sys.argv[:1])
    app.setApplicationName("DocuMeet")
    app.setOrganizationName("DocuMeet")
    window = MainWindow(Store(args.home))
    window.show()
    if args.smoke_screenshot:
        def capture():
            args.smoke_screenshot.parent.mkdir(parents=True, exist_ok=True)
            window.grab().save(str(args.smoke_screenshot))
            app.quit()
        QTimer.singleShot(1200, capture)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
