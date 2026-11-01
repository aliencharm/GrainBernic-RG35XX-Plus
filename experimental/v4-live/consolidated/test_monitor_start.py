import unittest
import numpy as np
from record_monitor import monitor_start_fade,RecordingMonitor
class MonitorStartTests(unittest.TestCase):
    def test_fade_then_unity_without_mutating_capture(self):
        raw=np.full((512,2),12000,dtype='<i2').tobytes();before=bytes(raw)
        result=np.frombuffer(monitor_start_fade(raw,2,48000,0),dtype='<i2').reshape(-1,2)
        self.assertEqual(result[0,0],0);self.assertEqual(result[479,0],12000)
        np.testing.assert_array_equal(result[480:],12000)
        self.assertEqual(raw,before)
        self.assertIs(monitor_start_fade(raw,2,48000,512),raw)
    def test_partial_first_block_continues_fade(self):
        raw=np.full((240,2),12000,dtype='<i2').tobytes()
        first=np.frombuffer(monitor_start_fade(raw,2,48000,0),dtype='<i2')
        second=np.frombuffer(monitor_start_fade(raw,2,48000,240),dtype='<i2')
        self.assertLess(first[-1],second[0]);self.assertEqual(second[-1],12000)
    def test_monitor_pipeline_leaves_recorded_file_unchanged(self):
        import os,struct,tempfile,threading
        from pathlib import Path
        from unittest.mock import patch
        raw=np.full((8192,2),12000,dtype='<i2').tobytes()
        header=b'RIFF'+struct.pack('<I',len(raw)+36)+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,2,48000,192000,4,16)+b'data'+struct.pack('<I',len(raw))
        class Output:
            def __init__(self):
                read,write=os.pipe();self.stdin=os.fdopen(write,'wb',buffering=0)
                self.returncode=None;self.audio=bytearray();self.ready=threading.Event()
                def drain():
                    with os.fdopen(read,'rb',buffering=0) as source:
                        while data:=source.read(4096):
                            self.audio.extend(data)
                            if len(self.audio)>=len(raw):self.ready.set()
                self.reader=threading.Thread(target=drain);self.reader.start()
            def poll(self):return self.returncode
            def terminate(self):self.returncode=0
            def wait(self,timeout):return self.returncode
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'capture.wav';path.write_bytes(header+raw)
            output=Output()
            with patch('record_monitor.subprocess.Popen',return_value=output):
                monitor=RecordingMonitor(path,'test');monitor.start()
                try:self.assertTrue(output.ready.wait(3))
                finally:monitor.stop();output.reader.join(1)
            self.assertIsNone(monitor.error)
            self.assertEqual(path.read_bytes(),header+raw)
            result=np.frombuffer(output.audio,dtype='<i2').reshape(-1,2)
            self.assertEqual(result[0,0],0)
            np.testing.assert_array_equal(result[480:],12000)
if __name__=='__main__':unittest.main()
