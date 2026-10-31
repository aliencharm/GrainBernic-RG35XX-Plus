# Original UI LIVE 0.2 validation

The user's probe 0.3 established on the actual RG35XX Plus:

- Original renderer class replacement via the retained main alias succeeds.
- Compiled ParameterBus.set dispatches through a replaced Parameter.set.
- UIEngine(None), draw_tabs and draw_placeholder execute with Mali video and
  V3's display adapter scaling 1024x768 to 640x480.

This implementation directly retains the renderer classes after guarded main
import, constructs its own LIVE page, and starts only the known V4 child.
It does not resume the original main loop or claim to integrate original
sample/FX/ORBIX audio with V4. No AudioWorker handover is required in this build.

New host validation passed:

- Six tests: bootstrap mutation/process guards; runtime V3 write protection;
  only the configured V4 executable may spawn; a fixture main aborts before
  its directory creation while class modules are retained; own real native
  child can execute afterward; shared frontend lock; renderer-startup failure
  closes the display and starts no audio. Some scenarios share a test method.
- Four existing device/config/button/frontend-default tests passed.
- Existing classic Pygame -> native ALSA-null start/control/stop/exit smoke
  passed after introducing the optional renderer interface and lock cleanup.
- New LIVE page end-to-end test uses renderer/ParameterBus fixtures with real
  Pygame dummy video and the real host C engine through ALSA null. It exercises
  six knob calls per frame, LIVE tab dispatch, wet/scatter commands reaching
  engine stats, clean stop/exit and avoidance of original settings-saving close.
- Add-on archive syntax, manifest hashes, expected file membership and shell
  syntax checked. Original V3 tracked files remain unchanged. Existing V4
  engine binary, config/calibration and old frontend are absent from the ZIP.

Still required on the handheld:

- New live page's actual native _draw_comp_knob calls and text layout.
- Combined native renderer + existing engine audio, controller response,
  displayed telemetry and exit/relaunch behavior.
- No hardware success is claimed for this new frontend before that test.

The six-knob host image is generated using fixture widgets and is not a
screenshot of the original ARM64 widget implementation. The actual rendered
widget is selected by UIEngine._draw_comp_knob at runtime on the handheld.
Python audit guards are not an OS sandbox for arbitrary native code; only
this pinned, previously inspected application build is supported.


To rerun host checks from experimental/v4-live after `make` (Pygame required):

```sh
V4_TEST_ENGINE=build/v4-live python3 -B original-ui/test_native_ui.py
python3 -B original-ui/test_live_screen.py build/v4-live
```


## 0.2 settings persistence

Previous LIVE UI 0.1 hardware report: original renderer initialized with Mali
and correct scaling; about 58 seconds of audio with zero recoveries and a
clean exit, with wet/pitch/scatter changes in engine stats. User confirmed
B stops audio and START exits. That establishes the previous graphical/audio
baseline; the new save/restore behavior still needs its quick device check.

New tests passed:

- Seven settings tests: absent-file defaults; round trip excluding wet/gain;
  per-field validation including booleans, nonfinite values and huge integers;
  malformed/unknown-schema reads leave the file unchanged; failed atomic
  replacement preserves old data and removes the temporary file; invalid
  saves rejected; A retains tone controls while resetting wet/gain and queues
  correct engine commands.
- Full two-launch test with the real host engine and ALSA null: pre-A changes
  reach engine stats, settings are not written while streaming, B saves the
  four fields, relaunch restores them, A resets manually raised wet/gain,
  and START exits cleanly while audio is active.
- Native-loader fixture verifies atomic preference saving/loading under the
  installed audit policy while original V3 writes remain blocked.
- Existing six native policy/startup tests, four frontend tests, classic UI
  smoke and six-knob LIVE screen smoke pass with the new settings code.

The native audio engine and its DSP are unchanged; no rebuild was needed.
