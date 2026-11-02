from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH).parent
datas, binaries, hiddenimports = [], [], ['gather.worker']
for package in ['moondream', 'kestrel', 'kestrel_native', 'kestrel_kernels',
                'kestrel_kernels_bundle_a', 'kestrel_kernels_bundle_b',
                'kestrel_kernels_bundle_c', 'kestrel_kernels_bundle_d',
                'kestrel_kernels_bundle_e', 'imageio_ffmpeg']:
    data, binary, hidden = collect_all(package)
    datas += data
    binaries += binary
    hiddenimports += hidden
hiddenimports += collect_submodules('transformers.models.nemotron3_diarization')
hiddenimports += collect_submodules('transformers.models.nemotron_asr_streaming')
hiddenimports += collect_submodules('librosa')
hiddenimports += ['transformers.models.auto.processing_auto', 'transformers.models.auto.modeling_auto']
analysis = Analysis([str(root / 'packaging' / 'entry.py')], pathex=[str(root)],
    binaries=binaries, datas=datas, hiddenimports=hiddenimports,
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'tkinter', 'matplotlib', 'pytest'])
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='DocuMeet',
    debug=False, strip=False, upx=False, console=False)
worker = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='DocuMeetWorker',
    debug=False, strip=False, upx=False, console=True)
collect = COLLECT(exe, worker, analysis.binaries, analysis.datas, name='DocuMeet', strip=False, upx=False)
