# GrainBrick V4 Integrated 0.1 — experimental hardware-test build

Continuous USB input routed through the ORIGINAL beta 1.0 GranularEngine and DSPChain, running the original application and tabs. This is separate from the previous standalone V4 / Original UI LIVE frontend. It is not yet validated on the RG35XX Plus with real USB audio.

## Install

Requires the working V3 in `/userdata/roms/ports/grainbrick-beta/` and the working V4 device configuration in `/userdata/roms/ports/grainbrick-v4-live/config.json`.

Extract this ZIP into `/userdata/roms/ports/`, merging its `grainbrick-v4-live` folder with the existing folder. It adds three Python files and a new launcher; it contains no configuration or preference files to overwrite. Launch **GrainBrick V4 Integrated**. Close V3 and other V4 launchers first.

First launch copies the installed original application into `grainbrick-v4-integrated/`; allow extra startup time. The V3 directory stays unchanged. Original binaries are checked against the inspected beta main SHA-256. User recordings, samples and projects are not copied. The integrated copy has its own recordings, samples, projects and saved DSP state. No proprietary original binaries are distributed in this ZIP.

## Short first test

1. Connect Tascam, disable its direct monitoring and lower headphone volume.
2. In the original SAMPLE browser, press Y to open RECORD INPUT.
3. Press X to choose LIVE, then A to start. Each new live start resets wet mix to 0%.
4. Verify dry input, then press D-pad right/left to raise/lower wet mix. Allow history to fill. Y toggles freeze; dry input continues while the granular buffer holds.
5. Use the original tab navigation to GRAIN and FX. Density, grain size and pitch in semitones are the original controls. Try an audible delay/reverb change, then return to SAMPLE to change live mix.
6. B stops LIVE; B again backs out. X selects REC when stopped; A then uses the original recording action. Exit with the original START + SELECT combination.

Suggested first granular test: size 20–60 ms, pitch 0 semitones, position centered, spray 0. Larger grains add audible wet delay. Live position is relative to the advancing write position; centered follows recent input. Spray scales with available history while the buffer fills. Freeze holds 16 seconds of RAM history; it does not save a WAV.

The live dry/granular mix feeds the original downstream DSP chain, so downstream FX affect the mix. This is not an effects bypass. Original file-mode granular behavior is retained. Existing standalone V4 settings are not imported into the original DSP controls.

## Send back

After a short test and a clean exit, send:
- `grainbrick-v4-live/v4-integrated.log`
- `grainbrick-v4-integrated/audio_process.log` (if created)
- Screenshot and observations: dry input, wet granular input, original FX, freeze, stop/restart and REC mode.

The first log appends across launches. The original audio worker manages its own log. If launch fails, the integrated log includes the traceback. USB capture failures stop the worker rather than silently substituting audio.

## Validation and limits

Ten host tests passed: buffer/freeze/mixing/parameter forwarding, pause cleanup, capture framing/timeout/EOF, isolated installation and device config validation. ARM64 CPython 3.12.8 emulation executed the actual original native granular engine, delay effects, DSPChain and AudioWorker processing loop with synthetic input. The original main/UI loop passed REC/LIVE routing, GRAIN/FX navigation, freeze, stop, original REC delegation and shutdown with hardware/process boundaries mocked.

These checks do not establish handheld duplex timing, CPU load, USB recovery or real ALSA operation. Hardware testing is required before claiming the integrated mode works. Keep the previously working launchers as fallbacks.
