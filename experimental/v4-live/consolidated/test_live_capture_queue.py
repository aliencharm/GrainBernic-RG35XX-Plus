import os
import threading
import types
import unittest
from unittest.mock import patch
import numpy as np
from live_source import ArecordCapture


class CaptureQueueTests(unittest.TestCase):
    def capture(self):
        read_fd,write_fd=os.pipe()
        process=types.SimpleNamespace(stdout=os.fdopen(read_fd,'rb',buffering=0),poll=lambda:None)
        with patch('live_source.subprocess.Popen',return_value=process):capture=ArecordCapture('test')
        self.addCleanup(process.stdout.close);self.addCleanup(os.close,write_fd)
        return capture,write_fd
    def block(self,value,frames=128):return np.full((frames,2),value,dtype='<i2').tobytes()

    def test_normal_queue_preserves_every_frame_in_order(self):
        capture,writer=self.capture()
        os.write(writer,self.block(100)+self.block(200))
        for value in (100,200):
            np.testing.assert_array_equal(capture.read(128),np.full((128,2),value/32768,np.float32))
        self.assertEqual(capture.skipped_frames,0);self.assertEqual(capture.resync_count,0)

    def test_backlog_returns_recent_input_instead_of_permanent_delay(self):
        capture,writer=self.capture()
        for value in (100,200,300,400):os.write(writer,self.block(value))
        np.testing.assert_array_equal(capture.read(128),np.full((128,2),400/32768,np.float32))
        self.assertEqual(capture.skipped_frames,384);self.assertEqual(capture.resync_count,1)
        for value in (500,600,700):
            os.write(writer,self.block(value))
            np.testing.assert_array_equal(capture.read(128),np.full((128,2),value/32768,np.float32))
        self.assertEqual(capture.resync_count,1)

    def test_resync_join_is_smoothed_then_reaches_latest_input(self):
        capture,writer=self.capture();os.write(writer,self.block(-1000));capture.read(128)
        for value in (1000,2000,3000,4000):os.write(writer,self.block(value))
        audio=capture.read(128)
        self.assertEqual(float(audio[0,0]),-1000/32768)
        self.assertAlmostEqual(float(audio[-1,0]),4000/32768,places=6)
        self.assertTrue(np.all(np.diff(audio[:,0])>=0))
        self.assertEqual(capture.skipped_frames,384)

    def test_odd_pipe_fragments_preserve_stereo_alignment_after_resync(self):
        capture,writer=self.capture()
        values=np.arange(2*(512+128),dtype='<i2').reshape(-1,2)
        raw=values.tobytes();os.write(writer,raw[:512*4+3])
        np.testing.assert_array_equal(capture.read(128),values[384:512].astype(np.float32)/32768)
        os.write(writer,raw[512*4+3:])
        np.testing.assert_array_equal(capture.read(128),values[512:].astype(np.float32)/32768)
        self.assertEqual(capture.skipped_frames,384)

    def test_normal_partial_reads_keep_attack_at_frame_zero(self):
        capture,writer=self.capture();values=np.zeros((128,2),dtype='<i2');values[0]=1234;values[-1]=-789
        raw=values.tobytes()
        def produce():
            for start in range(0,len(raw),7):os.write(writer,raw[start:start+7])
        thread=threading.Thread(target=produce);thread.start()
        try:np.testing.assert_array_equal(capture.read(128),values.astype(np.float32)/32768)
        finally:thread.join()
        self.assertEqual(capture.skipped_frames,0)

    def test_deadline_and_closed_stream_remain_errors(self):
        capture,writer=self.capture()
        with patch('live_source.time.monotonic',side_effect=[0.,3.]):
            with self.assertRaises(TimeoutError):capture.read(128)
        with patch('live_source.os.read',return_value=b''):
            with patch('live_source.select.select',return_value=([capture.process.stdout],[],[])):
                with self.assertRaisesRegex(OSError,'stream ended'):capture.read(128)
