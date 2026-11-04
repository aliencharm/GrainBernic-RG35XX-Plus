import sys,types,unittest
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'dsp-integration'))
from original_adapter import LiveController
from v4_live_latency import install

class LiveLatencyTests(unittest.TestCase):
    def test_restarts_and_stop_restore_original_output_profile(self):
        controller=LiveController(types.SimpleNamespace(),{})
        install(controller)
        audio=types.SimpleNamespace(low_latency_buffer_frames=7168,low_latency_period_frames=512,low_latency_pipe_bytes=8192)
        for _ in range(2):
            controller.configure_live_output(audio)
            self.assertEqual((audio.low_latency_buffer_frames,audio.low_latency_period_frames,audio.low_latency_pipe_bytes),(1024,512,4096))
            self.assertTrue(audio._v4_live_output)
        controller.restore_live_output();controller.restore_live_output()
        self.assertEqual((audio.low_latency_buffer_frames,audio.low_latency_period_frames,audio.low_latency_pipe_bytes),(7168,512,8192))
        self.assertFalse(audio._v4_live_output)

    def test_device_switch_restores_previous_device_before_applying_profile(self):
        controller=LiveController(types.SimpleNamespace(),{});install(controller)
        first=types.SimpleNamespace(low_latency_buffer_frames=7168,low_latency_period_frames=512,low_latency_pipe_bytes=8192)
        second=types.SimpleNamespace(low_latency_buffer_frames=4096,low_latency_period_frames=1024,low_latency_pipe_bytes=16384)
        controller.configure_live_output(first);controller.configure_live_output(second)
        self.assertEqual(first.low_latency_buffer_frames,7168)
        self.assertFalse(first._v4_live_output)
        controller.restore_live_output()
        self.assertEqual((second.low_latency_buffer_frames,second.low_latency_period_frames,second.low_latency_pipe_bytes),(4096,1024,16384))
