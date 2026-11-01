# GrainBrick V4 — UI test 1.13 for RG35XX Plus

**UI Test 1.13 is a small update for an existing UI Test 1.12 installation.**

This is the original GrainBrick beta 1.0 app adapted for RG35XX Plus, with its original features and DSP, plus the latest V4 live-input integration. It includes the original native engine/libraries, RG35XX display/controller adapters, bundled NumPy, resources, original project demo, AMBIENT preset, three LIVE mix knobs and Freeze [Y] hint. Personal samples/recordings/projects are not included or imported from other folders.

## UI Test 1.13 darker backgrounds and build credit

The five custom backgrounds are darker while retaining their palette hues. AMBER and all theme accents/text colors are unchanged.

| Theme | Background |
| --- | --- |
| MINT | `#050A09` |
| ICE | `#040911` |
| VIOLET | `#08050D` |
| SAGE | `#0B0E08` |
| SPRUCE | `#030E10` |

The SETTINGS footer credit reads `ANTEVASINBUILD - ON OFFICIAL ETRNLIAM BETA 1.0`, using the original pixel font and footer layout. Footer text is measured before drawing so the longer credit fits alongside existing controls. The credit appears in every theme; AMBER's colors and graphics remain original.

Close GrainBrick and extract `GrainBrick_V4_UI_Test_1.13_Update.zip` over the existing `ports/` directory. Requires installed 1.12. Personal settings/media and audio behavior are retained.

Validation: 32 host tests pass. The ARM-emulated original app verifies all six themes, renders the complete credit through the native footer, and passes TAPE/VISUAL and REC/LIVE controls with audio mocked. SETTINGS screenshots confirm the credit fits between UP/DOWN and B/A CHANGE without overlapping the DSP indicator.

## UI Test 1.12 approved palette refresh

The five custom themes now use the approved palette-tinted text, brighter selected controls, and matching waveform, tape texture and visualization colors. AMBER retains its original palette, tape textures and visualization colors.

| Theme | Background | Text | Inactive | Selected | Tape / wave |
| --- | --- | --- | --- | --- | --- |
| MINT | `#0A1110` | `#8EBDAA` | `#567568` | `#9BE8C0` | `#4E9D82` |
| ICE | `#08111E` | `#8FAFCB` | `#516B84` | `#83D5F3` | `#3F8EAF` |
| VIOLET | `#0F0B17` | `#AE97C3` | `#6F5B83` | `#CEA5F2` | `#8259A6` |
| SAGE | `#151A10` | `#AAA982` | `#6E7551` | `#E0CF8D` | `#A39556` |
| SPRUCE | `#071A1D` | `#75ADB0` | `#3C6A6E` | `#38CDD0` | `#287F87` |

SPRUCE uses the approved blue-green cyan with only a subtle green tint. Selected controls are brighter than normal text and inactive controls in all custom themes. Whites in tape textures and visualization drawing are replaced by palette shades. Tape texture tinting caches only the requested frame; original textures are retained for switching back to AMBER. Warning/status colors outside visualization remain available.

Close GrainBrick and extract `GrainBrick_V4_UI_Test_1.12_Update.zip` over the existing `ports/` directory. Requires installed 1.11. This update retains configuration, media and all audio/DSP/buffer behavior.

Validation: 32 host tests pass, including selection brightness, tinted graphics, source-texture preservation and Amber restoration. The original ARM-emulated app passes all six palettes, SETTINGS navigation, TAPE and VISUAL drawing, REC/LIVE controls and clean exit with audio mocked. Custom-theme TAPE/VISUAL screenshots have no near-white pixels; screenshots are inspected. Handheld animation performance and listening still need device testing.

## UI Test 1.11 darker Spruce background

SPRUCE / alpine has a slightly darker background: `#081411` (RGB 8, 20, 17), replacing `#0C1B18`. Its accent stays `#2A6061`. The other palette colors, themes, audio behavior and user settings are unchanged.

Close GrainBrick and extract `GrainBrick_V4_UI_Test_1.11_Update.zip` over the existing `ports/` directory. Requires installed 1.10. Only changed application files and integrity metadata are included.

## UI Test 1.10 Spruce accent

SPRUCE / alpine now uses `#2A6061` for its accent: a slightly brighter version of the requested `#1A4849`, retaining a muted spruce tone. Its background and other colors, the other five themes, and all audio behavior are unchanged. The dark background remains intact.

Close GrainBrick and extract `GrainBrick_V4_UI_Test_1.10_Update.zip` over the existing `ports/` directory. Requires installed 1.9. Only changed application files and integrity metadata are included; your selected theme, configuration and media are retained.

## UI Test 1.9 dark Sage and Spruce themes

Paper is replaced by two dark themes based on the supplied palette. SETTINGS → THEME now offers AMBER, MINT, ICE, VIOLET, SAGE and SPRUCE. The original four are retained.

| Theme | Background | Accent | Supporting color |
| --- | --- | --- | --- |
| SAGE / olive | `#151A10` | Sage `#CFB97E` | Muted olive `#78835D` |
| SPRUCE / alpine | `#0C1B18` | Sapphire `#72B0AB` | Spruce `#355E58` |

Both backgrounds remain dark. The brighter Sapphire tone is used for readable Spruce selections; the reference Spruce tone supports lines and separators. Text is softly tinted in each palette. A previously saved PAPER selection opens as SAGE automatically. A/B continues to cycle and save the theme while retaining audio settings and routes.

Close GrainBrick and extract `GrainBrick_V4_UI_Test_1.9_Update.zip` over the existing `ports/` directory. Requires installed 1.8. This is a small file update; configuration and personal media are not supplied or replaced. Audio, latency and LIVE/freeze behavior are unchanged.

Validation: 30 host tests pass, including dark backgrounds, text/selection contrast, accent-to-waveform contrast for the two new themes, and migration from PAPER. The original ARM-emulated app passes all six choices, reverse cycling, retained routes and REC/LIVE controls. Settings and waveform screenshots are inspected. Check the colors and VISUAL page on the handheld too.

## UI Test 1.8 themes

SETTINGS now includes THEME: AMBER (the original appearance), MINT, ICE, VIOLET and PAPER. Select THEME with the D-pad and use A/B to cycle. The choice applies immediately and is saved automatically in `config.json` as `ui_theme`, independently of SAVE PARAMS ON EXIT. Existing audio device and channel-route settings are retained. The six settings rows fit above the footer.

Themes change the background, text, dimmed controls, highlights and waveform colors through the original renderer. Signal/status colors and colorful visualizer content are retained where possible; tape imagery keeps its original texture. No screen-wide image filter runs on each frame. AMBER preserves the original palette. Audio buffers, DSP, LIVE/freeze and recording behavior are unchanged.

Close GrainBrick and extract `GrainBrick_V4_UI_Test_1.8_Update.zip` over the existing `ports/` directory. Requires installed 1.7. Only changed app files and integrity metadata are supplied; no personal settings or media are overwritten.

Validation: 29 host tests pass, including theme persistence, route preservation and text/selection contrast. The ARM-emulated original app passes all five theme selections, backward cycling, SETTINGS navigation around THEME, REC/LIVE actions and clean exit. Screenshots of the settings layouts are checked. Hardware display/performance still needs testing.

## UI Test 1.7 continuous waveform display

The bundled original renderer draws 800 separate one-pixel waveform columns over a 964-pixel-wide area. Empty columns between strokes become visible when scaled to the handheld display. This update interpolates the cached display peaks to cover every column, while retaining the original waveform colors, grain boundaries, ROAM range, playhead and drawing order. The source peak data and audio are unchanged. This is a display fix, not an audio-buffer change or a claim of full parity with official beta 1.01.

Close GrainBrick and extract `GrainBrick_V4_UI_Test_1.7_Update.zip` over the existing `ports/` directory. Requires installed 1.6. Only changed files and integrity metadata are included. Audio buffer sizes, LIVE latency, recording behavior, settings, and personal media are unchanged. Please compare the waveform with the same loaded sample and check LIVE/frozen LIVE too.

Validation: 24 consolidated host tests pass. An ARM-emulated original renderer check covers all 965 columns from x=30 to x=994, with the original markers retained. The original 28-frame UI exercise also passes with audio mocked. Real-device display performance still requires testing.

## UI Test 1.6 update (requires installed UI Test 1.5)

Input selection in the browser and REC/LIVE page, and the output list in SETTINGS, use the same short interface names: `TASCAM 1-2`, `AUDIO4c 1-2`, `AUDIO4c 3-4`, etc. Channel pair numbers remain visible. This changes display names only; ALSA devices, route aliases, configuration and audio behavior are retained.

Close GrainBrick, then extract `GrainBrick_V4_UI_Test_1.6_Update.zip` into the existing `ports/` directory and accept replacement of the included files. It contains only changed application files and updated integrity metadata. Keep the existing `grainbrick-v4` folder; do not delete it or install this update alone. No configuration, recordings, samples or projects are included. The full standalone package will be consolidated later.

The AUDIO4c saved-recording startup click remains under investigation. Tascam was reported free of the click. Frozen LIVE now keeps its read anchor when SIZE or PITCH changes. POSITION still scans the held buffer. ROAM and MOTION retain their independent movement when enabled; the highlighted grain span still changes length with SIZE. Unfrozen LIVE keeps its existing capture headroom and latency behavior. Original sample playback and REC audio are unchanged.

Validation: 21 consolidated tests, 8 routing tests and 8 existing source-adapter tests pass. The update overlay is checked against the complete target manifest. The original app also passes the ARM-emulated UI run; USB audio is mocked, so the freeze change still needs a handheld listening/display check.

## UI Test 1.5 changes

Selected input-pair labels are larger in the browser and REC/LIVE ready page, with a smaller fallback for long interface names. REC keeps its original capture/edit/save path and the default 1.4 monitor behavior. The saved-WAV startup click is still under investigation; the monitor-only fade did not solve the reported capture click.

Two opt-in diagnostic controls isolate monitor playback startup and V4 capture buffer timing. See `REC-STARTUP.md` for the four-case comparison. They do not fade, trim, denoise or otherwise alter saved audio. No click fix is claimed pending affected WAVs and on-device comparisons.

## Redesigned REC/LIVE controls (1.4)

On the SAMPLE/LIVE browser, X switches REC/LIVE directly; the current mode is displayed prominently at the upper right. Y opens and starts that selected mode. A still loads samples; B still navigates back. Sample preview moves from X to START on this browser; START + SELECT remains the global exit combo.

L2/R2 selects the input pair from the browser and from the REC/LIVE control page. The ready page has a large REC or LIVE heading, a dedicated input line and a separate format hint. LIVE keeps the three knobs. Mode/start/freeze/input shortcuts now appear in the footer, which is drawn through the original footer renderer.

While LIVE is running, Y toggles freeze. With LIVE stopped, Y starts it; with LIVE paused, Y resumes. B stops/backs out as before, and X changes mode on the control page. During sample recording, Y stops and opens the original recording editor; B remains supported. Original editing and save controls are retained.

The REC monitor now uses a 10 ms soft start only on its output. After that it remains unity-gain dry monitoring. The saved WAV, original capture algorithm, and LIVE DSP path are unchanged. The soft start reduces an initial digital discontinuity; it cannot guarantee removal of a hardware clock/stream-initialization pop. Hardware testing is required.

No new direct-monitor knob is added in this build. The user hears new notes with freeze and 100% granular mix; the user also confirmed fresh notes remain audible after stopping LIVE, identifying a path bypassing LIVE processing, likely interface/DAW monitoring. Closing the whole app can confirm that it is external. A software knob cannot mute an external routing path.

Host tests verify the startup fade and unchanged recorded-file bytes. The ARM-emulated original app checks browser X mode selection, Y LIVE start/freeze, input changes, mix controls, original tabs, Y REC start/stop delegation, footer rendering and clean exit with hardware/file recording mocked. These UI changes require a handheld check.

## New stereo-pair selection — hardware test build

This build adds per-app ALSA channel routes while keeping the original stereo DSP engine. It uses the interface's existing USB channel layout and does not change its saved internal routing.

For the submitted AUDIO4c configuration, Linux exposes 8 capture and 8 playback channels at 48 kHz, S32_LE. The app offers AUDIO4c pairs 1-2, 3-4, 5-6 and 7-8 in each direction. These are USB channel numbers, not physical-jack or DAW-route names. No 9-10 pair is invented when Linux exposes only 8 channels.

On SAMPLE/LIVE -> RECORD INPUT, the interface/pair name is shown. L2/R2 cycles input pairs in both REC and LIVE views. Changing a live input stops LIVE; press A to restart on the new pair. In REC, the original source selection also uses the new pair list. Do not change input during an active sample recording.

In SETTINGS, the original output selector now lists the interface's output pairs alongside the original internal/HDMI choices. The selection is used by sample playback, LIVE output and subsequent REC monitoring. Prefer selecting routing while audio is stopped. Input/output choices are retained in config.json as input_route/output_route. The default first pair preserves the prior routing.

A generated alsa-routing.conf is local to this app/process. It maps the stereo engine to/from the selected USB channels with unity coefficients; unused hardware output channels are silent. ALSA converts the native interface sample format as needed, retaining the existing stereo engine/recording formats. No global ALSA or interface-firmware settings are edited.

Real host ALSA file/null-plugin tests verify 8-channel S32 capture pair 3-4 to stereo S16 and stereo S16 playback to pair 5-6, including silence on other outputs. ARM-emulated original-app checks verify interface labels, input selection/stop/restart, REC delegation, four output choices, selection of 7-8, and configuration persistence using the supplied device descriptor fixture. Actual AUDIO4c routing still needs on-device testing. Keep standalone 1.2 as the stable fallback.

Send v4.log, audio_process.log and config.json after testing. Please check an input pair other than 1-2 in LIVE and REC, and route output to another available USB pair in the audio4c's existing mixer configuration.

## Requirements

Anbernic RG35XX Plus running **KNULLI Scarab 20260511** with its system Python 3.12, Pygame and ALSA tools. Tested audio interface: **Tascam DR-40X**. This is self-contained as an application; it uses the supported KNULLI system runtime. Other hardware/firmware combinations are not established by the testing.

## Install

1. Extract this single ZIP into `/userdata/roms/ports/`.
2. You will have `GrainBrick V4.sh` and `grainbrick-v4/`.
3. Connect a USB audio interface before launch and disable its direct monitoring when using software monitoring.
4. Refresh PORTS if needed, then launch **GrainBrick V4**. The RG35XX Plus button map is loaded automatically from KNULLI’s configured EmulationStation controller profile. Existing user calibration is preserved; if no compatible profile exists, follow the original one-time calibration prompts. No button numbers are guessed.

The app opens without copying anything from older versions. First launch checks the bundled files and creates a default USB configuration. No other downloads or version searches are needed. Sample playback and ORBIX also work without a USB interface; LIVE/USB recording require one. If you connect USB after launch, exit and reopen V4 to rescan. For sample playback, choose the wanted output in the original SETTINGS page if necessary; LIVE selects its configured USB output when started.

## USB configuration

`grainbrick-v4/config.json` is created automatically with capture/playback set to `auto`. Auto selects the first USB card with both capture and playback. With the tested Tascam connected, it resolves to `plughw:CARD=Series,DEV=0`. With multiple interfaces, or if automatic selection is unsuitable, set explicit ALSA device names in that file. `config.example.json` documents the format. Existing `config.json`, mappings and saved preferences are not replaced by the ZIP.

## Controls

On **SAMPLE/LIVE**, X switches REC/LIVE directly. Y starts the selected mode. A loads/opens the sample selection, B goes back, START previews a selected sample, and START + SELECT exits. L2/R2 selects the input pair.

On the LIVE control page, up/down selects GRANULAR/FX/TAPE MIX and left/right adjusts it. Y freezes when running or starts/resumes when stopped/paused. X changes mode; B stops/backs out. During REC, Y or B stops to the original edit page. Footer hints show the current actions.

Granular Mix blends raw input and grains. FX Mix blends around the original delay/reverb/shimmer group; Tape Mix blends around tape. Original per-effect controls, EQ, compression, ORBIX and gain remain available. FX/Tape default to 100%; Granular Mix resets to 0% when LIVE starts fresh. New stage blends apply to LIVE; original sample playback retains its original processing.

REC keeps the original WAV record/edit/save workflow and 100% dry software input monitoring. The original denoiser is for built-in-mic recordings, so it is unavailable for this RG35XX Plus/Tascam workflow. No replacement denoiser is added.

## Updating / decluttering

For a clean installation, extract into a fresh `grainbrick-v4` folder. If a folder with that name already contains work you want to keep, back it up first or update by overlaying the ZIP. Updating does not delete your existing audio/settings; original factory demo/preset filenames may be replaced by their stock copies.

Once this standalone build is tested on your device, you can back up and remove older GrainBrick app folders and launchers. They are not dependencies, even on first launch. Personal recordings in old folders remain there and must be backed up if wanted. Do not remove unrelated ports.

Keep this one entry:

```
roms/ports/
  GrainBrick V4.sh
  grainbrick-v4/
```

## Logs and data

Everything is under `grainbrick-v4/`: `v4.log`, `audio_process.log`, `config.json`, original settings/mapping files, `samples/`, `recordings/` and `projects/`. `RELEASE.json` identifies all packaged files and the byte-verified V4 audio baseline. No migration runs and no old folders are read for app assets or media.

## Validation and known limits

The integrated audio baseline was tested on RG35XX Plus/KNULLI/Tascam: original UI/DSP, LIVE low-latency dry monitoring, granular/FX/Tape knobs, freeze and sample recording/playback. LIVE DSP and original binaries are retained; REC monitor output alone receives the documented short startup fade. 13 host tests cover standalone setup, USB selection and controller-profile handling. The standalone first-run/configuration and complete bundled layout are verified under ARM emulation with hardware/process boundaries mocked. The automatic system profile also passed through the actual V3 translator and original InputManager for A/B/X/Y, L/R, L2/R2, SELECT/START, D-pad and the exit combo. A fresh full-app run generated its button map automatically from the system-profile fixture, with no old calibration or earlier app folders. One fresh-install handheld check is still needed for the standalone packaging.

Rare transition clicks during granular parameter changes remain a known observation. An earlier unexpected USB loss was not reproduced in later tests. New USB interfaces and timing under heavy DSP load need their own checks. The output buffer remains the tested 2048-frame LIVE request; no new DSP or timing algorithm is introduced.

See `CREDITS_V4.md`, the retained original `README_EN.md`, and third-party notices/sources for provenance and licences. The original application remains proprietary; this port does not change upstream licensing.

## Rebuild the ZIP

From the repository, provide an extracted original beta package (its native main checksum is verified):

```
python3 -B experimental/v4-live/consolidated/build_package.py --original /path/to/grainbrick-beta
```

RG35XX adapters come from this repository's working V3 port. Factory assets and all four V4 audio modules are hash-checked during packaging.
