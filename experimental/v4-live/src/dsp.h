#ifndef GBV4_DSP_H
#define GBV4_DSP_H
#include <stdint.h>
#define V4_RATE 48000
#define V4_HISTORY (V4_RATE * 4)
#define V4_VOICES 16
typedef struct { double pos; unsigned age, length; float speed; int active; } Grain;
typedef struct {
 float *ring; uint64_t written; unsigned countdown; uint32_t rng;
 float mix, target_mix, gain, target_gain, grain_ms, delay_ms, pitch;
 Grain grains[V4_VOICES];
} Dsp;
int dsp_init(Dsp *d);
void dsp_free(Dsp *d);
void dsp_frame(Dsp *d, const float in[2], float out[2]);
#endif
