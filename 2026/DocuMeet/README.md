# DocuMeet

A native Windows meeting workspace built with **Python + PySide6 (Qt)**.
Record or import a meeting, transcribe it offline with **Parakeet Redux**, detect
voices with **NVIDIA Nemotron 3 Diarization**, name/merge speakers, and export a
timestamped transcript as TXT or PDF.

**Summarization is intentionally deferred.** The Summary tab is disabled.

## Start on this computer

Double-click **Launch DocuMeet.cmd**. The project environment must first be installed
with **Setup DocuMeet.cmd** if `.venv` is missing or incomplete.

From PowerShell:

```powershell
.\.venv\Scripts\python.exe -m gather
```

## Install from source on another Windows computer

1. Install 64-bit Python 3.12 or 3.13 from https://www.python.org/downloads/windows/.
2. Copy this project and double-click **Setup DocuMeet.cmd**.
3. Double-click **Launch DocuMeet.cmd**.
4. Open **Offline models**, select **Download & verify models**, and let setup finish.
5. Recording, importing, transcription, speaker review and exports then work locally.

Setup downloads Python dependencies and model weights. The first setup needs an
internet connection and several GB of free disk space. It does not send meeting
recordings to a server. Office security policies may require your IT department to
allow the installation. No GPU is required by the configured CPU adapters.

## Meeting workflow

1. Select **New meeting**, give it a title, choose a microphone, then **Start recording**.
2. Select **Stop & save recording** when the meeting ends. Alternatively, import a
   recording transferred from a phone. WAV, MP3, M4A, FLAC and common video/audio
   containers are accepted through a bundled FFmpeg executable.
3. Select **Transcribe meeting**. Parakeet generates word timings; Nemotron then
   generates speaker activity intervals in a separate process.
4. In **Speakers**, play samples and enter names. Use **Same person as… → Merge**
   when one person has multiple detected identities.
5. In **Transcript**, double-click a row to listen. Select a row to correct its
   speaker or edit the text. Search filters by words or speaker name.
6. Select **Finish review**, then **Export transcript** and choose TXT or PDF.

The latest speaker merge can be undone with **Undo last merge**, until another
correction is saved or review is finished. Draft transcripts can also be exported;
their review status is included in the output. Re-running speaker detection
replaces earlier names, merges and transcript edits and asks for confirmation.

Keyboard shortcuts: Ctrl+N new meeting, Ctrl+O import, Ctrl+F search.

## Local files and recovery

By default, data is kept under `%LOCALAPPDATA%\Gather` (the original storage location, retained for compatibility):

```text
gather.sqlite3                  Meeting metadata, transcript and speaker edits
meetings/<id>/original.*         Copy of imported recording
meetings/<id>/capture.pcm        Continuously saved microphone capture
meetings/<id>/meeting.wav        Normalized 16 kHz mono recording
models/                         Downloaded model weights and local HF cache
models/ready.json               Written only after both model warmups succeed
last-worker.log                 Most recent worker's diagnostic output
```

Select **Open local files** from the sidebar to find the data folder. Do not share
that folder unless you intend to share its recordings. Deleting the app does not
delete meetings. To use another data folder:

```powershell
.\.venv\Scripts\python.exe -m gather --home .\.data
```

Cancelled processing retains the source recording and completed stages. On the
next launch an interrupted session is marked for recovery. **Recover / prepare
saved recording** converts saved raw audio. If speaker detection fails after ASR,
retrying uses the saved word transcript rather than transcribing again.

## Model implementation

- **ASR:** `moondream/parakeet-redux` through `moondream.photon`, explicit CPU device,
  native word timestamps, progressive transcription in a child process.
  If the installed Windows kernel reports only a scalar implementation, DocuMeet
  explicitly expands the **same Redux weights** using Kestrel's dense reference
  materializer. That compatibility mode uses more RAM and does not inherit the
  published packed-kernel throughput. The runtime is pinned because this adapter
  depends on Kestrel's materialization interface.
- **Speakers:** `nvidia/Nemotron-3-Diarization` through Hugging Face Transformers,
  float32 CPU inference. Streaming chunks use the model's speaker cache across the
  complete recording, preserving identity continuity. Audio is read in bounded
  chunks rather than loading an entire hour into a tensor.
- **Alignment:** words are assigned by overlap with detected speaker intervals;
  gaps remain unassigned and simultaneous speakers are marked for review.
- **Offline:** processing sets Hugging Face and Transformers offline flags. Model
  setup is the explicit network-enabled operation. No cloud ASR API is used.
  DocuMeet also disables Photon's anonymous usage telemetry in its isolated adapter
  and loads ASR from the downloaded checkpoint path. No API key is used.

The model size is not the app's total RAM/disk usage. Processing 30–60 minutes in
5–15 minutes is a target that must be measured on the actual demonstration laptop.
A single laptop mic cannot reliably capture simultaneous speech from all corners
of a room. Use a central phone/external mic, clear turn-taking and speaker review.
The app detects anonymous voices; it learns names only from the user's corrections.

## Development and verification

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[models,dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m gather --home .\.data
```

Model-independent tests exercise timestamp alignment, overlap, six-person/hour-long
timelines, merging, persistence, imports, PDF/TXT content, failure recovery and Qt
window state. They do not establish real-model accuracy. See `docs/VERIFICATION.md`
for actual runtime/model validation evidence and remaining limitations.

## Build a Windows distribution

Run `scripts\build.ps1` to create `dist\DocuMeet\DocuMeet.exe` with PyInstaller.
It includes Python and inference runtimes; model weights are downloaded from the
app's setup page. If Inno Setup 6 is installed, the same script builds a per-user
installer using `packaging\DocuMeet.iss`. No administrator privileges are required
by the generated installer.

## Project structure

```text
gather/ui.py           Native desktop screens and interactions
gather/recording.py    Microphone capture with continuous disk writes
gather/jobs.py         QProcess worker orchestration and cancellation
gather/worker.py       Import, ASR, diarization and setup jobs
gather/engines.py      Real model adapters and offline configuration
gather/domain.py       Word/speaker alignment and correction operations
gather/storage.py      SQLite persistence and data locations
gather/exports.py      UTF-8 text and paginated PDF exports
tests/                Core, integration and UI checks
```

## Model credits

- Moondream Parakeet Redux, based on NVIDIA Parakeet TDT v3: CC BY 4.0.
  https://huggingface.co/moondream/parakeet-redux
- NVIDIA Nemotron 3 Diarization: OpenMDW 1.1.
  https://huggingface.co/nvidia/Nemotron-3-Diarization
- Tutorial prototype reviewed for the ASR workflow:
  https://github.com/47thtechcorner/RayCodes_Parakeet_Redux

DocuMeet implements actual model inference and does not use the timestamp-based
speaker assignment formula in the earlier pasted tutorial code.
