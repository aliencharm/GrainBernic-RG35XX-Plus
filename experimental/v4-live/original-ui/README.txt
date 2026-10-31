GrainBrick V4 Original UI LIVE 0.2 — experimental frontend
=========================================================
REQUIRES the working V4 engine 0.1.1 and your existing V3 installation.
This add-on uses the ORIGINAL installed GrainBrick UIEngine: its pixel font,
tab bar, and compressor-style knob widget form a new LIVE control page.
It controls the same tested V4 C audio engine. No new audio binary is shipped.
The previous 0.1 LIVE screen passed the handheld control/audio test. This
0.2 update adds remembered tone controls; it uses the same renderer and
unchanged audio engine. Save/restore and startup behavior passed host tests.

INSTALL
1. Exit V3 and V4 completely.
2. Extract this ZIP and copy GrainBrick V4 Original UI.sh to:
     /userdata/roms/ports/
3. Copy the three .py files from grainbrick-v4-live/ into your EXISTING:
     /userdata/roms/ports/grainbrick-v4-live/
   New files: original_ui_entry.py, native_ui.py, live_frontend.py.
   Keep v4-live, frontend.py, config.json, buttons.json, live-settings.json
   (if present), and all logs.
   Do not copy anything into grainbrick-beta/ or delete any directory.
4. Refresh PORTS. Launch GrainBrick V4 Original UI (not Inspect).

FIRST TEST
The LIVE page should show six knobs, with the original GrainBrick pixel
font/tab bar and a selected orange control. No sample file is required.
A starts audio dry, with half output gain. Select Wet Mix and increase it.
D-pad UP/DOWN selects the next/previous control in reading order.
D-pad LEFT/RIGHT changes the selected control. B stops audio. START exits.
With no saved settings: Grain=20 ms, Delay=10 ms, Pitch=1, Scatter=0.
Saved settings replace those four defaults on later launches.
Keep the Tascam direct monitoring disabled, as for your working V4 test.

The footer shows engine status, device, last reported output peak, recovery
count and DSP time. Peak/DSP values update on the engine's two-second log
interval. They are not measured round-trip latency or an input meter.
Every audio start resets ONLY wet mix and output gain to dry/half gain.
Grain size, delay, pitch and scatter remain selected and are sent to the
engine on every audio start.
Existing V4 calibration is used, or V3 gb_buttons.json is read without edits.

REMEMBERED SETTINGS (NEW IN 0.2)
Grain size, delay, pitch and scatter are saved automatically when you press
B or exit with START, after the audio process has stopped. Preference writes do
not occur during live processing. Settings changed while stopped are also
saved on exit. Wet mix/output gain are never remembered and start at 0/0.5.

The file is grainbrick-v4-live/live-settings.json. It is generated locally
and is NOT part of this ZIP, so an update cannot replace it. config.json
still contains audio-device settings; buttons.json is calibration. Those
files are not changed by preference saving. Writes use a temporary file,
file flush/fsync and atomic replacement. Invalid saved values use defaults;
a malformed file is not overwritten merely by loading it. Save failures
appear in v4-native-ui.log and in the stopped-screen status.

QUICK SAVE/RESTORE TEST
1. Launch Original UI LIVE. Set grain, delay, pitch and scatter as desired.
2. Press A: the four values should remain selected; Wet=0 and Output=0.5.
3. Play, then B to stop. If tone controls changed, the status confirms settings were saved.
4. Exit with START and relaunch. The four knobs should show your values.
5. Press A again: those values apply, while Wet=0 / Output=0.5 stay safe.
The footer identifies LIVE UI 0.2; the unchanged engine still reports 0.1.1.
To reset remembered controls, close the app and rename live-settings.json.

REPORT
Please send a screenshot/photo plus:
  grainbrick-v4-live/v4-native-ui.log
  grainbrick-v4-live/v4-audio.log
Tell us whether A starts audio, the knobs adjust wet/pitch/scatter, and B /
START stop/exit normally. If the launcher returns to PORTS immediately,
v4-native-ui.log should contain the failure. The old standalone V4 launcher
continues to work as the fallback.

SCOPE
This release provides the LIVE page using the actual original renderer.
Use the unchanged V3 launcher for sample playback, projects, ORBIX and FX.
Those features are not routed through the independent live engine yet, and
this launcher never starts V3's main event loop or AudioWorker.
Only one application should own the Tascam at a time; close V3 before LIVE.
The same V4 .lock prevents simultaneous old/new V4 frontend instances.

IMPLEMENTATION / PROTECTION
The loader accepts only the exact beta main-module hash already inspected.
It imports until the observed early write/startup boundary and retains the
renderer/parameter classes. Original startup is never resumed. Python-level
guards block bootstrap writes, processes, and audio initialization. During
LIVE, V3 paths remain protected against Python writes and only the V4 engine
may be started as a subprocess. The renderer's original close/settings-save
method is not called. These guards are not a general OS sandbox for arbitrary
native code; this is for the pinned, inspected beta package only.
V3's known display adapter scales the original 1024x768 canvas to 640x480.
Mixer/global Pygame init stays disabled; display/joystick belong to the UI,
and USB capture/playback belongs to the existing V4 child process.

ROLLBACK
Exit, then use GrainBrick V4 Live or your V3 launcher as before. If desired,
remove ONLY GrainBrick V4 Original UI.sh, original_ui_entry.py, native_ui.py
and live_frontend.py. No changes to V3 or the old audio engine need undoing.
