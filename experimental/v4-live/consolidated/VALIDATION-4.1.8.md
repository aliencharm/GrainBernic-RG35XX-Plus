# V4.1.8 frozen LIVE buffer export

SELECT in the frozen LIVE mixer saves the complete 16-second stereo input ring as 48 kHz / 16-bit PCM WAV in the original samples/recordings folder, without changing LIVE/freeze or replacing the loaded sample. Grain size and roam range do not trim the export. Unfilled history remains silent. Repeated saves use exclusive file creation and unique names; partial writes are removed on failure. The browser refreshes after saving.

56 host tests pass, including chronological partial/wrapped history, early Freeze silence, empty/unacknowledged/unfrozen guards, session reset, exact PCM WAV round trips and unique filenames. A real forked worker test checks that the parent sees child-updated shared cursor/count/Freeze acknowledgement while its private writer/written counters remain zero. Snapshot acquisition is nonblocking; recording file I/O happens in the UI after a copied snapshot, outside the worker lock. While frozen, the worker does not acquire that lock each block.

The original ARM app regression --frozen-save renders synthetic input through the original native DSP, then checks the actual SELECT action writes 768000 stereo frames, validates every saved PCM sample, verifies no grain/range truncation, and keeps the same worker, loaded sample and Freeze state. Not-running and unfrozen saves are rejected. Original renderer screenshots cover Freeze/save hints and saved status. The original native chain/AudioWorker regression checks file return, density/pitch, freeze/resume and 48 shared-reader processing blocks.

The full archive and V4.1.7-to-4.1.8 update overlay pass manifest/inventory/hash checks. Personal recordings/config/state are excluded from the update. Native binaries, audio buffers, monitor behavior, project semantics and palettes are unchanged. USB/process boundaries are mocked for UI checks; on-device audio continuity and save latency require user confirmation.

## V4.1.9 MENU save action

56 host tests pass. The native regression now posts physical MENU down/up events through the actual controller translator, checks the SAVE_FROZEN action and validates complete 16-second WAV output. Logical MENU repeats save successfully and unique filenames preserve previous exports. SELECT is passed through unchanged to the original application. MENU outside frozen LIVE is guarded, and SAMPLE browser MENU navigation is unchanged. Both on-screen and footer hints now say MENU. The V4.1.8-to-4.1.9 update is verified against the full target manifest.
