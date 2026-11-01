# USB stereo-pair routing test 1.3

Stable fallback: standalone 1.2. The 1.3 test ZIP is complete and requires no older installation.

The supplied audio4c report exposes one capture and one playback PCM, each with 8 channels at 48000 Hz, S32_LE. The new selector lists four stereo pairs per direction: 1-2, 3-4, 5-6, 7-8. These are Linux USB channel numbers in the device's current configuration. The app does not infer analog/DAW routing labels or change interface firmware/matrix settings. Pair 9-10 is not exposed in the supplied Linux report. Mono choices are deferred.

On SAMPLE/LIVE -> RECORD INPUT, the current interface/pair is displayed. L2/R2 selects inputs in REC and LIVE; changing an active LIVE input stops it, then A restarts on the new pair. The original REC source controls also use the new pair list. SETTINGS' existing output control lists output pairs alongside the original internal/HDMI choices. Select routes while stopped. One input pair and one output pair are used at a time. Input/output choices persist in config.json.

Routes are defined in a per-app alsa-routing.conf and inherited by its audio processes. ALSA performs channel mapping and native-format conversion around the original stereo engine. No global ALSA config is edited. Original recording, LIVE DSP, mix knobs, freeze and the low-latency profile remain unchanged. Saved media/preferences are not deleted by this update.

Tests: descriptor/parser choices, actual ALSA route/file/null plugins (8-channel S32 capture 3-4 to stereo S16; stereo to output 5-6 with other channels silent), and ARM-emulated original app input selection/stop/restart/REC delegation, four output pairs, output 7-8 selection and saved choices. Audio4c hardware operation of the new pair routes remains unverified until the user test. Keep 1.2 backed up as the known working baseline.

After testing, send grainbrick-v4/v4.log, audio_process.log and config.json. Confirm a non-default input pair in LIVE and REC, plus a non-default output pair, against the interface's existing configured patchbay.

The read-only discovery ZIP remains available; it reads /proc/asound and ALSA lists without starting streams or changing audio config.
