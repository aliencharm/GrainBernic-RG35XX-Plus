# Experimental 0.1.0 validation

Built on x86_64 Linux using GCC for host checks and Debian Bookworm GCC
12.2.0 AArch64 cross compiler (glibc 2.36 sysroot). Build dependencies were
downloaded using signed Debian package metadata and normal package checksum
verification. No TLS or package verification was disabled.

Passed:

- C compilation with `-std=c11 -Wall -Wextra -Werror`, host and ARM64.
- Deterministic DSP assertions: dry identity at unity gain, wet response to
  changed input, old history overwritten, zero input eventually silent,
  uninitialized history not read at startup, finite bounded stereo output,
  multiple ring wraps and grain/delay/pitch/mix extremes.
- Same DSP suite with AddressSanitizer and UndefinedBehaviorSanitizer.
  LeakSanitizer could not execute under the environment's ptrace management;
  leak detection was disabled for the successful sanitizer run. No claim
  of leak-sanitizer coverage is made.
- Same DSP suite executed as ARM64 under QEMU user emulation.
- Packaged ARM64 executable's version command under QEMU. ELF requires
  GLIBC_2.34 at most, below the supplied V3 module's GLIBC_2.38 requirement.
- Real host ALSA null capture/playback opens and streams; live parameter
  changes, periodic statistics and clean exit. The null plugin is unclocked
  and does not validate audio content, physical duplex timing or latency.
- ALSA fault-injection tests: partial reads/writes, one capture XRUN,
  one playback XRUN, disconnect, negotiated-rate rejection, capture timeout.
  The mock ALSA library is test source only and is NOT shipped as a library.
- Three frontend tests for Tascam USB/duplex detection, explicit PCM config
  validation and V3 button/keyboard translation.
- Full headless Pygame screen -> native ALSA-null child -> wet-mix change ->
  periodic statistics -> stop -> exit. Diagnostics generation exercised.
- Launcher shell syntax; archive checksums and ARM64 binary identity.

Not tested / still required:

- Execution on RG35XX Plus, KNULLI Pygame 2.5.2 display/controller behavior.
- Tascam hardware capture/playback, format support, direct-monitor setting.
- Measured round-trip latency, actual audio quality, crackling, CPU load and
  sustained real-time stability on the handheld.
- Physical unplug/replug and V3 regression checks on that hardware.

This package is a testable experimental prototype, not a hardware-validated
GrainBrick release. It does not expose or modify the proprietary beta DSP.
