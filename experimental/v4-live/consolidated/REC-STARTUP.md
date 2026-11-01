# Saved REC WAV startup click investigation

UI Test 1.4 baseline: `57192d4a8db84e6fcfc2c2ef0463ec1c3f326dc7`.
The reported click is in the saved WAV. No affected WAV or matching device log
is available in this checkout, and USB hardware is unavailable in the cloud.
A root cause or successful fix cannot yet be claimed.

## Confirmed code path

`RecordingUI` delegates REC to the original `main.start_input_recording`.
`LiveController.install_record_monitor` stops the existing audio worker, calls
the original recorder, then starts `RecordingMonitor` on the growing WAV.
The original recorder owns capture and WAV writing. The monitor opens the WAV
read-only and sends its data to a separate `aplay` process. The 10 ms fade is
applied only to a copied playback buffer; it cannot change a saved click.
The original editor/save actions are retained.

Two startup differences deserve controlled hardware testing:

- V4 adds `--buffer-time=24000 --period-time=6000` to the original WAV capture
  command. Shorter periods could expose capture overruns, but no overrun evidence
  establishes that as the cause.
- V4 opens monitor playback after capture has begun, on the selected interface.
  A duplex stream/clock transition or an external monitor feedback path could
  reach capture. This is a hypothesis, not a confirmed interface defect.

A nonzero first sample or an ordinary signal beginning at the record boundary
can also click on playback without a corrupt capture. Inspect the actual WAV
and compare an independent capture before attributing the click to either path.

## Controlled on-device comparison

Use the same pair, output, source signal, gain, and interface routing for each
run. Disable interface/DAW direct monitoring or return feedback for all runs.
Start a quiet-input recording, then repeat with a steady source. Keep the raw
recordings; do not trim, fade, denoise, replace samples, or resave through an
external editor. Listen and compare the original WAVs at the same gain.

Set these variables before the `python3` command in `GrainBrick V4.sh`, and
restart the whole app between cases:

| Case | `GRAINBRICK_REC_MONITOR` | `GRAINBRICK_REC_CAPTURE_TIMING` |
| --- | --- | --- |
| A: current behavior | unset | unset |
| B: no monitor playback | `0` | unset |
| C: original capture timing, no monitor | `0` | `original` |
| D: original capture timing, with monitor | unset | `original` |

Example for C:

```sh
export GRAINBRICK_REC_MONITOR=0
export GRAINBRICK_REC_CAPTURE_TIMING=original
```

These are opt-in isolation controls. Defaults retain UI Test 1.4 capture timing
and monitor behavior. Disabling the monitor does not disable recording, change
its device/format/path, or alter its samples. Original timing merely passes the
original capture command through without V4's two latency flags. Other recording
lifecycle changes, including stopping the worker, remain in all four cases.
LIVE DSP is unchanged. Remove the exports to restore defaults.

If only monitored cases click, investigate playback-open timing and external
routing. If only short-period cases click, check capture overruns and negotiated
ALSA timing. If every case clicks, compare standalone `arecord` with the same
PCM/format and inspect the original record boundary and editor/save path. These
comparisons narrow causes; none alone proves a hardware fault.

Collect each case's unedited WAV, `v4.log`, `audio_process.log`, `config.json`,
interface model/routing, and whether the click is at frame zero or later.
No saved-audio suppression or speculative capture fix is implemented.

## Cloud validation

18 consolidated host tests pass, including unchanged monitored WAV bytes, exact
original command passthrough, and disabled-monitor isolation. The 1.5 standalone
ZIP passes manifest hash verification and ZIP integrity checks against the
verified original beta. The original native app passes a 28-frame ARM-emulated
UI run with AUDIO4c descriptors: input switching, LIVE/freeze/mix, REC start/stop
delegation, preview, and clean exit. Browser and ready-page screenshots were
inspected. Hardware and file recording are mocked in that UI run; it cannot
reproduce or validate a USB startup-click fix.
