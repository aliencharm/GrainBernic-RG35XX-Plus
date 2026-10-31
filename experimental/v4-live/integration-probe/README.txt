GrainBrick V3 interface inspection probe 0.2
===========================================
Purpose: verify in-memory class replacement, parameter method dispatch and
original renderer construction in a dummy off-screen display. The preceding
0.1 report successfully captured every target module on the handheld.
This is NOT a new V4 engine or a live-mode integration patch.

INSTALL AND RUN
1. Exit V3 and V4 completely.
2. Copy GrainBrick V4 Inspect.sh into /userdata/roms/ports/.
3. Copy inspect_v3.py into the EXISTING
   /userdata/roms/ports/grainbrick-v4-live/ directory.
   Do not replace any other V3/V4 file, config or calibration.
4. Refresh PORTS and run GrainBrick V4 Inspect once.
   It does not show the V3 interface. It should return to PORTS within
   20 seconds (plus Python startup).
5. Send BOTH files from grainbrick-v4-live/:
     v3-api-report.json
     v3-inspect.log
   Also send v3-ui-preview.png if it was created. It is an off-screen image,
   not the handheld display. If no report appears, send the inspection log.

WHAT IT DOES
Uses the same installed system Pygame / NumPy fallback / surfarray preload
as the working V3 launcher. A child Python process attempts to import the
installed main extension with guarded startup. Pygame initialization and
display/audio/joystick startup are intercepted. Python-level file mutations,
process spawning, socket connections and direct audio-library loads are
blocked by an audit hook. A metadata snapshot is collected at that boundary.
After the import boundary, the tool temporarily replaces and restores the
Parameter.set and UIEngine.draw methods to test replacement/dispatch. It
constructs fresh parameter/control objects. Pygame display calls are then
restored ONLY with dummy video/audio backends, to construct the original
UIEngine and draw its tabs/placeholder off-screen. Device enumeration is
stubbed during that check. No AudioWorker, DSP engine, recording, PCM or
playback process is started. Filesystem/process guards stay active.

The report/log and optional preview PNG in the V4 directory are the only
intended file changes. Original methods are restored after each check.
No proprietary files are bundled.

BOUNDARIES
These are Python-level guards, not a separate OS filesystem sandbox for
native code. The tool is for this known installed beta package only. Reports
may be partial if the compiled loader tries a blocked operation early. A
missing class or method in a partial report does not prove it is unavailable.
Read each compatibility result separately. A successful parameter call path
and renderer alias check do not prove that original main's event loop can
be redirected, or that its original audio worker safely stops/restarts.
Do not launch V3 or V4 during the inspection.

TESTING
Nine host tests passed: metadata/argument extraction, blocked file writes,
directory writes and process starts, rejected V3 output paths, parameter
setter interception/restoration, renderer class replacement/restoration,
missing-module failure reporting and dummy-display PNG rendering. These
use fixture classes, not the actual ARM64 application. Bytecode writes are
disabled. Actual compiled-class behavior still needs this handheld check.
The actual compiled V3 module is ARM64 Python 3.12 and cannot be imported by
the x86_64 cloud interpreter. This diagnostic still needs the handheld run.

REMOVAL
Delete only GrainBrick V4 Inspect.sh and grainbrick-v4-live/inspect_v3.py
if desired. V3 and the working standalone V4 remain as installed.
