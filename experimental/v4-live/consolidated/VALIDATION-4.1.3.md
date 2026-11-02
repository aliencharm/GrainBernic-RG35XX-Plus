# V4.1.3 SAMPLE/LIVE mixer validation

The SAMPLE browser now exposes SELECT MIX in its footer. Its second page provides independent GRANULAR MIX, FX MIX and TAPE MIX controls. X opens LIVE READY without capture and returns to the SAMPLE browser. Recording/editor and preview behavior are retained.

44 host tests pass using `/workspace/grainbernik-venv/bin/python -B -m unittest discover -s experimental/v4-live/consolidated -p 'test_*.py'`. The system Python lacks pygame; use the development environment for this suite.

ARM-emulated checks run the unchanged original native app and DSP with the packaged adapters:

- `exercise_original_app.py --integrated --final-entry --channel-routing --system-mapping --sample-mixer`: original native SAMPLE granular dry/half/full math and exact default passthrough; original FX/Tape bypass/half/full math; separate LIVE controls; SELECT routing, X ready transitions, LIVE start/freeze/stop, original recording and preview delegation.
- The original chain inspector with packaged `live_source` and `stage_mix` preloaded: native density/pitch, freeze/resume, file return, and original AudioWorker shared-parameter processing across 48 blocks pass.
- `--project-playback`: saved playing projects load paused, relocated media resolves, native file output and moving read head, preview and explicit playback pass.
- `--record-ui`: original recording page, LIVE across GRAIN/FX, freeze/stop, recording start/stop and clean shutdown pass.

Screenshots from the original renderer were inspected for the SAMPLE browser with long paths/names, SAMPLE mixer and footer hints. No native engine binary, buffer timing, saved WAV processing or Amber palette is changed.

The complete target archive passes inventory, hash, layout and license verification. The small update is virtually overlaid on V4.1.2 and checked against the complete target manifest. It contains no personal media, configuration or state.

OS audio/capture/process boundaries are mocked in UI tests. Real interface latency, sound and control feel need handheld confirmation. The existing AUDIO4c recorded startup click remains unresolved.
