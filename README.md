# GrainBrick V4.2 — RG35XX Plus

[**Download V4.2 — complete standalone**](https://github.com/aliencharm/GrainBernic-RG35XX-Plus/raw/refs/heads/v4-experimental/experimental/v4-live/releases/GrainBrick_V4.2_Standalone.zip)

[**Download personal-data importer**](https://github.com/aliencharm/GrainBernic-RG35XX-Plus/raw/refs/heads/v4-experimental/experimental/v4-live/releases/GrainBrick_V4.2_Import_Data.sh)

The V4.2 standalone consolidates the working **V4.1.10** runtime: separate SAMPLE/LIVE mixers, original recording/editor, full 16-second frozen input WAV saving on MENU, corrected LIVE transport/Freeze/stop controls, project loading fixes, sample deletion, folder navigation, stereo USB routing, continuous waveforms and six themes. Original native app/DSP and Amber remain unchanged.

The clean ZIP contains **GrainBrick V4.2.sh** and **grainbrick-v4/**. No earlier build or patch chain is required. Development files, old updates, logs, caches, diagnostic reports and personal media are excluded; required licenses and compliance sources remain.

To keep the projects, recordings, samples and settings used during development:

1. Close the app and rename the current `ports/grainbrick-v4` to `ports/grainbrick-v4-backup`.
2. Extract the V4.2 standalone into `ports/` to create the new app folder. Move the old V4.1 launcher off PORTS to avoid duplicate entries.
3. Put `GrainBrick_V4.2_Import_Data.sh` in `ports/`, refresh PORTS and launch it once.
4. Check `grainbrick-v4/Import_Report.txt` for **IMPORT COMPLETE**, then launch **GrainBrick V4.2**. The original backup stays intact. Keep it until your media/projects/settings are confirmed.

The importer copies only personal data and preference files. Conflicting new personal media blocks import rather than being overwritten. After confirmation, move the backup and optional diagnostic/import scripts off the handheld for a clean PORTS folder.

Target: **RG35XX Plus / KNULLI Scarab 20260511**, using system Python 3.12, Pygame and ALSA. A pruned NumPy runtime, factory demo/preset, original native libraries, assets and legal notices are bundled. Internal version, launcher and manifest identify this build as V4.2. The original V4.1 standalone remains a separate historical release.

[Installation and controls](experimental/v4-live/consolidated/README.md) · [Final validation](experimental/v4-live/consolidated/VALIDATION-4.2.md) · [Credits](experimental/v4-live/consolidated/CREDITS.md)

The AUDIO4c saved-REC startup click remains unresolved; the user reported Tascam free of that click. Direct Tascam connection is the confirmed working setup; the tested charging/data dongle did not appear in the handheld's USB/ALSA inventory. The final package is verified on the host and under ARM emulation; hardware timing still needs device confirmation.

Historical builds remain in the repository for reference; they are not installation dependencies.

---

The earlier V3 port documentation is retained below.

# GrainBernik

**GrainBernik** is an unofficial fork of [ETRNLIAM/GrainBrick](https://github.com/ETRNLIAM/GrainBrick) for the **Anbernic RG40XX H** (640×480) running KNULLI.

GrainBrick draws its interface for the TrimUI Brick screen (1024×768). On a 640×480 screen you only see the top-left part of it. This fork adds a small launcher patch: the app keeps drawing at 1024×768 off-screen, and every frame is scaled down to the real screen. Both screens are 4:3, so the picture fills the whole display.

The patch does not modify or redistribute the closed GrainBrick application: you still need the official release ZIP from the original author.

> Status: beta. Tested on RG40XX H with KNULLI: screen scaling, buttons, USB audio output and USB recording (Zoom H1n as audio interface).

## Install on RG40XX H

1. Install the official release as described below (copy `grainbrick-beta/` and `GrainBrick beta 1.0.sh` to `/userdata/roms/ports/`). With the card in a PC, this is the `roms/ports` folder on the SHARE partition.
2. Copy the files from [`rg40xx-h-patch/grainbrick-beta/`](rg40xx-h-patch/grainbrick-beta/) into `/userdata/roms/ports/grainbrick-beta/`, replacing `gb_launch.py`:
   - `gb_display_fit.py` — the screen adapter;
   - `gb_buttons.py` — the button layout adapter;
   - `gb_audio.py` — the USB recording adapter;
   - `gb_launch.py` — the original launcher plus a few lines that load the adapters.
3. Copy [`rg40xx-h-patch/GrainBernik Buttons Setup.sh`](rg40xx-h-patch/) (and optionally `GrainBernik Audio Check.sh`) into `/userdata/roms/ports/`.
4. Launch GrainBrick from PORTS. On the first launch a short button setup screen appears: press each button it asks for (A, B, X, Y, L1, R1, L2, R2, SELECT, START, MENU, D-pad, then optionally L3/R3 for TAB−/TAB+). Optional steps are skipped automatically after a few seconds.

### Buttons

GrainBrick reads the raw button numbers of the TrimUI Brick, so on other devices the button names in the app's hints don't match the physical buttons. `gb_buttons.py` records your device's layout once (saved to `grainbrick-beta/gb_buttons.json`) and translates every button press into the Brick's numbers. After that the button labelled **A** on the RG40XX H is **A** in GrainBrick, **L1** is **L1**, and so on. D-pad buttons are converted to the D-pad events the app expects; analog L2/R2 triggers are supported.

To redo the setup, run **GrainBernik Buttons Setup** from PORTS (or delete `gb_buttons.json`). Set `GRAINBRICK_BUTTONS=0` to turn the adapter off.

### USB audio

- **Output** works out of the box: connect a class-compliant USB audio device *before* starting GrainBrick and choose it in the app's OUTPUT setting.
- **Recording**: GrainBrick records "USB AUDIO" from a fixed device (`hw:1,0`, exactly 48 kHz / 16 bit / stereo), which on the RG40XX H is usually not the USB card and rejects devices with other formats. `gb_audio.py` redirects that recording to the first USB card that can record, through ALSA `plughw`, so sample rate, bit depth and channel count are converted automatically. Choose **USB AUDIO** as the input source on the recording page.
- The RG40XX H has no built-in microphone, so the BUILT-IN MIC source does not work.
- Tested with a **Zoom H1n**: micro-USB to USB-C data cable into the OTG port, on the recorder choose *Audio Interface → PC/Mac*. Batteries in the H1n make the connection more reliable.
- An iPhone cannot be used as a USB sound card on Linux.
- If a device doesn't show up, run **GrainBernik Audio Check** from PORTS with it connected; it writes `grainbrick-beta/audio_check.txt` with what the system sees.
- Optional: `GRAINBRICK_USB_IN=plughw:CARD=<id>,DEV=0` forces the capture device, `GRAINBRICK_AUDIO=0` turns the adapter off.

Optional settings (environment variables, can be added to `GrainBrick beta 1.0.sh` before the `python3` line):

| Variable | Values | Meaning |
|---|---|---|
| `GRAINBRICK_SCREEN` | e.g. `640x480` | Force the real screen size (default: auto-detect) |
| `GRAINBRICK_SCALE` | `smooth` / `fast` | Scaling quality. `smooth` is the default and switches to `fast` automatically if the CPU is too slow |
| `GRAINBRICK_FIT` | `0` | Turn the adapter off |

The launcher log `grainbrick-beta/beta_port_launcher.log` contains a `GB DISPLAY FIT:` line with the detected sizes.

## Установка на RG40XX H (кратко)

Установите официальный релиз в `roms/ports`, затем скопируйте `gb_display_fit.py`, `gb_buttons.py`, `gb_audio.py` и `gb_launch.py` из папки `rg40xx-h-patch/grainbrick-beta/` в `roms/ports/grainbrick-beta/` с заменой, а `GrainBernik Buttons Setup.sh` — в `roms/ports/`. Интерфейс будет уменьшен с 1024×768 до 640×480 на весь экран. При первом запуске появится экран настройки кнопок: нажимайте кнопки, которые он просит. После этого названия кнопок в подсказках приложения совпадут с надписями на приставке. Повторить настройку можно через порт «GrainBernik Buttons Setup». USB-звук: подключите USB-звуковую карту до запуска (проверено с Zoom H1n в режиме Audio Interface → PC/Mac), выберите её в OUTPUT, а для записи — источник USB AUDIO.

---

*Original README of GrainBrick below.*

# GrainBrick

A free granular ambient sound instrument for TrimUI Brick.

GrainBrick turns audio samples into evolving, organic textures with granular processing, tape-style sound shaping, effects and the ORBIX generative note engine.

It is designed for hands-on ambient exploration and sound design - not a tracker, sequencer or traditional looper.

## GrainBrick beta 1.0

This is the first public beta for the original TrimUI Brick running KNULLI.

## Features

- Granular sample processing and evolving ambient textures
- ORBIX generative note engine
- Reverb, delay, shimmer and other sound-shaping effects
- Tape-style processing
- Recording and trimming audio, including the Brick's internal microphone
- USB audio input/output support on compatible devices
- Project saving and contextual parameter help

## Download

Open the [original repository's Releases section](https://github.com/ETRNLIAM/GrainBrick/releases) and download:

GrainBrick_beta_1.0_TrimUI_Brick_KNULLI.zip

Do not download GitHub's automatically generated “Source code” ZIP - that is not the application.

## Compatibility

- Tested: original TrimUI Brick with KNULLI
- Requires a compatible AArch64 KNULLI installation providing Python 3.12, Pygame and NumPy
- Other handhelds, operating systems and TrimUI Brick Pro have not been confirmed compatible

## Installation

1. Download the release ZIP and extract its contents.
2. Copy both grainbrick-beta/ and GrainBrick beta 1.0.sh to the Brick's /userdata/roms/ports/ directory.
3. Refresh your PORTS list in KNULLI.
4. Launch GrainBrick beta 1.0.

When upgrading, preserve your own samples, projects, recordings and settings. Do not delete your existing grainbrick-beta/ folder without backing them up.

## Feedback

This is a beta release. Please use the repository's Issues section to report reproducible bugs and hardware compatibility findings, including your OS version and device model.

## Licensing

GrainBrick is free to download, but its original application source code is currently closed. An open public beta does not mean that the GrainBrick source code is open source.

The distribution includes notices and applicable source materials for its bundled third-party components, including LGPL-licensed SoundTouch. See THIRD_PARTY_NOTICES.md, THIRD_PARTY_LICENSES/ and THIRD_PARTY_SOURCES/ inside the downloadable release.
