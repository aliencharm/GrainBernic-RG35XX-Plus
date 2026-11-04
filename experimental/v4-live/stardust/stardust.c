/* Stardust: independent stereo feedback-network shimmer, not Sinevibes code. */
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#define PI 3.14159265358979323846f
#define LINES 8
#include "pitchcloud.h"
typedef struct {
 int sr,fdn_cap,pre_cap,wi,prewi,ready;
 float *fdn,*pre,*dry;
 PitchCloud cloud;
 float damp[8],damp2[8],delay[8],gain[8],norm[8],hp[2],early_lp[2][2],low_body[2];
 float aa_coeff[4][5],aa_state[2][4][2];
 float diffuse[2][4][1024];int dpi[2][4],dlen[2][4];
 float ratio,bright,send,ret,input,pretime,depth;
} Stardust;
static const float times[8]={.0297f,.0371f,.0411f,.0437f,.0533f,.0617f,.0713f,.0797f};
static const float sl[8]={1,1,1,1,-1,-1,-1,-1};
static const float srn[8]={1,-1,1,-1,1,-1,1,-1};
static float clamp(float x,float lo,float hi){return fminf(hi,fmaxf(lo,x));}
static float clean(float x){return isfinite(x)&&fabsf(x)>1e-20f?clamp(x,-8.f,8.f):0.f;}
static float read1(const float*b,int cap,int wi,float delay){
 float p=wi-delay;while(p<0)p+=cap;while(p>=cap)p-=cap;
 int i=(int)p,j=i+1;if(j==cap)j=0;float f=p-i;return b[i]+f*(b[j]-b[i]);
}
static float read2(const float*b,int cap,int wi,float delay,int c){
 float p=wi-delay;while(p<0)p+=cap;while(p>=cap)p-=cap;
 int i=(int)p,j=i+1;if(j==cap)j=0;float f=p-i;return b[2*i+c]+f*(b[2*j+c]-b[2*i+c]);
}
void* stardust_create(int rate){
 if(rate<8000||rate>96000)return NULL;
 Stardust*s=calloc(1,sizeof(*s));if(!s)return NULL;
 s->sr=rate;s->fdn_cap=(int)(rate*.42f)+32;s->pre_cap=(int)(rate*1.01f)+8;
 s->fdn=calloc(8*s->fdn_cap,sizeof(float));s->pre=calloc(2*s->pre_cap,sizeof(float));s->dry=calloc(2*s->pre_cap,sizeof(float));
 if(!s->fdn||!s->pre||!s->dry){free(s->fdn);free(s->pre);free(s->dry);free(s);return NULL;}
 for(int c=0;c<2;c++)for(int j=0;j<4;j++){int base[4]={149,211,263,293};s->dlen[c][j]=(base[j]+c*17)*rate/48000;}
 cloud_init(&s->cloud,rate);
 if(!s->cloud.history){free(s->fdn);free(s->pre);free(s->dry);free(s);return NULL;}
 return s;
}
void stardust_clear(void*handle){
 Stardust*s=handle;if(!s)return;
 memset(s->fdn,0,8*s->fdn_cap*sizeof(float));memset(s->pre,0,2*s->pre_cap*sizeof(float));memset(s->dry,0,2*s->pre_cap*sizeof(float));
 memset(s->diffuse,0,sizeof(s->diffuse));memset(s->dpi,0,sizeof(s->dpi));
 memset(s->early_lp,0,sizeof(s->early_lp));memset(s->low_body,0,sizeof(s->low_body));
 memset(s->damp,0,sizeof(s->damp));memset(s->hp,0,sizeof(s->hp));memset(s->damp2,0,sizeof(s->damp2));memset(s->aa_state,0,sizeof(s->aa_state));
 s->wi=s->prewi=0;cloud_clear(&s->cloud);s->ready=0;
}
void stardust_destroy(void*handle){Stardust*s=handle;if(s){free(s->fdn);free(s->pre);free(s->dry);free(s->cloud.history);free(s);}}
/* p: predelay ms, size, decay, pitch st, brightness, freq Hz, depth, input, send, return */
int stardust_process(void*handle,const float*feed,float*audio,int frames,const float*p){
 Stardust*s=handle;if(!s||!feed||!audio||!p||frames<0)return -1;
 for(int i=0;i<10;i++)if(!isfinite(p[i]))return -2;
 /* Long diffuse bed plus a prominent stereo pitch return; no feedback gain boost. */
 float room=.2f+4.6f*clamp(p[1],0,1),rt=.25f+59.75f*powf(clamp(p[2],0,1),1.4f);
 float target_delay[8],target_gain[8],target_norm[8],mean_loss=0;
 for(int j=0;j<8;j++){
  target_delay[j]=times[j]*s->sr*room;target_gain[j]=powf(.001f,times[j]*room/rt);
  float loss=fmaxf(1e-6f,1-target_gain[j]*target_gain[j]);
  target_norm[j]=sqrtf(loss);mean_loss+=loss*.125f;
 }
 /* One network-wide loss correction preserves the relative tap balance. */
 float compensation=sqrtf((.2f+.8f*mean_loss)/mean_loss);
 for(int j=0;j<8;j++)target_norm[j]*=compensation;
 float ratio=powf(2.f,clamp(p[3],-24,24)/12.f);
 float fc=300.f*powf(60.f,clamp(p[4],0,1));fc=fminf(fc,.43f*s->sr);
 float bright=1.f-expf(-2*PI*fc/s->sr),alpha=1.f-expf(-1.f/(.02f*s->sr));
 /* Butterworth anti-aliasing is independent of the musical Brightness control. */
 float max_ratio=fmaxf(1,ratio*1.02f);
 for(int c=0;c<2;c++)for(int v=0;v<GC_VOICES;v++)max_ratio=fmaxf(max_ratio,s->cloud.grain[c][v].step);
 float omega=2*PI*.4f/max_ratio,cw=cosf(omega),sw=sinf(omega),aa_target[4][5];
 const float quality[4]={.50979558f,.60134489f,.89997622f,2.56291545f};
 for(int j=0;j<4;j++){
  float a=sw/(2*quality[j]),n=1/(1+a);
  aa_target[j][0]=(1-cw)*.5f*n;aa_target[j][1]=(1-cw)*n;aa_target[j][2]=aa_target[j][0];
  aa_target[j][3]=-2*cw*n;aa_target[j][4]=(1-a)*n;
 }
 float freq=clamp(p[5],.05f,5.f),depth=powf(clamp(p[6],0,1),1.5f)*.006f*s->sr;
 float predelay=clamp(p[0],-1000,1000)*.001f*s->sr;
 float input=clamp(p[7],0,1),send=clamp(p[8],0,1),ret=clamp(p[9],0,1);
 float body=1-expf(-2*PI*400/s->sr),dark=1-clamp(p[4],0,1);dark*=dark;
 if(!s->ready){
  for(int j=0;j<8;j++){s->delay[j]=target_delay[j];s->gain[j]=target_gain[j];s->norm[j]=target_norm[j];}
  s->ratio=ratio;s->bright=bright;memcpy(s->aa_coeff,aa_target,sizeof(aa_target));s->pretime=predelay;s->input=input;s->send=send;s->ret=ret;s->depth=depth;s->ready=1;
 }
 for(int n=0;n<frames;n++){
  s->ratio+=alpha*(ratio-s->ratio);s->bright+=alpha*(bright-s->bright);
  for(int j=0;j<4;j++)for(int k=0;k<5;k++)s->aa_coeff[j][k]+=alpha*(aa_target[j][k]-s->aa_coeff[j][k]);
  s->pretime+=alpha*(predelay-s->pretime);s->depth+=alpha*(depth-s->depth);
  s->input+=alpha*(input-s->input);s->send+=alpha*(send-s->send);s->ret+=alpha*(ret-s->ret);
  float in[2]={clean(feed[2*n])*s->send,clean(feed[2*n+1])*s->send};
  for(int c=0;c<2;c++){s->pre[2*s->prewi+c]=in[c];s->dry[2*s->prewi+c]=clean(audio[2*n+c]);}
  for(int c=0;c<2;c++)in[c]=read2(s->pre,s->pre_cap,s->prewi,fmaxf(0,s->pretime),c);
  for(int c=0;c<2;c++)for(int j=0;j<4;j++){
   int pos=s->dpi[c][j];float v=s->diffuse[c][j][pos],next=-.65f*in[c]+v;
   s->diffuse[c][j][pos]=in[c]+.65f*next;in[c]=next;
   s->dpi[c][j]=(pos+1)%s->dlen[c][j];
  }
  float z[8],sum=0,wet[2]={0,0};
  for(int j=0;j<8;j++){
   s->delay[j]+=alpha*(target_delay[j]-s->delay[j]);s->gain[j]+=alpha*(target_gain[j]-s->gain[j]);s->norm[j]+=alpha*(target_norm[j]-s->norm[j]);
   /* Keep the diffuse bed stationary: moving these eight resonances adds
      level beating alongside the intended pitch modulation, even at modest Depth. */
   float v=read1(s->fdn+j*s->fdn_cap,s->fdn_cap,s->wi,s->delay[j]);
   s->damp[j]=clean(s->damp[j]+s->bright*(v-s->damp[j]));s->damp2[j]=clean(s->damp2[j]+s->bright*(s->damp[j]-s->damp2[j]));z[j]=s->damp2[j];sum+=z[j];
   wet[0]+=z[j]*sl[j]*.35355339f;wet[1]+=z[j]*srn[j]*.35355339f;
  }
  float pitch_input[2],pitch_ratio[2],pitched[2];
  float shift=clamp(fabsf(s->ratio-1)*8,0,1);
  for(int c=0;c<2;c++){
   s->early_lp[c][0]=clean(s->early_lp[c][0]+s->bright*(in[c]-s->early_lp[c][0]));
   s->early_lp[c][1]=clean(s->early_lp[c][1]+s->bright*(s->early_lp[c][0]-s->early_lp[c][1]));
   float value=wet[c]+.35f*s->early_lp[c][1];
   for(int j=0;j<4;j++){
    float*q=s->aa_coeff[j],*z=s->aa_state[c][j],out=q[0]*value+z[0];
    if(fabsf(out)<1e-20f)out=0;
    z[0]=q[1]*value-q[3]*out+z[1];z[1]=q[2]*value-q[4]*out;value=out;
   }
   pitch_input[c]=value;
   pitch_ratio[c]=s->ratio*(1+(c? .0015f:-.0015f)*shift);
  }
  cloud_tick(&s->cloud,pitch_input,pitched,pitch_ratio,s->depth/(.006f*s->sr),freq,clamp(p[1],0,1));
  for(int c=0;c<2;c++){
   float v=clean(pitched[c]);s->hp[c]=clean(s->hp[c]+.0015f*(v-s->hp[c]));pitched[c]=v-s->hp[c];
  }
  for(int j=0;j<8;j++){
   float base=z[j]-.25f*sum;
   float shifted=(pitched[0]*sl[j]+pitched[1]*srn[j])*.35355339f;
   float injected=(in[0]*sl[j]+in[1]*srn[j])*.35355339f*s->norm[j];
   float projection=(wet[0]*sl[j]+wet[1]*srn[j])*.35355339f;
   float v=injected+s->gain[j]*(base+.44f*(shifted-projection));
   s->fdn[j*s->fdn_cap+s->wi]=clean(v);
  }
  for(int c=0;c<2;c++){
   float dry=read2(s->dry,s->pre_cap,s->prewi,fmaxf(0,-s->pretime),c);
   /* The audible return is chiefly pitched, independent of the loop's loss budget.
      Near zero transposition, retain the unshifted output without doubling it. */
   float cloud=(wet[c]+.3f*s->early_lp[c][1])*(1-.8f*shift)+pitched[c]*(1.959592f*shift);
   s->low_body[c]+=body*(cloud-s->low_body[c]);
   cloud=cloud*(1-.4f*dark)+s->low_body[c]*dark;
   /* Normalize the projected network return to a usable wet level. */
   float v=dry*s->input+2.f*cloud*s->ret;
   /* Smooth headroom at strong wet settings; Return zero retains exact dry bypass. */
   if(s->ret>1e-6f&&fabsf(v)>.9f){
    float excess=fabsf(v)-.9f,limited=copysignf(.9f+.08f*excess/(.08f+excess),v);
    v+=clamp(s->ret*10.f,0,1)*(limited-v);v=clamp(v,-1.f,1.f);
   }
   audio[2*n+c]=isfinite(v)?clamp(v,-4.f,4.f):0;
  }
  if(++s->wi==s->fdn_cap)s->wi=0;
  if(++s->prewi==s->pre_cap)s->prewi=0;
 }
 return 0;
}
