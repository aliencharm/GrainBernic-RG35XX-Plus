# GrainBrick V4 — consolidated release 1.0

One launcher, one app folder, with the original GrainBrick beta 1.0 interface and DSP, live granular input, freeze and three mix knobs. This consolidates the user-tested integrated 0.1.7 audio code plus the 0.1.8 freeze hint. Audio/DSP adapter files are byte-identical to 0.1.8; this release changes installation and storage layout, not the sound engine.

## Install once

1. Close all GrainBrick versions. Leave the existing `grainbrick-v4-integrated`, `grainbrick-v4-live` and `grainbrick-beta` folders in place for the first launch.
2. Extract the ZIP into `/userdata/roms/ports/`. It adds `GrainBrick V4.sh` and `grainbrick-v4/`. Launch **GrainBrick V4**.
3. First launch copies the original installed engine/resources and migrates your samples, recordings, projects, USB config, button mapping and saved settings. Allow extra startup time and sufficient free space for a full copy. The originals are left in place. The download is small because original application binaries are copied locally, not included in this ZIP.
4. Check sample playback, REC and dry monitoring, LIVE, freeze, the mix knobs, and your projects. Exit and open V4 once more.
5. Read `grainbrick-v4/MIGRATION.txt`. If it says **Cleanup ready: YES**, and your files work in V4, back up the old folders and launchers to your computer. Then remove those old copies from the handheld.

After migration, V4 runs entirely from `grainbrick-v4/`. It no longer needs the old application folders. Do not delete the new folder or `GrainBrick V4.sh`.

## Declutter after checking V4

Keep only this V4 entry if that is your preference:

```
roms/ports/
  GrainBrick V4.sh
  grainbrick-v4/
```

Old GrainBrick launchers you can move to your computer after checking the new app:
- `GrainBrick V4 Live.sh`
- `GrainBrick V4 Original UI.sh`
- `GrainBrick V4 Integrated.sh`
- `GrainBrick V4 Inspect.sh`
- `GrainBrick beta 1.0.sh` and its old GrainBrick audio-check/button-setup launchers, if you also want to retire V3.

Old folders you can back up and remove once migration is verified:
- `grainbrick-v4-live/`
- `grainbrick-v4-integrated/`
- `grainbrick-beta/`

Leave unrelated ports alone. Keep the downloaded old ZIPs on your computer as fallbacks, rather than in the handheld ROM directory. This package never deletes or moves old launchers or data automatically.

## How data is preserved

The working integrated app's settings and mappings take priority. V3 libraries are also imported. Identical files share a copy; different files with the same path are both retained, with a suffix such as ` [V3]`. Project sample paths are updated to match renamed imported files. Alternative V3 settings are kept under `migration-backups/`.

`migration-report.json` lists imported files and checksums. If it lists unresolved old-folder references, `MIGRATION.txt` says **Cleanup ready: NO**. Keep the old folders and send the report; do not remove them yet. A completed migration is not repeated on later launches, so new recordings/settings stay intact.

## Controls

On **SAMPLE/LIVE**, Y opens RECORD INPUT. X switches REC/LIVE while stopped.

In LIVE:
- A starts/resumes; B stops; START + SELECT exits the app.
- Up/down selects a mix knob; left/right changes it in 5% steps.
- Y toggles freeze; its state and shortcut are shown beneath the knobs.
- Use the original tab controls for GRAIN, FX, TAPE and the other original pages.

GRANULAR MIX blends raw input with the original granular output. FX MIX blends around the original delay/reverb/shimmer group. TAPE MIX blends around the original tape stage. FX/Tape default to 100% and retain their original per-effect controls. Granular Mix resets to 0% on a fresh LIVE start. EQ, compression, ORBIX and level controls retain their original positions and behavior.

REC records a sample through the original WAV recorder and provides 100% dry unity-gain software monitoring. Keep Tascam direct monitoring off for software monitoring. Denoise belongs to the original built-in-microphone recording path; RG35XX Plus has no built-in mic, and denoise is unavailable for the Tascam workflow.

## Logs and configuration

Everything now lives under `grainbrick-v4/`:
- `v4.log`: launcher, migration, LIVE/REC monitor diagnostics.
- `audio_process.log`: original audio-worker log.
- `config.json`: migrated USB capture/playback configuration.
- `settings.json`, `sound_state.json`, `gb_buttons.json`, `button_mapping.json`: original saved state/mapping files, where present.
- `samples/`, `recordings/`, `projects/`: migrated and new audio/projects.

## Validation and known limits

The user has tested the integrated baseline on RG35XX Plus / KNULLI Scarab 20260511 with Tascam DR-40X: original UI/DSP, sample recording/playback, dry monitoring, live input, reduced-latency output, mix knobs and freeze. Later tests reported no USB interruption or continuous clicking. Rare transitions during granular parameter/switch changes remain a known observation. One earlier session recorded unexpected USB device loss; long-term USB reliability has not been established.

Consolidation adds a new migration and folder layout, which still needs one on-device installation check before old copies are removed. Host tests cover data/settings preservation, name collisions, project-path rewriting, invalid inputs, retry behavior and independence from old folders. The consolidated launcher, supplied V3 bootstrap and actual original ARM64 app event loop are also checked together in the consolidated folder with hardware/process boundaries mocked, including reopening with old source folders absent. No new DSP or timing changes are introduced here.
