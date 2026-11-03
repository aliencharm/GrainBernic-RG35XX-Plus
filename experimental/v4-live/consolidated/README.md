# GrainBrick V4.1 — standalone for RG35XX Plus

**One complete installation. No previous GrainBrick build or update ZIP is required.**

AntevasinBuild, based on the official **ETRNLIAM GrainBrick beta 1.0**, combines the original app/DSP with the tested V4 live-input, routing and UI changes through UI Test 1.13. The proprietary original engine and native libraries remain unchanged. This release consolidates the working build; it does not introduce a new audio algorithm.

## V4.1.9 MENU saves frozen LIVE audio

Close GrainBrick and merge `GrainBrick_V4.1.9_Update.zip` into installed V4.1.8. MENU now saves the full frozen LIVE buffer; SELECT retains its current pause/resume behavior. Freeze first, then press MENU and look for SAVED LIVE_FREEZE... below the controls. The footer and screen show MENU SAVE. Files remain in samples/recordings. MENU still goes to the parent folder in the SAMPLE browser.

## V4.1.8 save the full frozen LIVE sample

Close the app and merge `GrainBrick_V4.1.8_Update.zip` into installed V4.1.7, retaining the launcher, media and preferences.

Start LIVE, freeze with A or Y, then press SELECT to save the entire held input buffer. SELECT SAVE appears in the footer and SELECT: SAVE SAMPLE below Freeze. Saving keeps LIVE running and frozen. The saved stereo 48 kHz / 16-bit WAV contains the full 16-second buffer in chronological order, regardless of grain size, position or roam range. Freezing before the buffer fills retains the unused silent part. This saves the held input audio before granular/FX/tape processing.

Files use unique `LIVE_FREEZE_YYYYMMDD_HHMMSS.wav` names in the original sample recordings folder (`samples/recordings/`), with a numeric suffix for repeat saves in the same second. Return to SAMPLE and enter recordings to load one. The browser refreshes after saving. An empty or not-yet-acknowledged frozen buffer reports a message instead of writing a misleading file. Existing recordings are never overwritten.

The audio worker shares buffer cursor/length and Freeze acknowledgement with the UI so exports do not use the parent's stale private counters. Capture and DSP algorithms, buffer length and audio timing settings remain unchanged. SELECT retains its existing behavior outside the LIVE mixer.

## V4.1.7 browser navigation

Close GrainBrick and merge `GrainBrick_V4.1.7_Update.zip` into your installed V4.1.6 folder. MENU goes to the parent folder from the SAMPLE browser, including when a sample file is selected. LEFT provides the same action if MENU was not calibrated. B retains confirmed sample deletion. The footer includes MENU BACK; all other tabs keep their original MENU behavior.

A charging/data OTG splitter requires the handheld to remain the USB host while charging. App detection uses ALSA USB cards and stream descriptors; the connection path through a hub is not filtered. A missing interface through a splitter needs USB/ALSA evidence before an app change can be established. Connect before launch. The separately downloadable `GrainBrick_USB_Check.sh` can be placed in ports and run with the affected connection. The v2 script writes `grainbrick-v4/GrainBrick_USB_Report.txt` with explicit read/write permissions for network access without changing USB, audio, configuration or power settings. Compare direct and splitter connections, saving each report separately.

## V4.1.6 sample deletion and browser hints

Close the app and merge `GrainBrick_V4.1.6_Update.zip` into an installed V4.1.5 folder, retaining your launcher and personal files.

In the SAMPLE browser, B on a file asks DELETE SAMPLE? and shows its name. Press B again to delete that file or A to cancel. Navigation and mode/tab changes cancel the pending confirmation; B on folders retains the original back action. Deleting the loaded file stops playback and clears the player. Projects referencing a deleted file will need another sample; project JSON is not changed.

The browser hint row reads Y RECORD / SELECT TO SHOW MIXER. Existing recording, mixer and LIVE controls are retained.

## V4.1.5 mixer layout refinement

For installed V4.1.4, close the app and merge `GrainBrick_V4.1.5_Update.zip` into your existing `ports/` folder. Keep the same launcher and personal files.

Both mixers sit slightly higher. The compact LIVE Freeze switch and SAMPLE mixer Y: RECORD SAMPLE action sit below the knobs. The SAMPLE browser remains the main screen and now includes a small PRESS SELECT TO SHOW MIXER hint. Controls and audio behavior are unchanged.

## V4.1.4 input, preview and layout update

For installed V4.1.3, close GrainBrick and merge `GrainBrick_V4.1.4_Update.zip` into the existing `ports/` directory. Keep your launcher, settings and media.

SAMPLE and LIVE mixers share mode/status placement on the right, input details on the left and matching knobs/footer styling. SAMPLE shows its recording action and loaded filename; LIVE shows a compact FREEZE ON/OFF switch below the input details. A toggles Freeze during LIVE; Y keeps its start/freeze/resume behavior.

The RG35XX Plus has no built-in microphone. Only detected USB inputs are offered; with none connected, both modes show NO USB INPUT and recording/LIVE start report the missing input before starting capture. Internal output is valid when USB input is connected; choose the wanted output in SETTINGS. Connect the interface before launch.

START previews the selected browser audio file whether already loaded or not, using the same preview player. The SAMPLE browser separator is shortened and its right panel includes INPUT above the selected interface/pair.

## V4.1.3 SAMPLE and LIVE mixer update

Close GrainBrick and extract `GrainBrick_V4.1.3_Update.zip` into the existing `ports/` directory, merging `grainbrick-v4` with your installed V4.1.2 folder. Keep the existing launcher. Personal samples, projects, recordings and settings are preserved.

SAMPLE opens the sample browser. SELECT opens its playback mixer with separate GRANULAR MIX, FX MIX and TAPE MIX controls; SELECT or B returns to the browser. Up/down selects a mix and left/right adjusts it. A or START plays/pauses the loaded sample from the mixer. Y records using the original recording/editor workflow. Footer hints show these actions.

X switches from SAMPLE to the LIVE mixer in READY state; Y starts LIVE. X returns to the SAMPLE browser. The mode and interface labels sit further right, with long header text shortened to fit. SELECT retains its original behavior in other tabs, and START + SELECT still exits.

SAMPLE mix values are separate from LIVE and saved with project parameters. Older projects default all three to 100%, retaining original playback. GRANULAR MIX blends the original granular player with a native straight file player; FX MIX and TAPE MIX blend their respective native stages. The native effects keep running when their mix is zero. Audio buffer timing and saved recording audio are unchanged.

## V4.1.2 load projects paused

Loading a project now leaves transport paused even if the saved project has `transport.playing=1`. The original file worker remains ready, but no playback begins until you press Play. START preview remains available in the sample browser. Existing projects and their sound parameters are retained; no project JSON is rewritten automatically.

Close GrainBrick and extract `GrainBrick_V4.1.2_Update.zip` into the existing `ports/` directory, merging its `grainbrick-v4` folder with yours. Supports installed V4.1 or V4.1.1. Keep your current folder, launcher, settings and media.

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
- SAMPLE/LIVE selection, with separate three-control playback mixers.
- USB LIVE input with GRANULAR, FX and TAPE mix controls; freeze holds the buffer while SIZE changes retain the frozen read anchor.
- Stereo input/output pair selection, including the tested AUDIO4c USB pairs 1-2, 3-4, 5-6 and 7-8. Names identify USB channels, not physical jacks or DAW routes.
- Short TASCAM / AUDIO4c labels in input selection and output settings.
- Continuous waveform drawing, palette-tinted text/tape/visualizations and brighter selected controls in custom themes.
- Amber, Mint, Ice, Violet, Sage and Spruce themes. Amber retains its original colors and graphics. Custom backgrounds use the darker approved palettes.
- SETTINGS build credit: `ANTEVASINBUILD - ON OFFICIAL ETRNLIAM BETA 1.0`.

## Controls

On **SAMPLE/LIVE**, X switches SAMPLE browser / LIVE READY. In the SAMPLE browser, A loads, START previews, SELECT opens the SAMPLE mixer, Y records and L2/R2 selects the input pair. In the SAMPLE mixer, up/down selects a control, left/right adjusts, A/START plays or pauses, and SELECT/B returns to the browser.

In LIVE, up/down selects GRANULAR / FX / TAPE MIX and left/right adjusts. Y starts, freezes or resumes. B stops active LIVE, then returns to SAMPLE when stopped. Input changes stop LIVE; restart it on the chosen pair.

SAMPLE recording retains the original recorder and editor. Y or B stops recording to the editor. Do not change input during recording. Saved WAV audio is not faded, trimmed or otherwise modified to suppress startup clicks. START + SELECT exits globally.

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

The clean archive passes its manifest, layout, factory-content and license checks. All 46 host tests pass. The pruned NumPy runtime, original native DSP chain and fresh application startup/control flow pass ARM-emulated checks, including a separate no-USB launch. Hardware/audio-process boundaries are mocked in the UI tests. The V4.1 baseline was confirmed on device. The input/layout update needs device confirmation; see `VALIDATION-4.1.4.md` in the repository.

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
