# Verification record

Date: 29 October 2026. This file distinguishes implementation checks from actual
model evidence. Summarization is outside the current scope.

## Completed checks

- `python -m pytest -q --basetemp .data/pytest-tmp3`: 16 tests passed.
- Native Qt application launches on Windows 11, Python 3.13.7 / PySide6 6.12.0.
- Native UI checked through Windows accessibility: New meeting dialog, saved
  meeting view, microphone enumeration and import dialog.
- Welcome, recording, transcript, six-voice review and model-setup views rendered.
  Populated view fixtures are explicitly synthetic and do not prove inference.
- A seven-page PDF was generated, text-checked and visually inspected on its first
  and final pages. TXT/PDF tests verify speaker names, timestamps and final content.
- `pip check`: no broken requirements at the first installed-runtime checkpoint.
- PyTorch 2.15.0+cpu and Transformers 5.22.0 import successfully; the installed
  Transformers build includes `nemotron3_diarization`.

## Real-model validation in progress

- Both checkpoints have been downloaded to the local DocuMeet model cache.
- Real Parakeet Redux initialization initially failed: the Windows native wheel
  reports its ternary CPU kernel as `scalar`. DocuMeet now deliberately selects
  Kestrel's dense reference materializer for the same Redux checkpoint when packed
  kernels are unavailable. The real Redux warmup then succeeded.
- Nemotron initialization identified a missing `librosa` dependency. It has been
  added to the application dependency manifest; full inference is still being
  verified.
- `scripts/verify_runtime.py` runs actual ASR and speaker detection against the
  public fixture referenced by the Transformers documentation. It denies Python
  socket connections during inference and exports a result report.

## Remaining acceptance checks

- Complete Nemotron warmup and offline real-speech inference.
- Verify the UI worker chain, playback, cancellation and corrections on real output.
- Build and launch the packaged executable; verify packaged model loading.
- Build and smoke-test the Windows installer.
- Benchmark a 30–60 minute recording, including bounded-memory speaker inference.

## Test machine

Intel Core i5-13450HX, 10 physical cores / 16 logical processors, approximately
16 GB RAM, Windows 11. An RTX 4050 is present but these adapters explicitly use CPU.
Results from this machine do not guarantee identical performance on office laptops.

## Public inference fixture

https://huggingface.co/datasets/hf-internal-testing/dummy-audio-samples/resolve/main/diarization_example.mp3

Only public test audio is used for inference validation. A representative meeting
recorded in the actual demonstration room is still the best accuracy evaluation.
