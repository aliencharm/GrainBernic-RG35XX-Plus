/* Dense asynchronous granular pitch cloud; no FFT and no periodic pitch-head clock. */
#define GC_VOICES 8
typedef struct {float position,age,length,step,age_step;} CloudGrain;
typedef struct {
 float *history;int capacity,write,rate,ready;
 CloudGrain grain[2][GC_VOICES];
 float window[1025],wander[2],from[2],target[2],motion;
 unsigned random,motion_random;
} PitchCloud;
static float cloud_random(unsigned*s){unsigned x=*s;x^=x<<13;x^=x>>17;x^=x<<5;*s=x;return (x>>8)*(1.f/16777216.f);}
static void cloud_init(PitchCloud*p,int rate){
 memset(p,0,sizeof(*p));p->rate=rate;p->capacity=(int)(rate*.40f)+64;
 p->history=calloc(2*p->capacity,sizeof(float));p->random=0x19bc713u;p->motion_random=0xb895d51u;
 for(int i=0;i<=1024;i++)p->window[i]=.5f-.5f*cosf(2*PI*i/1024);
}
static void cloud_clear(PitchCloud*p){
 memset(p->history,0,2*p->capacity*sizeof(float));memset(p->grain,0,sizeof(p->grain));
 memset(p->wander,0,sizeof(p->wander));memset(p->from,0,sizeof(p->from));memset(p->target,0,sizeof(p->target));
 p->write=p->ready=0;p->motion=0;p->random=0x19bc713u;p->motion_random=0xb895d51u;
}
static void cloud_spawn(PitchCloud*p,int c,int voice,float ratio,float texture,float grain_ms,float age){
 CloudGrain*g=&p->grain[c][voice];
 float random=cloud_random(&p->random);
 g->length=p->rate*.001f*grain_ms*(.9f+.2f*random);
 g->age_step=1/g->length;
 float detune=texture*(.004f*p->wander[c]+.003f*(2*cloud_random(&p->random)-1));
 g->step=ratio*(1+detune);g->age=age;
 float delay=p->rate*(.003f+.001f*c+texture*(.006f*cloud_random(&p->random)+.002f*(p->wander[c]+1)));
 delay+=fmaxf(0,g->step*1.03f-1)*(g->length-1)-(g->step-1)*age*g->length;
 g->position=p->write-delay;while(g->position<0)g->position+=p->capacity;while(g->position>=p->capacity)g->position-=p->capacity;
}
static void cloud_tick(PitchCloud*p,const float input[2],float output[2],const float ratio[2],float texture,float speed,float grain_ms,float lfo_ratio){
 p->motion+=speed/p->rate;
 if(p->motion>=1||!p->ready){
  p->motion-=floorf(p->motion);
  for(int c=0;c<2;c++){p->from[c]=p->target[c];p->target[c]=2*cloud_random(&p->motion_random)-1;}
 }
 float curve=p->motion*p->motion*(3-2*p->motion);
 for(int c=0;c<2;c++)p->wander[c]=p->from[c]+(p->target[c]-p->from[c])*curve;
 for(int c=0;c<2;c++)p->history[2*p->write+c]=input[c];
 if(!p->ready){for(int c=0;c<2;c++)for(int v=0;v<GC_VOICES;v++)cloud_spawn(p,c,v,ratio[c],texture,grain_ms,(v+.13f*c)/GC_VOICES);p->ready=1;}
 for(int c=0;c<2;c++){
  float sum=0,weight=0;
  for(int v=0;v<GC_VOICES;v++){
   CloudGrain*g=&p->grain[c][v];
   if(g->age>=1)cloud_spawn(p,c,v,ratio[c],texture,grain_ms,0);
   float phase=g->age*1024;int k=(int)phase;float fraction=phase-k;
   float w=p->window[k]+fraction*(p->window[k+1]-p->window[k]);
   int a=(int)g->position,b=a+1;if(b==p->capacity)b=0;fraction=g->position-a;
   float value=p->history[2*a+c]+fraction*(p->history[2*b+c]-p->history[2*a+c]);
   sum+=w*value;weight+=w;
   g->position+=g->step*lfo_ratio;if(g->position>=p->capacity)g->position-=p->capacity;
   g->age+=g->age_step;
  }
  output[c]=sum/fmaxf(weight,.1f);
 }
 if(++p->write==p->capacity)p->write=0;
}
