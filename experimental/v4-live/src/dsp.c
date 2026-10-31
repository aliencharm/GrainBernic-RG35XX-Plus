#include "dsp.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
int dsp_init(Dsp *d) {
 memset(d,0,sizeof(*d)); d->ring=calloc(V4_HISTORY*2,sizeof(float));
 d->rng=0x91a32u; d->gain=d->target_gain=0.5f;
 d->grain_ms=80; d->delay_ms=120; d->pitch=1.0f;
 return d->ring ? 0 : -1;
}
void dsp_free(Dsp *d) { free(d->ring); d->ring=NULL; }
static float random01(Dsp *d) { d->rng=d->rng*1664525u+1013904223u; return (float)(d->rng>>8)/16777216.f; }
void dsp_frame(Dsp *d,const float input[2],float out[2]) {
 float in[2];
 for(int c=0;c<2;c++) { in[c]=isfinite(input[c])?input[c]:0; d->ring[(d->written%V4_HISTORY)*2+c]=in[c]; }
 d->written++;
 if(d->countdown) d->countdown--;
 else {
  unsigned length=(unsigned)(d->grain_ms*48.f);
  if(length<480) length=480;
  if(length>12000) length=12000;
  float speed=fminf(2.f,fmaxf(0.5f,d->pitch));
  double lookback=fmax(480.,d->delay_ms*48.)+length*fmax(1.,speed)+random01(d)*4800.;
  if(d->written>(uint64_t)ceil(lookback)+2) {
   for(int i=0;i<V4_VOICES;i++) if(!d->grains[i].active) {
    d->grains[i]=(Grain){.pos=(double)d->written-lookback,.length=length,.speed=speed,.active=1}; break;
   }
  }
  d->countdown=length/4-1;
 }
 float wet[2]={0,0},weight=0;
 for(int i=0;i<V4_VOICES;i++) {
  Grain *g=&d->grains[i]; if(!g->active) continue;
  uint64_t p=(uint64_t)g->pos;
  if(p+1>=d->written || (d->written>V4_HISTORY && p<d->written-V4_HISTORY)) { g->active=0; continue; }
  float f=(float)(g->pos-(double)p);
  float w=0.5f-0.5f*cosf(6.28318530718f*(float)g->age/(float)(g->length-1));
  for(int c=0;c<2;c++) wet[c]+=w*(d->ring[(p%V4_HISTORY)*2+c]*(1-f)+d->ring[((p+1)%V4_HISTORY)*2+c]*f);
  weight+=w; g->pos+=g->speed;
  if(++g->age>=g->length) g->active=0;
 }
 d->mix+=(d->target_mix-d->mix)*0.001f;
 d->gain+=(d->target_gain-d->gain)*0.001f;
 for(int c=0;c<2;c++) {
  float v=d->gain*((1-d->mix)*in[c]+d->mix*wet[c]/fmaxf(1.f,weight));
  out[c]=fmaxf(-0.98f,fminf(0.98f,v));
 }
}
