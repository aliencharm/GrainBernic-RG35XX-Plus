"""Exercise real ALSA routing with generated multichannel files; no hardware is opened."""
import ctypes as c,os,sys,tempfile
from pathlib import Path
from channel_routes import route_definition
def main():
    with tempfile.TemporaryDirectory(prefix='v4-route-') as temporary:
        root=Path(temporary)
        frames=512
        raw=(c.c_int32*(frames*8))(*[(channel+1)*1000*65536 for _ in range(frames) for channel in range(8)])
        (root/'input.raw').write_bytes(bytes(raw))
        def r(name,first):return dict(alias=name,first=first,channels=8,format='S32_LE')
        text='</usr/share/alsa/alsa.conf>\n'
        text+=f'pcm.v4_file_in {{ type file slave.pcm "null" infile "{root}/input.raw" file "/dev/null" format "raw" }}\n'
        text+=f'pcm.v4_file_out {{ type file slave.pcm "null" file "{root}/output.raw" format "raw" }}\n'
        text+=route_definition(r('test_in',2),'v4_file_in')+route_definition(r('test_out',4),'v4_file_out')
        (root/'alsa.conf').write_text(text);os.environ['ALSA_CONFIG_PATH']=str(root/'alsa.conf')
        lib=c.CDLL('libasound.so.2')
        lib.snd_pcm_open.argtypes=[c.POINTER(c.c_void_p),c.c_char_p,c.c_int,c.c_int]
        lib.snd_pcm_set_params.argtypes=[c.c_void_p,c.c_int,c.c_int,c.c_uint,c.c_uint,c.c_int,c.c_uint]
        lib.snd_pcm_readi.argtypes=[c.c_void_p,c.c_void_p,c.c_ulong];lib.snd_pcm_readi.restype=c.c_long
        lib.snd_pcm_writei.argtypes=[c.c_void_p,c.c_void_p,c.c_ulong];lib.snd_pcm_writei.restype=c.c_long
        lib.snd_pcm_close.argtypes=[c.c_void_p];lib.snd_pcm_drain.argtypes=[c.c_void_p]
        def open(name,direction):
         pcm=c.c_void_p();e=lib.snd_pcm_open(c.byref(pcm),name.encode(),direction,0);assert e>=0,('open',e,text)
         e=lib.snd_pcm_set_params(pcm,2,3,2,48000,1,64000);assert e>=0,('params',e)
         return pcm
        pcm=open('test_in',1);audio=(c.c_int16*(frames*2))();n=lib.snd_pcm_readi(pcm,audio,frames);assert n==frames,n;lib.snd_pcm_close(pcm)
        assert list(audio)==[v for _ in range(frames) for v in (3000,4000)],list(audio)[:16]
        pcm=open('test_out',0);audio=(c.c_int16*(frames*2))(*[v for _ in range(frames) for v in (1000,2000)])
        assert lib.snd_pcm_writei(pcm,audio,frames)==frames;lib.snd_pcm_drain(pcm);lib.snd_pcm_close(pcm)
        values=(c.c_int32*(len((root/'output.raw').read_bytes())//4)).from_buffer_copy((root/'output.raw').read_bytes())
        assert list(values)[:8]==[0,0,0,0,1000*65536,2000*65536,0,0],list(values)[:8]
        print('PASS actual ALSA route plugin: 8-channel S32 capture 3-4 -> stereo S16; stereo S16 -> output 5-6 with others silent')

if __name__=='__main__':main()
