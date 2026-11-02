# V4.1.1 project/playback regression evidence

Baseline: user-confirmed V4.1 standalone, commit `6d905f6`.

## Reproduced before the fix

A synthetic saved project with a valid sample and `live.enabled=1` / `live.freeze=1` restored those session flags. The next input poll forced SAMPLE/LIVE into the ready screen despite no deliberate LIVE start. The original preview path worked when an audio file was selected; project loading could leave a folder or unrelated entry selected instead.

## Fix scope

- Filter the two transient session flags when applying/snapshotting project parameters and saving/restoring last-sound state.
- Leave explicit LIVE start, freeze, audio processing and native capture/edit/save behavior intact.
- Switch project/file loads back to browser/file ownership; restart a stopped same-sample worker when loading succeeds.
- Select the loaded file in the sample browser, including a file restored at startup.
- Resolve moved media subpaths or the removed duplicate factory-demo path only when the current matching file is unambiguous. Preserve original project files and native missing-file errors.

## Host and archive checks

36 consolidated host tests pass, including new project/session ownership, worker restart, selection, persistence filtering, safe path relocation and ambiguous-path rejection checks. The update archive is applied virtually to the original V4.1 ZIP and checked against every target manifest hash. No project/sample/recording/configuration files are included in the update.

## Native app regression

The existing `dsp-integration/exercise_original_app.py` now supports `--project-playback`, using `project_regression.py` in an isolated test copy under `work/` or `/tmp/`. It intentionally creates synthetic TEST_* project/media/state fixtures; never run it on a personal installation.

With the existing AUDIO4c/system-mapping fixtures, it verifies:

1. Legacy LIVE flags in saved sound state do not arm the initial file worker.
2. Loading a saved LIVE project, including while LIVE owns the same file worker, returns to the browser with LIVE/freeze disabled and file playback running.
3. A moved sample and the legacy demo path load the correct file; a genuinely missing sample reports SAMPLE NOT FOUND.
4. Original project fixture JSON bytes remain unchanged.
5. The original native DSP renders nonzero file audio with a moving playhead. The exercised fixture produced peak amplitude about 0.054.
6. New project saves and exit state omit session flags without removing sound parameters.
7. START reaches browser preview start/stop through the original event loop, restores worker ownership, and toggles playback in GRAIN.

The native DSP libraries render the signal; preview/process/ALSA boundaries are mocked. A separate run of the original 28-frame REC/LIVE UI exercise also passes, including input/output selection, FX/GRAIN tabs, freeze/mixes, REC delegation, preview and shutdown.

## Limits

These fixtures reproduce the code-level faults without the user's specific project JSON or logs. Physical USB output and the affected projects need a handheld check. Paths that cannot be resolved unambiguously are left with an explicit error. The separate AUDIO4c saved-recording startup click remains unresolved.
