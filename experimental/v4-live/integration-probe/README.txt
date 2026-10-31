GrainBrick V3 interface inspection probe 0.1
===========================================
Purpose: find runtime Python class/method metadata exposed by the installed
compiled V3 package, before deciding whether V4 can reuse the original UI.
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
   If no report appears, send the inspection log.

WHAT IT DOES
Uses the same installed system Pygame / NumPy fallback / surfarray preload
as the working V3 launcher. A child Python process attempts to import the
installed main extension with guarded startup. Pygame initialization and
display/audio/joystick startup are intercepted. Python-level file mutations,
process spawning, socket connections and direct audio-library loads are
blocked by an audit hook. A metadata snapshot is collected at that boundary.
Only the two report/log files in the V4 directory are intentionally written.
No class constructors, DSP functions, UI methods or playback commands are
called by the metadata inspection itself. No proprietary files are bundled.

BOUNDARIES
These are Python-level guards, not a separate OS filesystem sandbox for
native code. The tool is for this known installed beta package only. Reports
may be partial if the compiled loader tries a blocked operation early. A
missing class or method in a partial report does not prove it is unavailable.
Compiled module globals and method metadata are evidence only: successful
attribute replacement and actual compiled call dispatch must be tested later.
Do not launch V3 or V4 during the inspection.

TESTING
Five host fixture tests passed: method argument/default metadata extraction,
blocked file writes, blocked directory creation, blocked subprocess startup,
and rejected output paths inside the V3 tree. Bytecode writing was disabled.
The actual compiled V3 module is ARM64 Python 3.12 and cannot be imported by
the x86_64 cloud interpreter. This diagnostic still needs the handheld run.

REMOVAL
Delete only GrainBrick V4 Inspect.sh and grainbrick-v4-live/inspect_v3.py
if desired. V3 and the working standalone V4 remain as installed.
