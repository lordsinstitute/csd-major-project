"""Real inference check. Uses a public speech fixture; never a mock model.

Usage: python scripts/verify_runtime.py --home PATH --audio PATH
Models must already be set up in PATH. External Python socket connections are denied
during inference, in addition to HF offline flags. Save results for review.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gather.storage import Store
from gather.worker import process_job
from gather.exports import export_txt, export_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/runtime"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    store = Store(args.home)
    meeting = store.create("Offline runtime verification")
    meeting["original"] = str(args.audio.resolve())
    store.save(meeting)
    process_job(store, meeting["id"], "prepare")

    import ipaddress
    external_attempts = []
    def is_loopback(address):
        if not isinstance(address, tuple):
            return True
        if address[0] == "localhost":
            return True
        try:
            return ipaddress.ip_address(address[0]).is_loopback
        except ValueError:
            return False
    original_connect = socket.socket.connect
    def local_connect(sock, address):
        # Windows asyncio uses a loopback socketpair for its internal wakeup pipe.
        if not is_loopback(address):
            external_attempts.append(str(address))
            raise RuntimeError(f"External network connection attempted: {address}")
        return original_connect(sock, address)
    socket.socket.connect = local_connect
    import threading
    import psutil
    process = psutil.Process()
    stop_monitor = threading.Event()
    peaks = dict(rss=0)
    def monitor():
        while not stop_monitor.wait(.2):
            peaks['rss'] = max(peaks['rss'], process.memory_info().rss)
    monitoring = threading.Thread(target=monitor, daemon=True)
    monitoring.start()
    timings = {}
    for stage in ["transcribe", "speakers"]:
        start = time.perf_counter()
        process_job(store, meeting["id"], stage)
        timings[stage] = round(time.perf_counter() - start, 3)
    stop_monitor.set()
    monitoring.join()
    assert not external_attempts, f"External connections were attempted: {external_attempts}"
    meeting = store.get(meeting["id"])
    export_txt(meeting, args.output / "transcript.txt")
    export_pdf(meeting, args.output / "transcript.pdf")
    report = dict(meeting_id=meeting["id"], duration=meeting["duration"], words=len(meeting["words"]),
                  speakers=len(meeting["speakers"]), segments=len(meeting["segments"]), timings=timings,
                  peak_rss_mb=round(peaks['rss'] / 1024 ** 2, 1), external_connection_attempts=external_attempts,
                  network="External Python socket connections denied; internal loopback allowed for asyncio; HF/Transformers offline flags enabled")
    (args.output / "verification.json").write_text(json.dumps(report, indent=2), "utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
