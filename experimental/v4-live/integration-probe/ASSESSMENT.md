# V3 interface integration: investigation 1

V3's compiled `main` module is a Nuitka package containing `engine.*`, `ui.*`
and visualizer modules. Static evidence comes from its ELF symbols and
embedded strings; it does not establish a supported or stable extension API.
The supplied V3 main/native libraries match the official beta byte for byte.

| Candidate | Static evidence | Runtime evidence still needed |
| --- | --- | --- |
| Original renderer | `ui.renderer.UIEngine`, grain/sample/settings drawing methods | Constructor arguments, mutable class methods, call dispatch |
| UI navigation | `engine.control.ControlManager`, `change_tab`, `params_for_page`, `change_param`, `handle` | Parameter layouts, actions, route to add a separate live page |
| Parameters | `engine.parameters.ParameterBus`, `add`, `get`, `set` | Parameter schema, units/ranges, per-process synchronization |
| Audio lifecycle | `engine.audio_worker.AudioWorker`, `start`, `stop`, `running`, `request_audio_device` | Constructor, ownership, stop/join guarantees, output release |
| Shared DSP process | Embedded `_audio_process_main` and shared-value parameter reader | Whether a replacement worker is actually invoked by compiled main |

Existing grain controls include `grain.enabled`, `grain.position`,
`grain.size`, `grain.density`, `grain.spray`, and `grain.pitch`. Their
similarity to live controls is not a verified mapping: units and behavior
must be established before assigning them to V4 commands.

## Preferred path if runtime inspection supports it

Use a NEW experimental launcher, with no edits to V3, to install in-memory
adapters before original UI construction. Add an explicitly separate live
mode/page and map its controls to the known working V4 engine. Switching
must stop and join the original worker and close recording/preview streams
before V4 opens the same Tascam. Leaving live mode must stop V4 before
restoring original playback. Original effects/ORBIX are not automatically
available to independent V4 audio just because their controls are visible.

The first functional integration test should prove worker stop/restart and
exclusive PCM ownership before connecting live audio to the original UI.
Never run both playback processes at once. Do not call guessed native ABIs
or mutate internal audio buffers to make a GUI integration appear to work.

## Next concrete step

The separate guarded inspection package collects runtime class and callable
metadata without deliberately starting the original UI/audio. Five fixture
tests passed. It needs one run on the installed ARM64 Python 3.12 handheld.
Its report may be partial; that must be assessed before any runtime adapter
is designed. No original-UI live integration has been implemented or verified.
The working standalone V4 0.1.1 remains the fallback.
