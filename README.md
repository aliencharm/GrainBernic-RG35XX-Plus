# GrainBernic — RG35XX Plus

An unofficial compatibility port of [GrainBrick](https://github.com/ETRNLIAM/GrainBrick) for the **Anbernic RG35XX Plus**, running **KNULLI Scarab 20260511**.

Based on the [GrainBernik RG40XX H compatibility patch](https://github.com/AlekseyMalykh/GrainBernik) by AlekseyMalykh.

## Stable V3

The RG35XX Plus V3 compatibility port has been tested with a **Tascam DR-40X USB audio interface**.

Confirmed working:

- GrainBrick beta 1.0 launches and exits cleanly
- Display scaling from 1024×768 to 640×480
- RG35XX Plus controller mapping
- USB audio playback
- USB audio recording from microphones and external synthesizers
- Sample saving, loading and granular processing
- ORBIX generative synthesizer
- Sound parameter persistence

The port uses the original application's bundled NumPy and preloads `pygame.surfarray` to resolve startup compatibility issues.

## Experimental V4

Development branch: `v4-live-granular-dev`

**Goal:** Continuous live granular processing of incoming audio using a circular ring buffer, with adjustable software dry/wet monitoring through the USB audio interface.

V4 is experimental. Live processing is not yet implemented or verified on the RG35XX Plus.

## Installation

This repository contains compatibility patches and launch scripts. It does not include the original GrainBrick application.

1. Obtain the official GrainBrick beta 1.0 release from the original developer.
2. Install it in `/userdata/roms/ports/grainbrick-beta/`.
3. Copy the four `gb_*.py` compatibility modules into that directory.
4. Copy the launcher `.sh` scripts into `/userdata/roms/ports/`.
5. Launch GrainBrick from KNULLI's Ports menu.

Tested environment: RG35XX Plus, KNULLI Scarab 20260511, Python 3.12.8, Pygame 2.5.2, Tascam DR-40X.

## Credits

- **ETRNLIAM** — Original GrainBrick application and synthesis engine.
- **AlekseyMalykh** — GrainBernik RG40XX H compatibility patch.
- **aliencharm** — RG35XX Plus adaptation and testing.

## Disclaimer

Unofficial community port. Not affiliated with or endorsed by the original GrainBrick developer or Anbernic.

The original GrainBrick application and its closed-source native libraries are not redistributed here.
