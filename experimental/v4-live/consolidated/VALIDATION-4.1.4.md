# V4.1.4 validation

46 host tests pass in the development Python environment, including loaded/unloaded browser preview dispatch and missing-input recording guards.

The original ARM native application is exercised in isolation with the original native DSP. The SAMPLE mixer regression covers native blend math, Internal output selection with USB input, blocked recording without input, SELECT/X transitions, recording/preview delegation, and A toggling Freeze on and off. The project regression retains paused project loading, moving playhead, native audio and browser preview dispatch.

The no-input regression boots the original app with no USB routes and Internal output. It checks that only NO USB INPUT is offered, attempts to record and start LIVE do not activate capture, messages identify the missing input, and X returns to SAMPLE. It also captures the browser and LIVE no-input screens.

Original-renderer screenshots are inspected for coherent SAMPLE/LIVE layout, input labels, smaller Freeze switch, shortened separator and footer hints. The full target archive is verified and the update overlay checked against V4.1.3. Personal media/configuration/state are excluded.

OS audio/process boundaries are mocked for UI checks. Device confirmation is needed for hardware sound and interaction. No buffer timing, native DSP or saved recording audio changes are included.
