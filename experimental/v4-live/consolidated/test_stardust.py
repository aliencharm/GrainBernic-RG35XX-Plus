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
            energies[shift]={hz:float(np.sum(spectrum[(frequencies>hz-8)&(frequencies<hz+8)])) for hz in (110,220,440,880)}
        self.assertGreater(energies[12][440],energies[0][440]*10)
        self.assertGreater(energies[-12][110],energies[0][110]*10)
        self.assertGreater(energies[12][440],energies[12][220]*2)
        self.assertGreater(energies[-12][110],energies[-12][220]*2)
        self.assertGreater(energies[12][880],energies[12][220]*.02)
    def test_stereo_cloud_remains_audible_in_mono_and_modulation_is_present(self):
        spectra={}
        for depth,frequency in ((0,.5),(1,.05),(1,5)):
            e=StardustDSP(48000,self.library);self.addCleanup(e.close)
            p=Params(**{'stardust.input':0,'stardust.predelay':0,'stardust.return':1,'stardust.pitch':12,'stardust.depth':depth,'stardust.frequency':frequency,'stardust.size':1,'stardust.decay':1})
            signal=np.zeros((48000*8,2),np.float32)
            signal[:48000*3]=(.2*np.sin(np.arange(48000*3)*2*np.pi*220/48000))[:,None]
            out=np.empty_like(signal)
            for start in range(0,len(signal),512):
                block=signal[start:start+512];out[start:start+len(block)]=e.process(block,block.copy(),p)
            tail=out[48000*3:48000*7]
            if depth==0:
                self.assertLess(abs(float(np.corrcoef(tail.T)[0,1])),.6)
                stereo=float(np.mean(tail*tail));mono=float(np.mean(np.mean(tail,axis=1)**2))
                self.assertGreater(mono,stereo*.2)
                channel_energy=np.mean(tail*tail,axis=0)
                self.assertGreater(float(min(channel_energy)/max(channel_energy)),.25)
            spec=np.sum(np.abs(np.fft.rfft(out[48000:144000]*np.hanning(96000)[:,None],axis=0))**2,axis=1)
            frequencies=np.fft.rfftfreq(96000,1/48000)
            region=(frequencies>420)&(frequencies<460)
            sides=region&(abs(frequencies-440)>3)
            spectra[depth,frequency]=float(np.sum(spec[sides])/np.sum(spec[region]))
        self.assertGreater(spectra[1,5],spectra[0,.5]+.01)
        self.assertLess(spectra[1,5],.7)

    def test_no_fixed_pitch_head_pulse_with_modulation_disabled(self):
        # 125 Hz was an especially strong cancellation/pulse case for the old 120 ms heads.
        for tone in (125,220,371):
            e=StardustDSP(48000,self.library);self.addCleanup(e.close)
            p=Params(**{'stardust.input':0,'stardust.predelay':0,'stardust.return':1,'stardust.pitch':12,'stardust.depth':0,'stardust.size':.5,'stardust.decay':.8})
            signal=np.repeat((.2*np.sin(np.arange(48000*12)*2*np.pi*tone/48000)).astype(np.float32)[:,None],2,axis=1)
            out=np.empty_like(signal)
            for start in range(0,len(signal),512):
                block=signal[start:start+512];out[start:start+len(block)]=e.process(block,block.copy(),p)
            envelope=np.sqrt(np.mean(out[48000*4:].reshape(-1,240,2)**2,axis=1))
            spec=np.abs(np.fft.rfft((envelope-envelope.mean(axis=0))*np.hanning(len(envelope))[:,None],axis=0))
            frequencies=np.fft.rfftfreq(len(envelope),.005)
            band=(frequencies>=5)&(frequencies<=30)
            pulse=np.max(spec[band],axis=0)/(len(envelope)/4*envelope.mean(axis=0))
            self.assertLess(float(max(pulse)),.12,(tone,pulse))
        # Frequency cannot add movement when Depth is zero.
        slow=self.render(seconds=1,**{'stardust.depth':0,'stardust.frequency':.05})
        fast=self.render(seconds=1,**{'stardust.depth':0,'stardust.frequency':5})
        np.testing.assert_array_equal(slow,fast)

    def test_depth_modulates_pitch_without_fast_envelope_beating(self):
        # The 20% onset reported on device is reproduced on a sustained 220 Hz note.
        # Keep the blend and Depth scaling unchanged: no pulse from moving FDN resonances.
        for depth in (.18,.2,.3,.5,1.):
            e=StardustDSP(48000,self.library);self.addCleanup(e.close)
            p=Params(**{'stardust.input':0,'stardust.predelay':0,'stardust.return':1,'stardust.pitch':12,'stardust.depth':depth,'stardust.frequency':.5,'stardust.size':.5,'stardust.decay':.8})
            signal=np.repeat((.2*np.sin(np.arange(48000*12)*2*np.pi*220/48000)).astype(np.float32)[:,None],2,axis=1)
            out=np.empty_like(signal)
            for start in range(0,len(signal),512):
                block=signal[start:start+512];out[start:start+len(block)]=e.process(block,block.copy(),p)
            envelope=np.sqrt(np.mean(out[48000*4:].reshape(-1,240,2)**2,axis=1))
            spec=np.abs(np.fft.rfft((envelope-envelope.mean(axis=0))*np.hanning(len(envelope))[:,None],axis=0))
            frequencies=np.fft.rfftfreq(len(envelope),.005)
            band=(frequencies>=5)&(frequencies<=30)
            pulse=np.max(spec[band],axis=0)/(len(envelope)/4*envelope.mean(axis=0))
            self.assertLess(float(max(pulse)),.08,(depth,pulse))
            self.assertLess(float(max(envelope.std(axis=0)/envelope.mean(axis=0))),.2,(depth,))

    def test_rhythmic_input_tail_at_reported_modulation_settings(self):
        e=StardustDSP(48000,self.library);self.addCleanup(e.close)
        p=Params(**{'stardust.input':0,'stardust.predelay':0,'stardust.return':1,'stardust.pitch':12,'stardust.depth':.2,'stardust.frequency':.5,'stardust.size':.5,'stardust.decay':.8})
        time=np.arange(48000*20)/48000;beat=time%.5
        envelope=(1-np.exp(-beat/.003))*np.exp(-beat/.07)*(time<10)
        signal=np.repeat((.2*np.sin(time*2*np.pi*220)*envelope).astype(np.float32)[:,None],2,axis=1)
        out=np.empty_like(signal)
        for start in range(0,len(signal),512):
            block=signal[start:start+512];out[start:start+len(block)]=e.process(block,block.copy(),p)
        self.assertTrue(np.isfinite(out).all())
        # After input stops, distinguish periodic fast beating from the smooth tail decay.
        env=np.sqrt(np.mean(out[48000*12:48000*18].reshape(-1,240,2)**2,axis=1))
        grid=np.arange(len(env))*.005
        trend=np.exp(np.stack([np.polyval(np.polyfit(grid,np.log(env[:,c]+1e-12),1),grid) for c in (0,1)],axis=1))
        normalized=env/trend
        spec=np.abs(np.fft.rfft((normalized-normalized.mean(axis=0))*np.hanning(len(env))[:,None],axis=0))
        frequencies=np.fft.rfftfreq(len(env),.005);band=(frequencies>=5)&(frequencies<=30)
        self.assertLess(float(np.max(spec[band])/(len(env)/4)),.12)

    def test_depth_gives_background_drift_and_fine_lower_range(self):
        excursions={}
        for depth in (0.,.2,.5,1.):
            e=StardustDSP(48000,self.library);self.addCleanup(e.close)
            p=Params(**{'stardust.input':0,'stardust.predelay':0,'stardust.return':1,'stardust.pitch':12,'stardust.depth':depth,'stardust.frequency':.5,'stardust.size':.5,'stardust.decay':.8})
            signal=np.repeat((.2*np.sin(np.arange(48000*14)*2*np.pi*220/48000)).astype(np.float32)[:,None],2,axis=1)
            out=np.empty_like(signal)
            for start in range(0,len(signal),512):
                block=signal[start:start+512];out[start:start+len(block)]=e.process(block,block.copy(),p)
            # Measure the audible octave's coherent frequency drift, excluding other harmonics.
            section=out[48000*4:48000*14,0];spectrum=np.fft.fft(section)
            frequencies=np.fft.fftfreq(len(section),1/48000)
            spectrum[(frequencies<400)|(frequencies>480)]=0
            analytic=np.fft.ifft(spectrum)
            instant=np.diff(np.unwrap(np.angle(analytic)))*48000/(2*np.pi)
            instant=instant[48000:48000*9].reshape(-1,240).mean(axis=1)
            time=np.arange(len(instant))*.005
            design=np.stack([np.ones_like(time),np.sin(time*np.pi),np.cos(time*np.pi),time],axis=1)
            fit=np.linalg.lstsq(design,instant,rcond=None)[0]
            excursions[depth]=float(1200*np.log2(1+np.hypot(fit[1],fit[2])/440))
        self.assertLess(excursions[0.],.1)
        self.assertLess(excursions[.2],1.)
        self.assertGreater(excursions[.5],3.);self.assertLess(excursions[.5],6.)
        self.assertGreater(excursions[1.],18.);self.assertLess(excursions[1.],28.)
        self.assertLess(excursions[.2],excursions[.5]*.3)

    def render_signal(self,signal,**values):
        engine=StardustDSP(48000,self.library);p=Params(**values);out=np.empty_like(signal)
        try:
            for start in range(0,len(signal),512):
                block=signal[start:start+512];out[start:start+len(block)]=engine.process(block,block.copy(),p)
            return out
        finally:engine.close()

    def test_wet_presence_and_decay_do_not_starve_the_send(self):
        time=np.arange(48000*10)/48000;ratios={}
        for kind in ('noise','chord','rhythm'):
            if kind=='noise':signal=np.random.default_rng(5).normal(0,.1,(len(time),2)).astype(np.float32)
            else:
                mono=sum(np.sin(time*2*np.pi*f) for f in (110,164.81,220,261.63))*.05
                if kind=='rhythm':mono*=(1-np.exp(-(time%.5)/.003))*np.exp(-(time%.5)/.08)
                signal=np.repeat(mono.astype(np.float32)[:,None],2,axis=1)
            dry=float(np.sqrt(np.mean(signal[240000:]**2)))
            for decay in (0.,1.):
                out=self.render_signal(signal,**{'stardust.input':0,'stardust.return':1,'stardust.predelay':0,'stardust.pitch':12,'stardust.depth':.25,'stardust.frequency':.5,'stardust.size':.5,'stardust.decay':decay})
                ratios[kind,decay]=float(np.sqrt(np.mean(out[240000:]**2)))/dry
        self.assertGreater(ratios['noise',1.],.3)
        self.assertGreater(ratios['chord',1.],.7)
        self.assertGreater(ratios['rhythm',1.],.65)
        self.assertGreater(ratios['noise',1.],ratios['noise',0.]*.85)

    def test_control_endpoints_change_the_audible_dry_wet_result(self):
        time=np.arange(48000*8)/48000;beat=time%.5
        mono=sum(np.sin(time*2*np.pi*f) for f in (110,164.81,220,261.63))*.04
        mono*=(.25+.75*(1-np.exp(-beat/.003))*np.exp(-beat/.08))
        signal=np.repeat(mono.astype(np.float32)[:,None],2,axis=1)
        reference=float(np.sqrt(np.mean(signal[192000:]**2)))
        ranges={'predelay':(-1000,1000),'size':(0,1),'decay':(0,1),'pitch':(-12,12),'brightness':(0,1),'frequency':(.05,5),'depth':(0,1),'input':(0,1),'send':(0,1),'return':(0,1)}
        for key,limits in ranges.items():
            outputs=[self.render_signal(signal,**{'stardust.input':.7,'stardust.return':.8,'stardust.predelay':0,'stardust.pitch':12,'stardust.depth':.75,'stardust.frequency':.5,'stardust.size':.5,'stardust.decay':.75,'stardust.'+key:value})[192000:] for value in limits]
            contrast=float(np.sqrt(np.mean((outputs[1]-outputs[0])**2)))/reference
            self.assertGreater(contrast,.35,(key,contrast))

    def test_strong_wet_output_has_headroom_and_return_zero_is_exact(self):
        time=np.arange(48000*12)/48000
        mono=sum(np.sin(time*2*np.pi*f) for f in (110,164.81,220,261.63))
        mono*=.99/np.max(np.abs(mono));signal=np.repeat(mono.astype(np.float32)[:,None],2,axis=1)
        values={'stardust.input':1,'stardust.return':1,'stardust.predelay':0,'stardust.pitch':12,'stardust.depth':1,'stardust.frequency':5,'stardust.size':.5,'stardust.decay':1}
        out=self.render_signal(signal,**values)
        self.assertTrue(np.isfinite(out).all());self.assertLessEqual(float(np.max(np.abs(out))),.981)
        values['stardust.return']=0
        np.testing.assert_array_equal(self.render_signal(signal,**values),signal)

    def test_return_ramp_does_not_switch_headroom_abruptly(self):
        e=StardustDSP(48000,self.library);self.addCleanup(e.close)
        p=Params(**{'stardust.input':1,'stardust.return':0,'stardust.send':0,'stardust.predelay':0})
        signal=np.full((512,2),.99,np.float32)
        np.testing.assert_array_equal(e.process(signal,signal.copy(),p),signal)
        p.values['stardust.return']=.02
        out=e.process(signal,signal.copy(),p)
        self.assertLess(abs(float(out[0,0])-.99),.001)
        self.assertLess(float(np.max(np.abs(np.diff(out[:,0])))),.001)

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
