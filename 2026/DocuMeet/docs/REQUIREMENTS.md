# DocuMeet demo scope

Native Windows app built with Python and PySide6. English in-person meetings,
4–6 participants, 30–60 minutes, typical office laptops with CPU inference.
5–15 minutes processing is a target to benchmark, not an established guarantee.

## Required

- Record microphone audio to local disk; stop and preserve the recording.
- Import phone recordings (WAV, MP3, M4A, FLAC and other FFmpeg-supported formats).
- Normalize to 16 kHz mono and retain the source for recovery.
- Run real Parakeet Redux inference locally, retaining native word timestamps.
- Run real Nemotron 3 speaker diarization, retaining identity cache across chunks.
- Listen to detected voice samples, name voices, merge duplicate identities.
- Review and correct statement speaker assignments and transcription text.
- Persist meeting audio, words, speaker corrections and reviewed transcripts.
- Export timestamped named transcripts as UTF-8 TXT and paginated PDF.
- Download models during setup, then use the app offline.
- Keep UI responsive using isolated worker processes; retain completed stages after cancellation.
- Provide Windows launch/setup instructions and packaging.

## Explicitly deferred

Summarization, summary model selection, and summary exports. The disabled Summary
tab marks this deferred scope. No summaries are fabricated from keyword rules.

## Quality limits to communicate

Diarization produces anonymous voices, not verified real identities. Names come
from the user. Single-channel ASR cannot reliably recover simultaneous talkers;
overlapping spans are flagged for listening and correction. A quiet room alone
does not guarantee far-field microphone quality.

## Reference implementations

- https://github.com/47thtechcorner/RayCodes_Parakeet_Redux (ASR prototype)
- https://huggingface.co/moondream/parakeet-redux (CC BY 4.0 model)
- https://huggingface.co/nvidia/Nemotron-3-Diarization (OpenMDW 1.1 model)
- https://huggingface.co/docs/transformers/main/en/model_doc/nemotron3_diarization

The earlier pasted diarization code assigned speakers by timestamp modulo 2.
That algorithm is not used in this project.
