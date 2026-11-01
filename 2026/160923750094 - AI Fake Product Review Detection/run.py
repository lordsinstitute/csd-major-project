import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def skip_email_question():
    """Streamlit asks for an email the first time. This stops that question."""
    cred = Path.home() / ".streamlit" / "credentials.toml"
    if not cred.exists():
        cred.parent.mkdir(parents=True, exist_ok=True)
        cred.write_text('[general]\nemail = ""\n')


def launch():
    skip_email_question()
    cmd = [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
           "--browser.gatherUsageStats=false"]
    print("Starting TrustLens... your browser will open by itself.")
    print("To stop the website, press Ctrl + C in this terminal.")
    try:
        subprocess.run(cmd, cwd=str(ROOT))
    except KeyboardInterrupt:
        print("TrustLens stopped.")


if __name__ == "__main__":
    launch()
