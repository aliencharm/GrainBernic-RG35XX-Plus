# V4.2.2 SAMPLE mixer UX

START is the only play/pause action on the SAMPLE mixer. A is consumed without an action so it cannot fall through to the original input-recording handler. Footer state is START PLAY / START PAUSE. A in the browser and LIVE retain their load and Freeze actions. Audio/DSP code is unchanged from V4.2.1.

65 host tests pass. The original ARM preview-mixer regression uses the real SamplePreview with only external players mocked. Across repeated preview-to-mixer cycles, A does not change transport or enter recording while either paused or playing; START does toggle transport and native output remains audible. Footer screenshots cover both states. This builds on the V4.2.1 zero/intermediate/full granular and Tape mix verification.

The cumulative update is virtually checked on both V4.2 and V4.2.1 against every target manifest hash. It preserves media, settings, controls and the V4.2 launcher. Full-package integrity/layout/license checks pass; only the small update is published. Device UX confirmation remains necessary.
