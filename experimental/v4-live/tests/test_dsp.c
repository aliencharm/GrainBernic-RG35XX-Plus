#include "dsp.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
static void frame(Dsp *d,float x,float *last) { float in[2]={x,-x},out[2]; dsp_frame(d,in,out); assert(isfinite(out[0])&&isfinite(out[1])); assert(fabsf(out[0])<=.981f); assert(fabsf(out[0]+out[1])<1e-6); *last=out[0]; }
int main(void) {
 Dsp d; float v=0; assert(dsp_init(&d)==0);
 d.gain=d.target_gain=1;
 for(int i=0;i<48000;i++) { float x=.2f*sinf(i*.1f); frame(&d,x,&v); assert(fabsf(v-x)<1e-6); }
 d.mix=d.target_mix=1;
 /* Warm past the entire ring with fresh constant input: wet must update. */
 for(int i=0;i<V4_HISTORY*2;i++) frame(&d,.3f,&v);
 assert(fabsf(v-.3f)<1e-4);
 for(int i=0;i<V4_HISTORY*2;i++) frame(&d,-.2f,&v);
 assert(fabsf(v+.2f)<1e-4);
 for(int i=0;i<V4_HISTORY*2;i++) frame(&d,0,&v);
 assert(fabsf(v)<1e-6); /* Old material was overwritten, not looping. */
 /* Exercise control extremes, many wraps and varying conceptual block boundaries. */
 for(int block=1;block<=1024;block*=2) for(int b=0;b<180;b++) {
  d.grain_ms=(b%2)?10:250; d.pitch=(b%3)?0.5f:2;
  d.delay_ms=(b%2)?10:1000; d.target_mix=(b%2)?1:0;
  for(int j=0;j<block;j++) frame(&d,.2f*sinf((float)d.written*.04f),&v);
 }
 dsp_free(&d);
 assert(dsp_init(&d)==0); d.mix=d.target_mix=1;
 for(int i=0;i<400;i++) { frame(&d,.3f,&v); assert(v==0); }
 frame(&d,NAN,&v); assert(isfinite(v)); dsp_free(&d);
 puts("PASS dry identity, wet responds to new input, history overwrite, silence, startup, finite stereo output, control extremes and ring wraps");
 return 0;
}
