import shutil,subprocess,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
from v4_shimmer import StardustDSP,SHIMMER_DEFAULTS,STARDUST_PARAMS,ParameterView,ShimmerChoice

class Params:
    def __init__(self,**values):self.values={k:v[0] for k,v in SHIMMER_DEFAULTS.items()};self.values.update(values)
    def get(self,k):return self.values[k]

class StardustTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('cc') is None:raise unittest.SkipTest('Native C compiler required')
        cls.folder=tempfile.TemporaryDirectory();cls.library=Path(cls.folder.name)/'stardust.so'
        source=Path(__file__).resolve().parents[1]/'stardust/stardust.c'
        subprocess.run(['cc','-std=c99','-O3','-shared','-fPIC',str(source),'-o',str(cls.library),'-lm'],check=True)
    @classmethod
    def tearDownClass(cls):cls.folder.cleanup()
    def render(self,seconds=3,rate=48000,**values):
        p=Params(**values);engine=StardustDSP(rate,self.library);self.addCleanup(engine.close)
        signal=np.zeros((int(seconds*rate),2),np.float32);signal[0]=.8
        output=np.empty_like(signal)
        for start in range(0,len(signal),512):
            feed=signal[start:start+512];audio=feed.copy()
            output[start:start+512]=engine.process(feed,audio,p)
        return output
    def test_silence_and_dry_passthrough(self):
        e=StardustDSP(48000,self.library);self.addCleanup(e.close)
        p=Params(**{'stardust.input':1,'stardust.send':0,'stardust.return':0})
        audio=np.random.default_rng(10).uniform(-.8,.8,(512,2)).astype(np.float32)
        np.testing.assert_array_equal(e.process(audio.copy(),audio.copy(),p),audio)
        e.clear();zeros=np.zeros((512,2),np.float32)
        np.testing.assert_array_equal(e.process(zeros,zeros.copy(),Params()),zeros)
    def test_predelay_and_wet_tail(self):
        out=self.render(**{'stardust.input':0,'stardust.predelay':100,'stardust.send':1,'stardust.return':1})
        self.assertEqual(float(np.max(np.abs(out[:4800]))),0)
        self.assertGreater(float(np.max(np.abs(out[4800:]))),.001)
        self.assertGreater(float(np.sum(out[24000:]**2)),1e-7)
        self.assertTrue(np.isfinite(out).all())
    def test_negative_predelay_delays_dry_signal(self):
        out=self.render(seconds=.5,**{'stardust.predelay':-100,'stardust.input':1,'stardust.send':0,'stardust.return':0})
        self.assertEqual(float(np.max(np.abs(out[:4800]))),0)
        self.assertAlmostEqual(float(out[4800,0]),.8,places=6)
    def test_send_return_and_input_are_independent(self):
        out=self.render(**{'stardust.input':0,'stardust.send':0,'stardust.return':1})
        np.testing.assert_array_equal(out,np.zeros_like(out))
        out=self.render(seconds=.2,**{'stardust.input':.5,'stardust.send':1,'stardust.return':0})
        self.assertAlmostEqual(float(out[0,0]),.4,places=6)
        self.assertEqual(float(np.max(np.abs(out[1:]))),0)
    def test_decay_control_changes_late_energy(self):
        short=self.render(**{'stardust.input':0,'stardust.decay':0,'stardust.return':1,'stardust.pitch':0})
        long=self.render(**{'stardust.input':0,'stardust.decay':1,'stardust.return':1,'stardust.pitch':0})
        self.assertGreater(float(np.sum(long[48000:]**2)),float(np.sum(short[48000:]**2))*3)
    def test_parameter_extremes_and_long_tail_remain_finite(self):
        for shift in (-24,24):
            out=self.render(seconds=12,**{'stardust.input':0,'stardust.size':1,'stardust.decay':1,'stardust.depth':1,'stardust.frequency':5,'stardust.pitch':shift,'stardust.return':1})
            self.assertTrue(np.isfinite(out).all());self.assertLess(float(np.max(np.abs(out))),4)
    def test_expansive_pitch_tail_and_size_response(self):
        # Broadband burst: late pitched tail must persist, then decay without self-oscillation.
        for pitch in (-12,12):
            e=StardustDSP(48000,self.library);self.addCleanup(e.close)
            p=Params(**{'stardust.input':0,'stardust.predelay':0,'stardust.size':1,'stardust.decay':1,'stardust.pitch':pitch,'stardust.return':1,'stardust.depth':0})
            feed=np.zeros((48000*24,2),np.float32)
            feed[:24000]=np.random.default_rng(3).normal(0,.12,(24000,2))
            out=np.empty_like(feed)
            for start in range(0,len(feed),512):
                block=feed[start:start+512];out[start:start+len(block)]=e.process(block,block.copy(),p)
            early=float(np.mean(out[24000:48000]**2))
            late=float(np.mean(out[48000*8:48000*9]**2))
            end=float(np.mean(out[-48000:]**2))
            self.assertTrue(np.isfinite(out).all())
            self.assertGreater(late,early*1e-5)
            self.assertLess(end,late*.01)
            self.assertLess(float(np.max(np.abs(out))),.5)
        small=self.render(seconds=.5,**{'stardust.input':0,'stardust.predelay':0,'stardust.size':0,'stardust.depth':0})
        large=self.render(seconds=.5,**{'stardust.input':0,'stardust.predelay':0,'stardust.size':1,'stardust.depth':0})
        onset=lambda x:int(np.flatnonzero(np.max(np.abs(x),axis=1)>1e-7)[0])
        self.assertGreater(onset(large),onset(small)*8)

    def test_clear_and_frame_sizes(self):
        e=StardustDSP(48000,self.library);self.addCleanup(e.close)
        for n in (1,7,17,127,512,1024):
            feed=np.ones((n,2),np.float32)*.1
            self.assertEqual(e.process(feed,feed.copy(),Params()).shape,(n,2))
        e.clear()
        p=Params(**{'stardust.input':0,'stardust.send':0,'stardust.return':1})
        for _ in range(100):
            z=np.zeros((512,2),np.float32)
            np.testing.assert_array_equal(e.process(z,z.copy(),p),z)
    def test_pitch_feedback_creates_upward_and_downward_bands(self):
        energies={}
        for shift in (-12,0,12):
            e=StardustDSP(48000,self.library);self.addCleanup(e.close)
            p=Params(**{'stardust.input':0,'stardust.predelay':0,'stardust.return':1,'stardust.pitch':shift,'stardust.depth':0,'stardust.decay':.9,'stardust.brightness':1})
            feed=np.zeros((48000*4,2),np.float32)
            feed[:48000]=(.4*np.sin(np.arange(48000)*2*np.pi*220/48000))[:,None]
            out=np.empty_like(feed)
            for start in range(0,len(feed),512):
                block=feed[start:start+512];out[start:start+len(block)]=e.process(block,block.copy(),p)
            signal=out[48000:144000,0]
            spectrum=np.abs(np.fft.rfft(signal*np.hanning(len(signal))))**2
            frequencies=np.fft.rfftfreq(len(signal),1/48000)
            energies[shift]={hz:float(np.sum(spectrum[(frequencies>hz-8)&(frequencies<hz+8)])) for hz in (110,440)}
        self.assertGreater(energies[12][440],energies[0][440]*10)
        self.assertGreater(energies[-12][110],energies[0][110]*10)
    def test_choice_keeps_original_path_and_only_processes_selected_engine(self):
        class FX:sample_rate=48000
        fx=FX();choice=ShimmerChoice(fx);p=Params(**{'shimmer.mix':.8,'reverb.mix':.7})
        calls=[]
        def original(engine,audio,parameters):
            calls.append((parameters.get('shimmer.mix'),parameters.get('reverb.mix')))
            audio*=.5;return audio
        block=np.ones((512,2),np.float32)*.2
        out=choice.process(block.copy(),p,original)
        np.testing.assert_array_equal(out,block*.5);self.assertIsNone(choice.star)
        self.assertEqual(calls[-1],(.8,.7))
        p.values.update({'shimmer.type':1,'stardust.input':1,'stardust.send':0,'stardust.return':0,'stardust.predelay':0})
        factory=lambda rate:StardustDSP(rate,self.library)
        with patch('v4_shimmer.StardustDSP',side_effect=factory):
            for _ in range(3):out=choice.process(block.copy(),p,original)
        self.addCleanup(choice.star.close)
        np.testing.assert_allclose(out,block*.5)
        self.assertEqual(calls[-1],(0.,.7));self.assertEqual(p.get('shimmer.mix'),.8)
        p.values['shimmer.type']=0
        for _ in range(3):out=choice.process(block.copy(),p,original)
        np.testing.assert_array_equal(out,block*.5);self.assertEqual(calls[-1],(.8,.7))
    def test_original_parameters_are_not_modified_by_view(self):
        p=Params(**{'shimmer.mix':.7,'reverb.mix':.6,'reverb.decay':9})
        view=ParameterView(p)
        self.assertEqual(view.get('shimmer.mix'),0)
        self.assertEqual(view.get('reverb.mix'),.6)
        self.assertEqual(p.get('shimmer.mix'),.7)
