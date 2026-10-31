# GrainBrick V4 Integrated 0.1.7 — experimental hardware-test build

Continuous USB input routed through the ORIGINAL beta 1.0 GranularEngine and DSPChain, running the original application and tabs. This is separate from the previous standalone V4 / Original UI LIVE frontend. It is not yet validated on the RG35XX Plus with real USB audio.

## Install

Requires the working V3 in `/userdata/roms/ports/grainbrick-beta/` and the working V4 device configuration in `/userdata/roms/ports/grainbrick-v4-live/config.json`.

Extract this ZIP into `/userdata/roms/ports/`, merging its `grainbrick-v4-live` folder with the existing folder. It adds five Python files and a new launcher; it contains no configuration or preference files to overwrite. Launch **GrainBrick V4 Integrated**. Close V3 and other V4 launchers first.

First launch copies the installed original application into `grainbrick-v4-integrated/`; allow extra startup time. The V3 directory stays unchanged. Original binaries are checked against the inspected beta main SHA-256. User recordings, samples and projects are not copied. The integrated copy has its own recordings, samples, projects and saved DSP state. No proprietary original binaries are distributed in this ZIP.

## Short first test

1. Connect Tascam, disable its direct monitoring and lower headphone volume.
2. In the original SAMPLE browser, press Y to open RECORD INPUT.
3. Press X to choose LIVE, then A to start. Each new live start resets wet mix to 0%.
4. Use D-pad up/down to select GRANULAR MIX, FX MIX or TAPE MIX; left/right changes the selected knob in 5% steps. Verify input, then raise GRANULAR MIX. Allow history to fill. Y toggles freeze; dry input continues while the granular buffer holds.
5. Use the original tab navigation to GRAIN and FX. Density, grain size and pitch in semitones are the original controls. Try an audible delay/reverb change, then return to SAMPLE to adjust the three mixes.
6. B stops LIVE; B again backs out. X selects REC when stopped; A then uses the original recording action. Exit with the original START + SELECT combination.

Suggested first granular test: size 20–60 ms, pitch 0 semitones, position centered, spray 0. Larger grains add audible wet delay. Live position is relative to the advancing write position; centered follows recent input. Spray scales with available history while the buffer fills. Freeze holds 16 seconds of RAM history; it does not save a WAV.

The raw/granular blend feeds the original downstream DSP chain. The new FX and Tape mixes blend around their respective original stages; EQ, compression and ORBIX retain their existing controls. Original file-mode granular behavior is retained. Existing standalone V4 settings are not imported into the original DSP controls.

## SAMPLE/LIVE tab label (0.1.7)

The visible SAMPLE header is now SAMPLE/LIVE. It uses the original small font to fit in the existing tab slot. Only the displayed label changes; tab routing and sample browsing retain the original SAMPLE identifier. The original main/UI regression check passed under ARM emulation. No audio processing changes from 0.1.6.

## Three original-style mix knobs (0.1.6)

The existing RECORD INPUT page in LIVE mode now has GRANULAR MIX, FX MIX and TAPE MIX knobs drawn by the original app's knob renderer. D-pad up/down selects a knob; left/right changes it by 5%. A starts/resumes LIVE, B stops, Y freezes, and X switches REC/LIVE when stopped. Original tab navigation is retained.

- GRANULAR MIX is the previous live.mix control: raw input at 0%, original granular output at 100%.
- FX MIX blends the signal entering the original delay/reverb/shimmer stage with that stage's output. 0% bypasses its audible contribution, 100% preserves its existing sound and individual FX mix settings. This is a group blend, not three separate per-effect replacements.
- TAPE MIX blends the input to the original tape stage with that stage's output. 0% bypasses its audible contribution, 100% preserves the original Tape sound. Tape must be enabled and configured to hear its contribution.

Processing order remains source blend -> input gain -> EQ -> compressor -> FX stage blend -> Tape stage blend -> ORBIX addition -> master gain. EQ, compression and ORBIX are outside the FX/Tape blend controls. The new stage mixes apply to LIVE only; file playback and dry REC monitoring keep their prior processing. With all three mixes at 0%, raw input still passes through any enabled EQ/compression/ORBIX and level controls.

FX and Tape default to 100% for compatibility with 0.1.5. Their values are saved by the original sound-state mechanism, according to its save settings. GRANULAR MIX still resets to 0% on a fresh LIVE start. Stage mix changes ramp across one processing block (about 11 ms). Linear mix behavior is retained without automatic gain normalization. Both original stages keep running at 0% to maintain their state/tails, so lowering the new knobs does not eliminate their CPU cost.

28 host tests cover mixing endpoints, in-place native buffer behavior, separate controls, smooth transitions, unchanged original stage output at 100%, transport argument forwarding, file-mode passthrough and prior LIVE/REC behavior. Actual original ARM64 DSP tests verify native delay bypass/identity, native Tape bypass/identity and the original AudioWorker loop with both stage wrappers and shared parameter reading. The actual original app event loop verifies three-knob input, freeze, original tabs and REC delegation with audio mocked. These new stage blends still need handheld testing; 0.1.5 remains the validated fallback.

## LIVE output latency retained from 0.1.5

The selected 0.1.3 dry REC monitor and the user-tested 0.1.5 LIVE output buffering are retained. Original AudioOutput uses a 7168-frame low-latency buffer, 512-frame period and 8192-byte output pipe. LIVE requests 2048 frames, the same 512-frame period and a 4096-byte pipe. At 48 kHz, the requested output buffer capacity falls from about 149 ms to 43 ms. These are buffer capacities, not measured end-to-end latency. The original values are restored on LIVE stop/error/exit; REC monitoring retains the 0.1.3 configuration.

At LIVE wet mix 0%, input bypasses the granular mix, but still passes through USB capture/output and the original downstream FX/DSP. Delay/reverb/tape/other enabled effects can contribute their own response. For a latency comparison, use a synth patch with a sharp attack, wet 0%, downstream effects off, and comfortable DSP headroom. Compare the onset with 0.1.3. Then test usual FX and note any clicks. Smaller buffers reduce scheduling tolerance, so this build needs hardware testing. No zero-latency claim is made.

`v4-integrated.log` prints `ORIGINAL LIVE OUTPUT REQUEST` and `ORIGINAL LIVE OUTPUT ACTIVE`, including whether original low-latency startup succeeded. An active flag confirms the original startup branch, not independently queried ALSA hardware timing. Send both logs if latency persists or clicks increase. 21 host tests passed; ARM-emulated original main and actual original AudioOutput argument/start/restore checks passed with audio process creation mocked.

## REC monitoring retained from 0.1.3

REC plays the unprocessed recorded PCM at unity gain, without the granular/FX chain. It retains the original arecord WAV writer, format, path and edit/save workflow, with the 0.1.3 capture request of 24 ms buffer / 6 ms period. It follows the growing WAV and uses a 64 ms output buffer / 8 ms period, with no sample skipping or gain conversion. These capture timing changes differ from unmodified V3; 0.1.4 remains available if original REC without software monitoring is wanted. This build deliberately retains the monitoring behavior the user selected after testing both.

Keep Tascam direct monitoring off. Record a short sample, check dry monitoring, stop/cancel and repeat. The added REC monitor cannot write to the recorded file; failure is logged while the original recording continues. Previous user tests reported this configuration working. Latest hardware latency testing is pending.

## Recording denoise availability

On the recorded-sample edit page, L2 decreases and R2 increases the ORIGINAL denoise percentage by 5 points per press. Existing Y + directional controls are retained. This mapping does not add denoise to live mode. The original denoise availability check is respected; unavailable recordings show an explicit message. The original denoiser is for built-in microphone recordings. RG35XX Plus has no built-in microphone, so it is unavailable for this Tascam USB recording workflow. The edit page now states that limitation. No USB denoising is added.

Four additional tests passed for button delegation, unavailable recordings, release handling and keeping other tabs/live controls unchanged. Real original main/UI regression tests passed again under ARM emulation. Handheld button mapping and actual denoise processing still require testing.

## Send back

After a short test and a clean exit, send:
- `grainbrick-v4-live/v4-integrated.log`
- `grainbrick-v4-integrated/audio_process.log` (if created)
- Screenshot and observations: dry input, wet granular input, original FX, freeze, stop/restart and REC mode.

The first log appends across launches. The original audio worker manages its own log. If launch fails, the integrated log includes the traceback. USB capture failures stop the worker rather than silently substituting audio.

## Validation and limits

Ten host tests passed: buffer/freeze/mixing/parameter forwarding, pause cleanup, capture framing/timeout/EOF, isolated installation and device config validation. ARM64 CPython 3.12.8 emulation executed the actual original native granular engine, delay effects, DSPChain and AudioWorker processing loop with synthetic input. The original main/UI loop passed REC/LIVE routing, GRAIN/FX navigation, freeze, stop, original REC delegation and shutdown with hardware/process boundaries mocked.

These checks do not establish handheld duplex timing, CPU load, USB recovery or real ALSA operation. Hardware testing is required before claiming the integrated mode works. Keep the previously working launchers as fallbacks.
