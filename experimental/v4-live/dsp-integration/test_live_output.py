import types
import unittest
from original_adapter import LiveController

class LiveOutputTests(unittest.TestCase):
    def test_live_profile_restores_original_output_on_stop(self):
        audio=types.SimpleNamespace(low_latency_buffer_frames=7168,low_latency_period_frames=512,low_latency_pipe_bytes=8192)
        controller=LiveController(types.SimpleNamespace(),{})
        controller.configure_live_output(audio)
        self.assertEqual((audio.low_latency_buffer_frames,audio.low_latency_period_frames,audio.low_latency_pipe_bytes),(2048,512,4096))
        controller.restore_live_output()
        self.assertEqual((audio.low_latency_buffer_frames,audio.low_latency_period_frames,audio.low_latency_pipe_bytes),(7168,512,8192))
        self.assertFalse(audio._v4_live_output)
    def test_restart_retains_original_baseline(self):
        audio=types.SimpleNamespace(low_latency_buffer_frames=7168,low_latency_period_frames=512,low_latency_pipe_bytes=8192)
        controller=LiveController(types.SimpleNamespace(),{})
        controller.configure_live_output(audio);controller.configure_live_output(audio)
        controller.restore_live_output();controller.restore_live_output()
        self.assertEqual(audio.low_latency_buffer_frames,7168)
        self.assertEqual(audio.low_latency_pipe_bytes,8192)

if __name__=='__main__':unittest.main()
