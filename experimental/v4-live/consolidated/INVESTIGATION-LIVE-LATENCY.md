# LIVE latency investigation — V4.2.16 test update

After the source investigation and offline checks, the user authorized a V4.2.16 test update. This release makes recovery optional and removes the cyclic pointer allocations described below. V4.2.15 enables recovery automatically; V4.2.16 defaults to OFF.

## Optional recovery

SETTINGS now includes LIVE RECOVERY, default OFF. A enables it; B disables it. The screen explains that ON skips stale input to catch up after a stall and may alter a note or DAW recording; OFF performs no recovery skips but latency may accumulate. The setting is stored as the boolean `live_recovery_enabled` in config.json, independently of projects/sound parameters. Updates merge the latest configuration so routes and theme are retained. A shared byte makes the switch effective in an already-running audio worker without restarting capture. A failed save leaves the previous setting active.

The capture reader also defaults to OFF when used without the settings controller. Normal one/two-block queues remain unchanged. With recovery enabled, the V4.2.15 catch-up and smoothed-join behavior remains available. This option does not prevent an ALSA underrun or make an overloaded path lossless.

## Evidence from the uploaded log

The V4.2.15 section contains two LIVE sessions. The first runs approximately 583.6 audio seconds and reports two recoveries totaling 6784 skipped frames (141.3 ms at 48 kHz). The second runs approximately 182.5 audio seconds and reports two recoveries totaling 7232 frames (150.7 ms). Each session has one output underrun around 100 ms followed by the recovery counters increasing. Repeated queue reports repeat cumulative counters; they are not additional skips.

Earlier versions show a recurring pattern: a single large approximately 78–101 ms underrun usually occurs around 56–70 seconds of processed LIVE audio after startup. It is present from V4.2.3 and predates the V4.2.14 output-buffer reduction and V4.2.15 recovery. Additional smaller underruns/overruns occur much later in some sessions. The log lacks wall-clock and per-stage timing, so these observations do not distinguish a processing pause, capture starvation, output blocking, OS scheduling or a driver event. They do not establish tape as the source.

## Reproduced backlog mechanism

A real OS-pipe fixture shows that after a stall accumulates input, a reader consuming one block per render can remain behind indefinitely even once producer and consumer advance at the same rate. Recovery addresses that symptom, not the event that originally starved playback.

## Confirmed cyclic allocation in the Stardust wrapper

The original Stardust ctypes handoff calls NumPy `data_as` on three arrays for every audio block. These pointer-owner dictionaries form garbage-collected cycles. With collection temporarily disabled for measurement, 100 blocks leave 600 tracked/unreachable objects. This is also reproduced through the complete original ARM DSP chain under emulation. The actual native audio-worker entry point runs with Python garbage collection enabled.

The V4.2.16 wrapper uses address-only ctypes pointers while retaining strong Python references to the arrays throughout the synchronous native call, and caches the fixed parameter-array pointer. It keeps the same C ABI, processing algorithm and buffers. The host and complete ARM-chain probes now add zero cyclic objects per 100 blocks. A 512-block automated comparison produces bit-identical output against the previous wrapper.

This removes a confirmed source of allocation/collection pressure. It is not yet proof that garbage collection caused the handheld's 100 ms underrun. A clean-state 6500-block emulated DSP run triggers generation 0/1 collections but does not trigger a generation 2 collection, and does not reproduce the logged 100 ms stall. Emulator timings are not Anbernic CPU measurements.

## Validation so far

108 host tests pass, including default-OFF behavior, persistence, preserving routes/theme, failed-save behavior, changing an active capture's shared switch, disabled recovery preserving queued input, normal capture alignment and attacks, and no per-block cyclic pointer accumulation. ARM-emulated tests cover capture queues/settings and the original Settings screen with its explanation, A/B operation and cursor retention. Native app checks retain project/shared-reader behavior, Original/Stardust selection, native REVERB state and full LIVE dry/silent/wet routing. The Settings screen has been visually inspected. No audio devices are opened in these tests.

## Remaining investigation

The user reports clicks throughout the session, not just near startup. The early large underruns therefore do not explain every audible click. Smaller processing overruns, input recovery joins and parameter/effect transitions remain possible contributors; the existing log does not identify each click.

Correlate any future underrun against monotonic block timing, capture-read wall time versus thread CPU time, complete render time, output-write waiting, and garbage-collection generation/duration. This would distinguish CPU work from I/O/scheduling stalls. The existing two-second status messages cannot do that retrospectively. Do not label the cyclic-allocation removal a proven cure or release another build solely on that assumption.
