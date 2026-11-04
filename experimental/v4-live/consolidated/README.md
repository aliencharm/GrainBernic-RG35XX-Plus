# GrainBrick V4.2 — RG35XX Plus

A complete standalone AntevasinBuild based on official **ETRNLIAM GrainBrick beta 1.0**. This V4.2 standalone consolidates the working V4.1.10 controls, SAMPLE/LIVE mixers, project fixes, themes and frozen-buffer saving. The current update revision is **4.2.12**; it adds the optional Stardust shimmer and retains the V4.2 controls and dry-playback fixes. No earlier installation or patch chain is required.

Target: **Anbernic RG35XX Plus / KNULLI Scarab 20260511**, with system Python 3.12, Pygame and ALSA tools. The required NumPy runtime is bundled.

## V4.2.12 Stardust preview

This is the granular-core device-test build of Stardust, an independent native ARM shimmer. Close GrainBrick and merge `GrainBrick_V4.2.12_Stardust_Preview_Update.zip` into an installed V4.2 / V4.2.1 / V4.2.2 / V4.2.3 / V4.2.4 / V4.2.5 / V4.2.6 / V4.2.7 / V4.2.8 / V4.2.9 / V4.2.10 / V4.2.11 folder. Keep the V4.2 launcher, personal media and settings. No desktop VST is included or hosted.

In FX, open **SHIMMER**. **TYPE** is in the upper header, with its hint below. Move up from the first control row to select TYPE, then use A/B for Original/Stardust. **MENU** switches the type directly while on this category. **L2 selects the previous effect; R2 selects the next**, wrapping at either end. X no longer advances FX. Y retains Fine/Coarse adjustment. L2/R2 keep their existing input-selection function in SAMPLE/LIVE. The selected type and both sets of parameters are saved with the project. Older projects default to Original.

This test build separates reverb dimensions, grain duration, texture intensity and modulation speed. All 13 controls are visible together in a five-column grid, with TYPE still above the grid. Size affects only the reverb network. Grain Size sets duration independently (20–100 ms); Texture Depth controls scattering/micro-detuning without changing duration. Granular Rate sets the rate of smooth irregular movement, without changing grain duration. New LFO Rate and LFO Depth add independent periodic sine pitch modulation to the pitched grain branch. LFO Depth defaults to 0% (off); full depth is about +/-50 cents. Granular Mix is deliberately omitted. Existing Input/Send/Return and internal pitched/unpitched scalar balances remain. Older projects receive 60 ms Grain Size and LFO off; they retain their saved reverb Size. These intentional control separations change older Stardust sounds, while Original is unchanged. The LFO reuses the existing grain path and window lookup table, adding no second pitch engine or FFT.

Original retains the native GrainBrick shimmer and its controls. Stardust provides:

- **Pre Delay:** -1000 to +1000 ms. Positive delays the send to Stardust; negative delays its dry/base path.
- **Size / Decay:** reverb dimensions and relative tail length. Neither sets grain duration.
- **Grain Size:** independent grain duration, 20–100 ms (with small asynchronous variation).
- **Pitch:** -12 to +12 semitones, in the wet return and the recirculating shimmer path.
- **Brightness:** warm low-mid pitched body at low values, opening into an airy bright tail at high values. Dark downward shifts include gentle harmonic definition to reduce sub-bass-only humming. Anti-alias protection remains separate.
- **Granular Rate / Texture Depth:** rate (0.05–5 Hz) of irregular movement, and amount of scatter/micro-detuning. They do not change grain duration. Texture Depth 0% removes added irregularity; it does not turn off the granular pitch shifter.
- **LFO Rate / LFO Depth:** independent sine modulation rate (0.05–5 Hz) and pitch excursion (0–about +/-50 cents). LFO Depth 0% is off regardless of LFO Rate.
- **Input / Send / Return:** base-path level, feed to Stardust and calibrated wet-tail level. Return is substantially stronger than in earlier previews; start around 50%. Input scales the existing FX output in this mode; Send feeds Stardust independently from the FX input.

The existing REVERB category, native engine and parameters remain unchanged. Stardust adds its own feedback-delay network and pitch-shift loop in the shimmer slot. Only the selected shimmer algorithm processes audio; switching resets shimmer history and uses a brief transition fade. Original projects retain their original default path.

Start a sample or LIVE input, set its **FX MIX above 0%**, choose Stardust and try Input 100%, Send 100%, Return 50%, Pitch +12 ST, Grain Size 60 ms and LFO Depth 0%. Return 0% removes the Stardust tail; Send 0% lets the existing tail decay. Ordinary reverb remains available independently.

The DSP is implemented in C; Python handles selection and controls. Host and ARM-emulated tests check stability and compatibility, but they do not establish handheld CPU headroom or subjective sound quality. On device, compare the DSP meter/overruns under your usual granular/tape workload. For a separate timing check, close the app, put the optional `GrainBrick_Stardust_Profile.sh` in ports and launch it. It writes `grainbrick-v4/Stardust_Profile.txt` with readable permissions and opens no audio device. The updated probe reports elapsed and thread CPU time separately, with separate LFO-off and maximum-LFO cases on this build. It measures Stardust alone, excluding the rest of GrainBrick. LIVE captures USB data inside the render path; its DSP time may include capture waiting and is not necessarily a pure CPU-utilization percentage.

The provided Luminance manual, screenshot and preset values informed the control reference. Stardust is an independent implementation, not a bit-exact recreation. The uploaded VST and preset bank are not bundled.

## V4.2.2 SAMPLE mixer controls

Close the app and merge `GrainBrick_V4.2.2_Update.zip` into installed V4.2 or V4.2.1. Keep the GrainBrick V4.2 launcher, media and settings. START is now the only play/pause button on the SAMPLE mixer; A is unassigned there. A still loads files in the browser and toggles Freeze in LIVE. The update includes the V4.2.1 dry-playback fix and leaves audio processing unchanged from that revision.

## V4.2.1 SAMPLE dry playback update

For an installed V4.2, close the app and merge `GrainBrick_V4.2.1_Update.zip` into the existing ports folder. Keep the GrainBrick V4.2 launcher, media and settings.

The SAMPLE mixer now plays the original file when its mix controls are zero, without requiring ROAM. Turning GRANULAR off also passes the original sample through, even if GRANULAR MIX is still at 100%. Enabled processing is blended in as its mix increases. Dry playback loops at the original sample rate and follows play/pause. The native granular engine remains the fully wet path; LIVE controls, Freeze/export and SAMPLE recording are unchanged.

## Clean installation

Close GrainBrick before changing files. Extract `GrainBrick_V4.2_Standalone.zip` into `/userdata/roms/ports/`. It provides exactly:

```
ports/
  GrainBrick V4.2.sh
  grainbrick-v4/
```

Connect the USB interface before launching **GrainBrick V4.2**. First launch verifies the runtime and creates configuration. Existing KNULLI controller mappings are used; otherwise calibration runs. Original Amber is the default theme.

The archive contains runtime modules, unchanged native application/DSP libraries, required resources, a pruned NumPy runtime, one factory demo and AMBIENT project, documentation and required legal materials. It excludes development/test files, caches, compiler tools, old updates, logs, diagnostic reports, user configuration and personal media. Normal logs and preferences are created when the app runs.

## Bring your development data into the final build

The separate `GrainBrick_V4.2_Import_Data.sh` tool imports existing personal data on the handheld. Keep a backup until you have confirmed the import.

1. Close GrainBrick. Rename the current `ports/grainbrick-v4` folder to **`ports/grainbrick-v4-backup`**. Keep that folder intact. If a backup with that name already exists, preserve it elsewhere before renaming the current working app folder.
2. Extract the final standalone ZIP into `ports/`, creating the new `grainbrick-v4`. Use the supplied GrainBrick V4.2 launcher. Move the old GrainBrick V4.1.sh launcher off ports to avoid duplicate entries. The app folder remains grainbrick-v4 for data-path compatibility.
3. Put **GrainBrick_V4.2_Import_Data.sh** directly in `ports/`, refresh PORTS and launch it once before using the new app.
4. It copies `samples/` (including `samples/recordings/`), `recordings/`, `projects/`, and existing `config.json`, `settings.json`, `sound_state.json`, `gb_buttons.json` and `button_mapping.json` into the new installation. Your previous theme, routes and controls are retained. Old runtime files, root logs, diagnostic reports and generated ALSA/lock/setup files are not imported.
5. Check `grainbrick-v4/Import_Report.txt` for **IMPORT COMPLETE**, then launch GrainBrick V4.2 and check your projects and recordings. The importer preserves the backup and refuses to overwrite conflicting new personal media. Re-running after a completed import leaves files unchanged.
6. After verifying everything, move the backup and the optional import/USB-check scripts off the handheld if you want a clean PORTS folder.

For manual import, copy the same data folders and JSON files from the backup with the app closed. Copy entire directory trees so nested media paths remain available. A project references a sample; it does not embed its audio or a temporary LIVE buffer. Existing project loading resolves unambiguous legacy media paths and reports genuinely missing files. Projects load paused, and saved transient LIVE flags are ignored.

## SAMPLE/LIVE controls

The SAMPLE browser is the main SAMPLE screen:

- **A:** load the selected sample. **START:** preview any selected sample, including the loaded file.
- **SELECT:** open the SAMPLE mixer; **SELECT/B** returns to the browser.
- **Y:** original recording workflow. Y or B stops recording into the original editor; original edit/save controls remain.
- **B on a file:** ask to delete it; B again confirms, A cancels. Moving selection or leaving the page cancels confirmation. Deleting a loaded file stops playback and unloads it.
- **MENU or LEFT:** go up a folder. B on folders retains back behavior.
- **L2/R2:** select the USB input pair. **X:** open LIVE READY.

The SAMPLE mixer has separate GRANULAR MIX, FX MIX and TAPE MIX controls. Up/down selects a mix; left/right adjusts it. START plays/pauses the sample; A is unassigned on the SAMPLE mixer screen. Defaults are 100% and old projects retain their original playback. LIVE mix settings are separate.

In LIVE:

- **Y:** start/stop LIVE, including when frozen or paused.
- **A:** Freeze on/off only.
- **SELECT:** existing pause/resume behavior.
- **B:** stop LIVE and stay on its screen; B again returns to SAMPLE.
- **X:** stop LIVE and return directly to the SAMPLE browser.
- **D-pad:** select/adjust GRANULAR, FX and TAPE MIX. L2/R2 changes input pair and stops LIVE.
- **MENU while frozen:** save the complete held input buffer.

Footer hints reflect the current state. Other tabs retain their original controls. **START + SELECT exits globally.**

## Save the whole frozen LIVE buffer

Start LIVE, freeze with A, then press MENU. Look for **SAVED LIVE_FREEZE...** below the controls. Files are stereo 48 kHz / 16-bit PCM WAVs in:

```
grainbrick-v4/samples/recordings/LIVE_FREEZE_YYYYMMDD_HHMMSS.wav
```

The export contains the full **16-second input buffer** in chronological order, including audio outside the grain/roam selection. Freezing before the buffer fills retains silence in the unused part. It saves input audio before granular, FX and tape processing. LIVE stays frozen and keeps playing. Repeat saves get unique names and do not overwrite existing recordings. Return to the SAMPLE browser root and open recordings to load the file.

## Settings, USB and themes

RG35XX Plus has no built-in microphone. Only detected USB inputs are offered; without one, NO USB INPUT is shown. Sample playback and ORBIX remain available without USB. Select the wanted output in SETTINGS; Internal output can be used with a connected USB input. Connect USB before launch and restart the app after changing interfaces.

Interface labels identify USB channel pairs, not physical jacks or DAW routing. AUDIO4c pairs 1-2, 3-4, 5-6 and 7-8 are supported. Routing is per app through generated `alsa-routing.conf`; system/interface routing is not changed. Disable external direct monitoring or feedback loops when using software monitoring.

Themes are Amber, Mint, Ice, Violet, Sage and Spruce. In SETTINGS → THEME, A/B cycles and saves immediately. Amber remains unchanged; custom themes retain the approved dark backgrounds, palette-tinted text/graphics and brighter selected controls. SETTINGS retains the AntevasinBuild / official ETRNLIAM beta credit.

## Known limits and diagnostics

The AUDIO4c click at the beginning of saved REC audio remains unresolved; the user reported Tascam free of that recording-start click. Saved recording audio is not faded, trimmed or otherwise altered. The tested LIVE output request remains 2048 frames / 512-frame periods.

A Tascam connection through the tested charging/data splitter did not appear in Linux USB/ALSA inventories, while direct connection worked. The dongle worked on an iPad; compatibility with the handheld/KNULLI USB setup is unconfirmed. No app workaround is claimed.

Normal logs are `v4.log` and `audio_process.log` inside the app folder. The optional USB Check v2 script saves `GrainBrick_USB_Report.txt` there with explicit network-readable permissions. Optional REC diagnostic environment switches remain `GRAINBRICK_REC_MONITOR=0` and `GRAINBRICK_REC_CAPTURE_TIMING=original`; they do not modify saved WAV samples.

## Credits and validation

The original proprietary native app and DSP are unchanged. Preserve `CREDITS_V4.md`, the original `README_EN.md`, third-party notices/licenses and supplied compliance sources. This port does not relicense the original app.

The final archive passes inventory, hashes, original-engine, executable launcher, factory media and license checks. Host tests cover the runtime and data import. ARM-emulated original-app checks cover LIVE controls, full frozen WAV export, paused project loading and original DSP processing. OS audio/process boundaries are mocked in UI checks; hardware timing still needs on-device confirmation. Detailed evidence and historical changes remain in the repository, outside the runtime package.

To rebuild Stardust from source, run `python3 experimental/v4-live/stardust/build_native.py` with an ARM64 cross compiler (optional `--cc` / `--sysroot`), then use the normal package builder. Development source/tests/profile helpers stay outside the installed runtime.
