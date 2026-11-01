"""Verify isolation controls cannot replace or modify the original WAV capture."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from record_monitor import RecordingMonitor,recording_command

class RecordingDiagnosticsTests(unittest.TestCase):
    def test_original_timing_passes_exact_capture_command_through(self):
        command=['arecord','-D','v4_capture_USB_0_3_4','-f','S16_LE','-r','48000','-c','2','-t','wav','capture.wav']
        with patch.dict(os.environ,{'GRAINBRICK_REC_CAPTURE_TIMING':'original'}):
            self.assertIs(recording_command(command),command)
        with patch.dict(os.environ,{'GRAINBRICK_REC_CAPTURE_TIMING':''}):
            self.assertEqual(recording_command(command),[command[0],'--buffer-time=24000','--period-time=6000',*command[1:]])

    def test_disabled_monitor_never_opens_capture_file_or_playback(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'capture.wav';raw=b'original capture bytes';path.write_bytes(raw)
            with patch.dict(os.environ,{'GRAINBRICK_REC_MONITOR':'0'}),patch('record_monitor.subprocess.Popen') as spawn,patch.object(Path,'open',side_effect=AssertionError('monitor must not open WAV')):
                monitor=RecordingMonitor(path,'USB');monitor.start();monitor.stop()
                spawn.assert_not_called()
                self.assertIsNone(monitor.thread)
                self.assertEqual(monitor.status,'OFF')
            self.assertEqual(path.read_bytes(),raw)

if __name__=='__main__':unittest.main()
