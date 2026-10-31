/* Fault-injection ALSA shim for tests only; NEVER include in a device package. */
#define _POSIX_C_SOURCE 200809L
#include <alsa/asoundlib.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
typedef struct { unsigned calls; int stream; } Fake;
static int injected;
static const char *mode(void) { const char *s=getenv("V4_TEST_FAULT"); return s?s:"partial"; }
int snd_pcm_open(snd_pcm_t **p,const char *n,snd_pcm_stream_t s,int m) { (void)n;(void)m; Fake *f=calloc(1,sizeof(*f)); if(!f) return -ENOMEM; f->stream=s; *p=(snd_pcm_t*)f; return 0; }
int snd_pcm_close(snd_pcm_t *p) { free(p); return 0; }
int snd_pcm_set_params(snd_pcm_t *p,snd_pcm_format_t f,snd_pcm_access_t a,unsigned c,unsigned r,int soft,unsigned l) { (void)p;(void)f;(void)a;(void)c;(void)r;(void)soft;(void)l; return 0; }
int snd_pcm_get_params(snd_pcm_t *p,snd_pcm_uframes_t *b,snd_pcm_uframes_t *r) { (void)p; *b=1152;*r=288;return 0; }
snd_pcm_sframes_t snd_pcm_readi(snd_pcm_t *p,void *b,snd_pcm_uframes_t n) {
 Fake *f=(Fake*)p; f->calls++;
 if(!strcmp(mode(),"timeout")) return -EAGAIN;
 if(!strcmp(mode(),"disconnect")) return -ENODEV;
 if(!strcmp(mode(),"xrun") && f->calls==4 && !injected) { injected=1; return -EPIPE; }
 if(n>17) n=17;
 memset(b,0,n*4); return (snd_pcm_sframes_t)n;
}
snd_pcm_sframes_t snd_pcm_writei(snd_pcm_t *p,const void *b,snd_pcm_uframes_t n) {
 (void)b; Fake *f=(Fake*)p; f->calls++;
 if(!strcmp(mode(),"write-xrun") && f->calls==4 && !injected) { injected=1; return -EPIPE; }
 if(n>13) n=13;
 return (snd_pcm_sframes_t)n;
}
int snd_pcm_wait(snd_pcm_t *p,int ms) { (void)p;(void)ms; struct timespec t={0,2000000}; nanosleep(&t,NULL); return 1; }
int snd_pcm_prepare(snd_pcm_t *p) { (void)p; return 0; }
int snd_pcm_drain(snd_pcm_t *p) { (void)p; return 0; }
int snd_pcm_drop(snd_pcm_t *p) { (void)p; return 0; }
const char *snd_strerror(int e) { return strerror(e<0?-e:e); }
int snd_pcm_hw_params_malloc(snd_pcm_hw_params_t **p) { *p=calloc(1,16); return *p?0:-ENOMEM; }
void snd_pcm_hw_params_free(snd_pcm_hw_params_t *p) { free(p); }
int snd_pcm_hw_params_current(snd_pcm_t *p,snd_pcm_hw_params_t *h) { (void)p;(void)h; return 0; }
int snd_pcm_hw_params_get_rate(const snd_pcm_hw_params_t *p,unsigned *r,int *d) { (void)p; *r=!strcmp(mode(),"rate")?44100:48000; *d=0; return 0; }
int snd_pcm_hw_params_get_channels(const snd_pcm_hw_params_t *p,unsigned *c) { (void)p;*c=2;return 0; }
int snd_pcm_hw_params_get_format(const snd_pcm_hw_params_t *p,snd_pcm_format_t *f) { (void)p;*f=SND_PCM_FORMAT_S16_LE;return 0; }
