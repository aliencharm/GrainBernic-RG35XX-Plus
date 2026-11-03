# V4.2.1 SAMPLE dry playback

The previous dry branch instantiated another native granular engine with grain disabled. Native reproduction with all SAMPLE mixes zero, grain disabled and ROAM off returned zero from both the source and dry engine. The source was being called and preview ownership had returned correctly; the dry signal itself was silent.

The dry branch now reads the loaded file directly, loops at its original sample rate with linear rate conversion when required, and follows transport pause/resume. GRANULAR disabled uses dry playback irrespective of its mix knob. Enabled native granular output remains the wet path, including exact full-wet passthrough. FX/Tape retain the native processing and stage mixes. Grain/ROAM switches are not changed. LIVE capture/rendering, its controls and frozen export are unchanged.

63 host tests pass, adding known-signal dry looping, pause continuity, sample-rate conversion and disabled-granular passthrough checks to the existing runtime/import suite. Existing dry/half/full tests now compare against actual sample data rather than a fake granular-off output.

The original ARM app --preview-mixer regression uses the original SamplePreview class and only mocks external player processes. It exercises repeated browser preview → SELECT mixer → START playback with all mixes zero and ROAM off, disabled granular at full mixes, and granular enabled at zero mix. Each produces positive native DSP output with the correct loaded sample and worker ownership. The same scenario failed with peak 0.0 before the fix.

The original ARM --sample-mixer regression passes native wet/straight-file dry/half/full blend math, exact wet passthrough, original FX/Tape mixes, SAMPLE/LIVE transitions, recording/preview delegation and Freeze actions. Hardware audio processes are mocked, so final output/timing needs device confirmation.

The update is checked by virtually overlaying it on the V4.2 standalone and validating all target manifest hashes. Personal files, settings, control maps and the GrainBrick V4.2 launcher are excluded from the small update.

## Extended mixer verification

65 host tests pass after adding full GRANULAR MIX sweeps and both-direction ramp checks. The original native source is checked at 0%, 1%, 25%, 50%, 75%, 99% and 100%, ascending/descending, with grain ON/OFF and all ROAM/MOTION toggle combinations. Every settled output matches dry + mix × (native wet − dry), and each transition matches the block ramp. With grain OFF the effective mix is dry throughout.

The --tape-mix regression uses the actual native DSP chain and Tape processor with a known sine file, grain ON and OFF, and controlled non-neutral saturation. At 0/25/50/75/100% it compares the rendered chain output with the observed dry/native-wet blend; positive mixes change the audio. Tape OFF is also exercised through the original native processor; Tape ON with strong saturation differs from that output. This verifies signal routing and mixing, not the current settings on the user's handheld. No additional runtime change is made for these checks.
