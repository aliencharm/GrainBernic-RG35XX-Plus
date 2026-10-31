# Experimental V4 Live

Independent C ALSA duplex engine and Pygame control screen for RG35XX Plus.
Existing V3 files are untouched. See [installation and hardware test guide](package/INSTALL-V4.txt).

`src/dsp.c` implements a four-second stereo ring, bounded overlapping grains,
linear interpolated reads, Hann windows, scattered lookback and pitch ratios.
Scatter is adjustable from 0 to 100 ms and defaults to zero. At unity pitch
and fixed grain/delay, zero scatter preserves a delayed waveform without
random phase offsets. Startup defaults are 20 ms grains and 10 ms delay.
The capture writer and grain readers run in the same thread, so no ring locks
or concurrent engine-buffer mutation are needed. Each grain reads initialized,
non-overwritten history behind the writer. Memory is allocated before streaming.

`src/audio.c` uses system `libasound.so.2` via runtime symbol resolution,
nonblocking capture/playback with partial-transfer handling and two-second
stall limits. Both streams are reset together after XRUN; disconnects fail
rather than silently selecting another output. Commands arrive over stdin;
logs contain aggregate statistics, never captured audio.

`package/grainbrick-v4-live/frontend.py` selects a Tascam or explicit configured
PCM pair, reads V3 calibration without writing it, and starts/stops only its own
child. Wet mix starts at zero each time. No integration with the proprietary
application UI or effects is attempted in this prototype.

## Build

Requires a C11 compiler, libc development files and ALSA development headers.
On Debian: `gcc make libasound2-dev`; cross build also requires
`gcc-aarch64-linux-gnu libc6-dev-arm64-cross`. ALSA headers are architecture
neutral for this source; only libc/libm/libdl are linked. The target uses its
own system ALSA at runtime. Do not ship a test shim or replace system ALSA.

```sh
make
make test
make CC=aarch64-linux-gnu-gcc BUILD=build/arm64
```

Use `CPPFLAGS=-I/path/to/alsa-header-parent` and compiler `--sysroot` when
using an extracted toolchain. Do not use the native x86 build on the handheld.
Copy the ARM64 `build/arm64/v4-live` to `package/grainbrick-v4-live/v4-live`,
then package the `package/` contents. Make the launcher and binary executable.

## Validation

```sh
make test BUILD=build/sanitized CFLAGS='-O1 -g -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer'
python3 -B tests/test_frontend.py
python3 -B tests/test_ui_smoke.py build/v4-live
mkdir -p build/fake
cc -shared -fPIC -Wall -Wextra -Werror tests/fake_alsa.c -o build/fake/libasound.so.2
python3 -B tests/test_audio.py build/v4-live build/fake
```

UI tests need Pygame; ALSA-null tests need the host ALSA library and its null
plugin. The fault shim exists only for tests. LeakSanitizer cannot run in some
ptrace-managed environments; there use `ASAN_OPTIONS=detect_leaks=0` while
retaining address/undefined-behavior checks, and record that limitation.

Offline and emulated checks do not establish real-time hardware readiness.
Consult VALIDATION.md for the exact checks executed for this package.

## Package 0.1.1

From this directory, after cross compiling:

```sh
python3 tools/package.py --binary build/arm64/v4-live --output GrainBrick_V4_0.1.1.zip
```

Overlay the installed V4 files after exiting the app. Preserve config.json,
buttons.json and logs. See INSTALL-V4.txt in the archive for the listening test.
