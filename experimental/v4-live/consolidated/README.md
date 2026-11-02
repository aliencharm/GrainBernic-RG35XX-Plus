# GrainBrick V4.1 — standalone for RG35XX Plus

**One complete installation. No previous GrainBrick build or update ZIP is required.**

AntevasinBuild, based on the official **ETRNLIAM GrainBrick beta 1.0**, combines the original app/DSP with the tested V4 live-input, routing and UI changes through UI Test 1.13. The proprietary original engine and native libraries remain unchanged. This release consolidates the working build; it does not introduce a new audio algorithm.

## V4.1.1 project/playback update

For an existing V4.1 installation, close the app and extract `GrainBrick_V4.1.1_Update.zip` into the same `ports/` directory, accepting replacement of the included application files. Keep your existing `grainbrick-v4` folder and **GrainBrick V4.1** launcher. This small update does not contain or overwrite projects, samples, recordings, settings or theme preferences.

Project loading now returns to file playback and the sample browser. Transient `live.enabled` / `live.freeze` flags from older saved projects and last-session state are ignored, and new saves omit those flags. Loading the same file after LIVE restarts the original file worker as needed. The loaded audio file is selected in the browser so START previews it; the original preview and REC edit/save implementations are retained.

Legacy references to the duplicate factory demo and moved media directories are resolved to an unambiguous matching path in the current installation. Existing project JSON files are not automatically rewritten. Actually missing or ambiguous files retain the original SAMPLE NOT FOUND error. A saved project references an audio file; it does not embed a temporary LIVE buffer.

The update does not change DSP algorithms, audio buffers, themes or saved-recording samples. V4.1 remains the complete standalone baseline; V4.1.1 is an overlay for it.

## Install fresh

Requires **Anbernic RG35XX Plus running KNULLI Scarab 20260511**, with its system Python 3.12, Pygame and ALSA tools. Bundled NumPy supplies the additional runtime dependency. No pip installation or earlier app folders are needed. Other firmware/hardware combinations are not established by these checks.

1. Close GrainBrick. If `ports/grainbrick-v4` already exists, back it up outside `ports` or rename it before installing. Keep your recordings and projects safe.
2. Extract `GrainBrick_V4.1_Standalone.zip` into `/userdata/roms/ports/`.
3. The ZIP provides exactly these two top-level items:

   ```
   ports/
     GrainBrick V4.1.sh
     grainbrick-v4/
   ```

4. Connect USB audio before launch, refresh the PORTS list if necessary, and launch **GrainBrick V4.1**.
5. The first launch verifies bundled files, creates a default USB configuration and uses KNULLI's controller profile. If no compatible profile is available, the original button calibration runs.

For a decluttered PORTS list, keep only the new launcher after backing up/removing your own older GrainBrick launchers and app folders. This package never deletes old installations or reads their assets/settings. Its launcher uses only the adjacent `grainbrick-v4` directory.

## Bringing your own data forward

After a clean launch, close the app before copying any personal `samples/`, `recordings/` or `projects/` from your backup. Existing V4 `config.json`, `settings.json`, `sound_state.json`, `gb_buttons.json` and `button_mapping.json` can be copied selectively if you want those preferences/mappings retained. Back up both copies before replacing files. Old logs, generated ALSA routing files, lock files and setup markers need not be copied.

The ZIP contains only the original factory demo WAV and AMBIENT project. It does not contain anyone's recordings, custom presets, device configuration or saved state. The default theme is the original Amber; your saved V4 theme is retained if you copy your `config.json`.

## Included features

- Original granular instrument, ORBIX, FX, tape, sample editing and project workflow.
- REC/LIVE selection and controls integrated into the original UI.
- USB LIVE input with GRANULAR, FX and TAPE mix controls; freeze holds the buffer while SIZE changes retain the frozen read anchor.
- Stereo input/output pair selection, including the tested AUDIO4c USB pairs 1-2, 3-4, 5-6 and 7-8. Names identify USB channels, not physical jacks or DAW routes.
- Short TASCAM / AUDIO4c labels in input selection and output settings.
- Continuous waveform drawing, palette-tinted text/tape/visualizations and brighter selected controls in custom themes.
- Amber, Mint, Ice, Violet, Sage and Spruce themes. Amber retains its original colors and graphics. Custom backgrounds use the darker approved palettes.
- SETTINGS build credit: `ANTEVASINBUILD - ON OFFICIAL ETRNLIAM BETA 1.0`.

## Controls

On **SAMPLE/LIVE**, X changes REC/LIVE; Y opens and starts the selected mode. A loads a sample, B goes back, START previews a sample, and L2/R2 changes the input pair. START + SELECT exits globally.

In LIVE, up/down selects GRANULAR / FX / TAPE MIX, and left/right adjusts it. Y freezes/unfreezes while running, or starts/resumes when stopped/paused. B stops/backs out and X changes mode. Input changes stop LIVE; restart it on the chosen pair.

In REC, Y starts the original recorder. Y or B stops to the original recording editor. Original edit/save controls remain. Do not change input during an active recording. REC uses dry software monitoring; saved WAV audio is not faded, trimmed or otherwise modified to suppress startup clicks.

In **SETTINGS → THEME**, use A/B to cycle. Theme changes save immediately, independently of SAVE PARAMS ON EXIT. Audio output selection remains in SETTINGS. Footer hints show current actions; the native application's original control behavior is retained elsewhere.

## USB audio and routing

`config.json` is generated on first launch with `capture` and `playback` set to `auto`, selecting the first USB interface with capture and playback. With multiple devices you may use explicit ALSA PCM names; `config.example.json` shows the format. Input/output route choices and theme preference are saved without replacing one another.

A generated `alsa-routing.conf` applies only to this process. The original stereo engine is routed to the selected interface channels with unity coefficients; unused output channels are silent. Interface firmware routing and global ALSA configuration are not edited. Connect USB before launch; exit/reopen after connecting a new interface.

Disable the interface/DAW's direct monitoring or return feedback when using software monitoring. An external monitor path can remain audible while LIVE is frozen or stopped. RG35XX Plus has no built-in microphone; the original built-in-mic denoiser is unavailable for USB REC.

Without USB, sample playback and ORBIX remain available. For sample playback, select the wanted output in SETTINGS as needed. LIVE selects its configured USB output when started.

## Themes

| Theme | Background | Text | Inactive | Selected | Tape / waveform |
| --- | --- | --- | --- | --- | --- |
| MINT | `#050A09` | `#8EBDAA` | `#567568` | `#9BE8C0` | `#4E9D82` |
| ICE | `#040911` | `#8FAFCB` | `#516B84` | `#83D5F3` | `#3F8EAF` |
| VIOLET | `#08050D` | `#AE97C3` | `#6F5B83` | `#CEA5F2` | `#8259A6` |
| SAGE | `#0B0E08` | `#AAA982` | `#6E7551` | `#E0CF8D` | `#A39556` |
| SPRUCE | `#030E10` | `#75ADB0` | `#3C6A6E` | `#38CDD0` | `#287F87` |

A saved legacy PAPER selection maps to SAGE. Spruce uses the approved blue-green cyan with a subtle green tint. AMBER is unchanged.

## Clean runtime package

Only runtime Python modules, native engine/libraries, required resources, the pruned NumPy runtime, factory demo/preset, release integrity manifest and documentation/licenses are included. NumPy's test suites, compiler tooling, headers, typing stubs, Python caches, development scripts, old patch instructions, logs, user state and the duplicate demo WAV are omitted.

Original licenses, third-party notices and supplied compliance sources are retained. Those are part of the distribution, not removable runtime clutter. See `CREDITS_V4.md`, `README_EN.md`, `THIRD_PARTY_NOTICES.md`, `THIRD_PARTY_LICENSES/` and `THIRD_PARTY_SOURCES/`.

`RELEASE.json` records the version and hashes. First launch verifies the installed application; normal recordings/settings are mutable and are not treated as immutable app files.

## Validation

The clean archive passes its manifest, layout, factory-content and license checks. All 32 host tests pass. The pruned NumPy runtime, original native DSP chain and fresh application startup/control flow pass ARM-emulated checks, including a separate no-USB launch. Hardware/audio-process boundaries are mocked in the UI tests. The new clean install still needs on-device confirmation; detailed release evidence is in the repository’s `VALIDATION-4.1.md`.

## Known limits and diagnostics

The AUDIO4c startup click in saved REC audio remains unresolved. The user reported no corresponding click with Tascam. No saved-audio suppression is introduced. Rare granular transition clicks and interface/DAW monitoring paths remain separate observations. New interfaces and heavy-DSP timing need on-device checks. The tested LIVE output request remains 2048 frames with 512-frame periods.

Logs are `v4.log` and `audio_process.log` under `grainbrick-v4`. For a device issue, keep those logs, `config.json`, interface details and the original affected WAV.

Optional REC isolation settings can be exported before the launcher command: `GRAINBRICK_REC_MONITOR=0` disables only software monitor playback; `GRAINBRICK_REC_CAPTURE_TIMING=original` omits V4's capture latency flags. Defaults retain the tested behavior. These controls do not edit saved audio.

## Rebuild

From the repository, using the checksum-verified extracted original beta:

```
python3 -B experimental/v4-live/consolidated/build_package.py --original /path/to/grainbrick-beta
```

The builder verifies original assets and the historical audio baseline before packaging the current tested overrides. Development tests/build helpers stay in the repository and are not installed on the handheld.
