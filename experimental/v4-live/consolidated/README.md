# GrainBrick V4 — Final 1.1, clean setup

The latest V4 live integration, with the original project's demo sample and starter preset only. No personal samples, recordings or custom projects are imported. The audio code is byte-identical to integrated 0.1.8 (the user-tested 0.1.7 audio plus the Freeze shortcut hint).

## Install

1. Close GrainBrick. Keep the existing V3/integrated app and `grainbrick-v4-live/config.json` until the first launch; the original engine is copied locally.
2. If you already launched Final 1.0, rename its `grainbrick-v4` folder to **`grainbrick-v4-previous`** before extracting this clean package. This keeps any previously imported files as a backup instead of deleting them. If you never launched 1.0, this step is unnecessary.
3. Extract into `/userdata/roms/ports/`, adding `GrainBrick V4.sh` and a fresh `grainbrick-v4/` folder. Launch **GrainBrick V4**. Allow extra startup time for the original engine/resources to be copied.
4. Check the original demo sample, sample recording/playback, LIVE input, freeze and the three mix knobs. Exit and launch again.
5. Once checked, back up the old folders/launchers to your computer, then remove the old copies from the handheld if wanted. The new V4 no longer depends on them.

The setup retains working USB configuration, original controller mapping and UI/DSP preferences. It does not copy files from old `samples`, `recordings` or `projects` directories. Only the hash-checked original project demo from `demo-samples` and bundled original AMBIENT starter preset are added to the new library. Third-party notices and original resources are preserved. The original native application binaries are not distributed in this small ZIP; they are copied from your installed original app on first launch.

If an old imported V4 install is detected in the destination, setup stops and asks for a backup/fresh folder. It never deletes recordings or user libraries. New samples recorded after clean setup stay in V4 and are retained on subsequent launches.

## Keep one Ports entry

```
roms/ports/
  GrainBrick V4.sh
  grainbrick-v4/
```

After testing and backing up your files, old GrainBrick items you can remove include:
- Launchers: `GrainBrick V4 Live.sh`, `GrainBrick V4 Original UI.sh`, `GrainBrick V4 Integrated.sh`, `GrainBrick V4 Inspect.sh`.
- Folders: `grainbrick-v4-live`, `grainbrick-v4-integrated`, `grainbrick-v4-previous` (if present).
- If retiring V3 too: `GrainBrick beta 1.0.sh`, its GrainBrick audio-check/button-setup launchers, and `grainbrick-beta`.

Your personal audio remains in the old folders: back it up before removing them. Leave unrelated ports alone. No automatic cleanup/deletion is performed.

## Controls

On **SAMPLE/LIVE**, Y opens RECORD INPUT. X switches REC/LIVE while stopped.

In LIVE:
- A starts/resumes, B stops, START + SELECT exits.
- Up/down selects GRANULAR, FX or TAPE MIX; left/right adjusts by 5%.
- Y toggles freeze. The page shows **FREEZE [Y]: ON/OFF** and “HOLD LIVE BUFFER / PRESS Y TO TOGGLE”.
- Original tab navigation opens GRAIN, FX, TAPE and the other original pages.

Granular Mix blends raw input with grains. FX Mix blends around the original delay/reverb/shimmer group; Tape Mix blends around the tape stage. Their original individual controls remain. EQ, compression, ORBIX and gain keep their original processing positions. FX/Tape default to 100%; Granular Mix resets to 0% on a fresh LIVE start.

REC keeps the original WAV recording/edit/save workflow with 100% dry software input monitoring. Keep Tascam direct monitoring off. The original denoiser applies to built-in-mic recordings; it is unavailable for this RG35XX Plus/Tascam USB workflow.

## Files and logs

All app files are in `grainbrick-v4/`:
- `v4.log` — startup, setup and LIVE/REC monitor diagnostics.
- `audio_process.log` — original audio-worker log.
- `SETUP.txt` — confirms clean setup without user-media import.
- `config.json` — working USB capture/output settings.
- `samples/`, `recordings/`, `projects/` — original demo/preset and any new work created in V4.

## Validation

The underlying UI/DSP, low-latency LIVE, mix knobs, freeze and dry REC monitoring have been tested by the user on RG35XX Plus / KNULLI Scarab 20260511 / Tascam DR-40X. Rare clicks during granular parameter changes remain a known observation; an earlier unexpected USB loss was not reproduced in the latest tests. This release introduces no new DSP or buffer changes.

Clean-setup tests check that personal media is excluded, original demos are verified, old folders stay intact, previous imported installs require backup, and subsequent launches preserve new work without needing old folders. The actual consolidated entry/bootstrap/original ARM64 app event loop is checked under emulation with hardware/process boundaries mocked. The new installation layout still needs a first-launch check on the handheld before old folders are removed.
