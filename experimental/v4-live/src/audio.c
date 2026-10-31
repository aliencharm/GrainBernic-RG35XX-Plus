#define _POSIX_C_SOURCE 200809L
#include <alsa/asoundlib.h>
#include <dlfcn.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <math.h>
#include "dsp.h"
/* Resolve system ALSA at runtime; no bundled ALSA or KNULLI configuration changes. */
#define SYMBOLS(X) \
 X(snd_pcm_drain) X(snd_pcm_open) X(snd_pcm_close) X(snd_pcm_set_params) X(snd_pcm_get_params) \
 X(snd_pcm_readi) X(snd_pcm_writei) X(snd_pcm_wait) X(snd_pcm_prepare) X(snd_pcm_drop) \
 X(snd_strerror) X(snd_pcm_hw_params_malloc) X(snd_pcm_hw_params_free) \
 X(snd_pcm_hw_params_current) X(snd_pcm_hw_params_get_rate) X(snd_pcm_hw_params_get_channels) \
 X(snd_pcm_hw_params_get_format)
#define DECL(n) static __typeof__(&n) p_##n;
SYMBOLS(DECL)
static volatile sig_atomic_t stop;
static void on_signal(int sig) { (void)sig; stop=1; }
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9; }
static int load_alsa(void) {
 void *lib=dlopen("libasound.so.2",RTLD_NOW|RTLD_LOCAL);
 if(!lib) { fprintf(stderr,"FATAL ALSA load: %s\n",dlerror()); return -1; }
#define LOAD(n) *(void **)(&p_##n)=dlsym(lib,#n); if(!p_##n) { fprintf(stderr,"FATAL missing ALSA symbol %s\n",#n); return -1; }
 SYMBOLS(LOAD)
 return 0;
}
static int configure(snd_pcm_t *pcm,const char *label,unsigned latency) {
 /* Exact application contract. ALSA plug conversion is possible only if explicitly selected. */
 int e=p_snd_pcm_set_params(pcm,SND_PCM_FORMAT_S16_LE,SND_PCM_ACCESS_RW_INTERLEAVED,2,V4_RATE,0,latency);
 if(e<0) { fprintf(stderr,"FATAL %s configure: %s\n",label,p_snd_strerror(e)); return -1; }
 snd_pcm_uframes_t buffer,period;
 snd_pcm_hw_params_t *hw=NULL; unsigned rate=0,channels=0; int direction=0; snd_pcm_format_t format;
 if(p_snd_pcm_get_params(pcm,&buffer,&period)<0 || p_snd_pcm_hw_params_malloc(&hw)<0) return -1;
 e=p_snd_pcm_hw_params_current(pcm,hw);
 if(e>=0) e=p_snd_pcm_hw_params_get_rate(hw,&rate,&direction);
 if(e>=0) e=p_snd_pcm_hw_params_get_channels(hw,&channels);
 if(e>=0) e=p_snd_pcm_hw_params_get_format(hw,&format);
 p_snd_pcm_hw_params_free(hw);
 if(e<0 || rate!=V4_RATE || channels!=2 || format!=SND_PCM_FORMAT_S16_LE) {
  fprintf(stderr,"FATAL %s negotiated format differs from 48000 Hz stereo S16_LE\n",label); return -1;
 }
 fprintf(stderr,"PCM %s rate=%u channels=%u format=S16_LE period=%lu buffer=%lu requested_latency_us=%u\n",label,rate,channels,(unsigned long)period,(unsigned long)buffer,latency);
 return 0;
}
static void controls(Dsp *d) {
 static char line[128]; static unsigned used; char ch; unsigned budget=256;
 while(budget-- && read(STDIN_FILENO,&ch,1)==1) {
  if(ch=='\n') {
   line[used]=0; float v; char key[24];
   if(!strcmp(line,"quit")) stop=1;
   else if(sscanf(line,"%23s %f",key,&v)==2 && isfinite(v)) {
    if(!strcmp(key,"mix")&&v>=0&&v<=1) d->target_mix=v;
    if(!strcmp(key,"gain")&&v>=0&&v<=1) d->target_gain=v;
    if(!strcmp(key,"grain")&&v>=10&&v<=250) d->grain_ms=v;
    if(!strcmp(key,"delay")&&v>=10&&v<=1000) d->delay_ms=v;
    if(!strcmp(key,"pitch")&&v>=.5f&&v<=2) d->pitch=v;
   }
   used=0;
  } else if(used<sizeof(line)-1) line[used++]=ch;
  else used=0;
 }
}
static int transfer(snd_pcm_t *pcm,int16_t *data,unsigned frames,int capture) {
 unsigned done=0; double deadline=now()+2.;
 while(done<frames && !stop) {
  snd_pcm_sframes_t n=capture?p_snd_pcm_readi(pcm,data+2*done,frames-done):p_snd_pcm_writei(pcm,data+2*done,frames-done);
  if(n>0) { done+=(unsigned)n; continue; }
  if(n<0 && n!=-EAGAIN && n!=-EINTR) return (int)n;
  if(now()>deadline) return -ETIMEDOUT;
  int e=p_snd_pcm_wait(pcm,50); if(e<0 && e!=-EINTR) return e;
 }
 return stop ? -EINTR : 0;
}
int main(int argc,char **argv) {
 if(argc==2 && !strcmp(argv[1],"--version")) { puts("GrainBrick V4 Live experimental 0.1.0 / independent ALSA DSP"); return 0; }
 if(argc<3 || argc>4) { fprintf(stderr,"Usage: %s CAPTURE_PCM PLAYBACK_PCM [latency_us:10000..100000]\nControls on stdin: mix 0..1, gain 0..1, grain 10..250, delay 10..1000, pitch .5..2, quit\n",argv[0]); return 2; }
 unsigned latency=24000;
 if(argc==4) { char *end; unsigned long value=strtoul(argv[3],&end,10); if(*end || value<10000 || value>100000) return 2; latency=(unsigned)value; }
 fprintf(stderr,"V4 0.1.0 capture=%s playback=%s block=128 pid=%ld\n",argv[1],argv[2],(long)getpid());
 if(load_alsa()<0) return 1;
 signal(SIGINT,on_signal); signal(SIGTERM,on_signal); signal(SIGPIPE,SIG_IGN);
 int flags=fcntl(STDIN_FILENO,F_GETFL); if(flags>=0) fcntl(STDIN_FILENO,F_SETFL,flags|O_NONBLOCK);
 snd_pcm_t *cap=NULL,*play=NULL; int result=1,e;
 Dsp dsp; if(dsp_init(&dsp)<0) return 1;
 e=p_snd_pcm_open(&cap,argv[1],SND_PCM_STREAM_CAPTURE,SND_PCM_NONBLOCK);
 if(e<0) { fprintf(stderr,"FATAL capture open: %s\n",p_snd_strerror(e)); goto end; }
 e=p_snd_pcm_open(&play,argv[2],SND_PCM_STREAM_PLAYBACK,SND_PCM_NONBLOCK);
 if(e<0) { fprintf(stderr,"FATAL playback open: %s\n",p_snd_strerror(e)); goto end; }
 if(configure(cap,"capture",latency)<0 || configure(play,"playback",latency)<0) goto end;
 int16_t input[256]={0},output[256]={0}; unsigned recoveries=0; uint64_t frames=0; double report=now(),max_dsp=0; float peak=0;
 fprintf(stderr,"READY dry monitoring; gain=0.5 mix=0.0. Hardware operation unverified.\n");
 while(!stop) {
  controls(&dsp); if(stop) break;
  e=transfer(cap,input,128,1); if(e<0) goto recover;
  double t=now();
  for(int i=0;i<128;i++) {
   float in[2]={input[2*i]/32768.f,input[2*i+1]/32768.f},out[2]; dsp_frame(&dsp,in,out);
   /* Startup fade independent of wet history. */
   float fade=fminf(1.f,(float)(frames+i)/2400.f);
   for(int c=0;c<2;c++) { float v=out[c]*fade; output[2*i+c]=(int16_t)lrintf(v*32767.f); peak=fmaxf(peak,fabsf(v)); }
  }
  double elapsed=now()-t; if(elapsed>max_dsp) max_dsp=elapsed;
  e=transfer(play,output,128,0); if(e<0) goto recover;
  frames+=128;
  if(now()-report>=2.) {
   fprintf(stderr,"STATS frames=%llu recoveries=%u dsp_max_ms=%.3f peak=%.3f mix=%.2f grain_ms=%.0f delay_ms=%.0f pitch=%.2f\n",(unsigned long long)frames,recoveries,max_dsp*1000,peak,dsp.mix,dsp.grain_ms,dsp.delay_ms,dsp.pitch);
   report=now(); max_dsp=0; peak=0;
  }
  continue;
 recover:
  if(stop) break;
  fprintf(stderr,"AUDIO_ERROR %s (%d) recovery=%u\n",p_snd_strerror(e),e,recoveries+1);
  if((e!=-EPIPE && e!=-ESTRPIPE) || ++recoveries>20) goto end;
  p_snd_pcm_drop(cap); p_snd_pcm_drop(play);
  if(p_snd_pcm_prepare(cap)<0 || p_snd_pcm_prepare(play)<0) goto end;
  /* Both queues reset together; discard stale history and fade back in. */
  float mix=dsp.target_mix,gain=dsp.target_gain,grain=dsp.grain_ms,delay=dsp.delay_ms,pitch=dsp.pitch;
  dsp_free(&dsp); if(dsp_init(&dsp)<0) goto end;
  dsp.target_mix=mix; dsp.target_gain=gain; dsp.grain_ms=grain; dsp.delay_ms=delay; dsp.pitch=pitch;
  frames=0;
 }
 if(play && frames) {
  int16_t ramp[960];
  for(int i=0;i<480;i++) for(int c=0;c<2;c++)
   ramp[2*i+c]=(int16_t)(output[254+c]*(1.f-(float)i/479.f));
  unsigned done=0; double deadline=now()+.05;
  while(done<480 && now()<deadline) {
   snd_pcm_sframes_t n=p_snd_pcm_writei(play,ramp+2*done,480-done);
   if(n>0) done+=(unsigned)n;
   else if(n==-EAGAIN) { if(p_snd_pcm_wait(play,5)<0) break; }
   else break;
  }
  /* Allow the queued fade to reach the device, with a bounded drain. */
  deadline=now()+.15;
  while(now()<deadline) {
   int draining=p_snd_pcm_drain(play);
   if(draining==0 || (draining!=-EAGAIN && draining!=-EINTR)) break;
   if(p_snd_pcm_wait(play,5)<0) break;
  }
 }
 result=0;
 end:
 if(cap) { p_snd_pcm_drop(cap); p_snd_pcm_close(cap); }
 if(play) { p_snd_pcm_drop(play); p_snd_pcm_close(play); }
 dsp_free(&dsp); fprintf(stderr,"EXIT status=%d\n",result); return result;
}
