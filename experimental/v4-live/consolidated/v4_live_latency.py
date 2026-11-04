"""LIVE output-buffer profile; processing blocks and capture remain unchanged."""
from types import MethodType


def configure_live_output(controller,audio):
    controller.restore_live_output()
    names=('low_latency_buffer_frames','low_latency_period_frames','low_latency_pipe_bytes')
    controller.live_output_restore=(audio,{name:getattr(audio,name) for name in names})
    audio.low_latency_buffer_frames=1024
    audio.low_latency_period_frames=512
    audio.low_latency_pipe_bytes=4096
    audio._v4_live_output=True
    print('V4 LIVE OUTPUT REQUEST: buffer_frames=1024 period_frames=512 pipe_bytes=4096',flush=True)


def install(controller):
    controller.configure_live_output=MethodType(configure_live_output,controller)
