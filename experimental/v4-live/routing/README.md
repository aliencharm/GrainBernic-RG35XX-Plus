# Multichannel routing investigation

Stable baseline: standalone V4 1.2. User confirmed iConnectivity audio4c works with analog inputs 1/2, and requests interface-name display plus input and output channel selection in the original UI.

The engine remains stereo. First implementation: stereo pairs 1/2, 3/4, 5/6 and onward across every ALSA-exposed USB channel pair, with separate capture and playback lists. Mono selection is deferred at the user's request. ALSA-visible USB channels may also carry routed DAW/USB signals; physical-jack labels must not be inferred solely from channel numbers. Actual capture/playback PCM devices, formats, counts and rates must be read from the user's hardware before implementing channel routes. Input/output choices must be separate, and REC/LIVE must share the selected input path.

The discovery ZIP adds only a temporary report launcher and Python script. It reads /proc/asound descriptors, ALSA device lists and app version/config. It never starts capture/playback, edits the audio configuration or changes the stable app. Run it with audio4c connected; return grainbrick-v4/audio-routing-report.txt. The launcher and diagnostic script can be removed afterward.

The source inventory parser and channel-choice model are initial development work, not integrated channel routing. Four parser/model tests pass. No new multichannel support is claimed until implemented and tested on hardware.
