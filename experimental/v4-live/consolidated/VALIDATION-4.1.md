# GrainBrick V4.1 release validation

This is a packaging consolidation of tested UI Test 1.13, with runtime version 4.1 and a single standalone launcher. The audio, routing, recording, waveform and theme implementations retain the tested behavior.

## Package audit

`verify_package.py` checks ZIP integrity, all manifest hashes, pinned original native main, executable launcher, exactly two top-level installation entries, absence of personal settings/media and developer/cache files, the factory project's sample reference, a single demo WAV, and retained licenses/compliance sources. NumPy licenses are preserved even where development headers are removed.

The pruned runtime excludes test suites, f2py compiler tools, headers, typing stubs, PyInstaller tooling, Python caches and original wheel entry-point/record metadata for omitted tools. Runtime Python/native modules, library metadata and licenses remain. Packaging uses a deterministic timestamp and writes SHA256SUMS.txt.

The following installed implementations were compared byte-for-byte with the tested complete UI Test 1.13 package: `original_adapter.py`, `live_source.py`, `record_monitor.py`, `stage_mix.py`, `v4_themes.py`, `v4_record_ui.py`, `v4_waveform.py`, `channel_routes.py`, and `audio_inventory.py`. All match. All retained original native binaries and resources are copied unchanged and hashed.

## Host regressions

32 consolidated host tests pass: standalone preparation, existing settings/recordings preservation, device selection, controller profiles, unchanged saved monitor WAV bytes, REC isolation controls, frozen read-position behavior, continuous waveform drawing, theme saving/contrast/tinting and original Amber texture restoration.

## Pruned runtime under ARM emulation

A clean extraction was run with its own `_vendor` as the only NumPy source. No original-release vendor folder or previous GrainBrick app supplied dependencies. NumPy FFT, linear algebra, testing helpers, the NPZ noise-profile resource, and Pygame surfarray all passed; the loaded NumPy path was verified inside the extracted app.

The original native DSP checks passed with that pruned runtime: chain rendering, FX/tape stage blends, source-buffer mutation, grain density, native LIVE-buffer rendering, freeze/resume, file-source return, and AudioWorker's shared-parameter processing loop. Capture/playback/process boundaries were mocked; the original DSP libraries performed the numerical processing.

## Fresh application runs

The actual original app loop passed a fresh 28-frame run with system-controller and AUDIO4c descriptor fixtures: automatic mapping and config creation, sample loading, input/output pairs, REC/LIVE actions, original GRAIN/FX tabs, freeze/mixes, preview and clean exit. No saved preferences or earlier app folders were used.

A separate clean extraction also passed startup, sample loading and clean exit with no USB interface detected. Its default config and controller mapping were created locally. OS audio was mocked in these UI tests.

## Practical limits

The underlying behavior through 1.13 was user-tested on-device. The new clean standalone install still needs a handheld confirmation; emulation does not verify USB timing, physical mapping or animation performance. The AUDIO4c saved-REC startup click remains unresolved and is documented. No fade/trim/denoise is applied to saved recordings to conceal it.

## Reproduce

```
python3 -B experimental/v4-live/consolidated/build_package.py --original /path/to/grainbrick-beta
python3 -B experimental/v4-live/consolidated/verify_package.py experimental/v4-live/releases/GrainBrick_V4.1_Standalone.zip
python3 -B -m unittest discover -s experimental/v4-live/consolidated
```

Use a host Python with NumPy/Pygame for the host suite. Native application/DSP checks require an ARM64 Python 3.12 runtime or the existing ARM emulation lab and its system Pygame/ALSA boundaries.
