"""Create an hour-long, six-voice stress fixture from the public demo's first 32s.
This repeats audio and is a capacity/performance test, not an accuracy benchmark.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import soundfile as sf
from gather.audio import normalize_audio

target = Path('.data/meeting-60min.wav')
normalize_audio('.data/diarization-example.mp3', '.data/public-demo.wav')
data, rate = sf.read('.data/public-demo.wav', start=0, stop=32 * 16000, dtype='float32')
remaining = 3600 * rate
with sf.SoundFile(target, 'w', samplerate=rate, channels=1, subtype='PCM_16') as out:
    while remaining:
        portion = data[:remaining]
        out.write(portion)
        remaining -= len(portion)
print(f'{target}: {sf.info(target).duration}s; repeated six-voice public audio')
