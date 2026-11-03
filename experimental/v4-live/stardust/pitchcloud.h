/* Independent streaming phase-vocoder pitch cloud, normalized overlap/add.
   No periodic crossfade between delay heads: that can beat audibly on tones. */
#define PC_N 2048
#define PC_HOP 512
#define PC_BINS (PC_N/2+1)
typedef struct {
 float input[2][PC_N],output[2][PC_N];
 float previous[2][PC_BINS],phase[2][PC_BINS];
 float synth_real[2][PC_BINS],synth_imag[2][PC_BINS];
 float window[PC_N],wr[PC_N/2],wi[PC_N/2];
 unsigned short reverse[PC_N];
 float real[PC_N],imag[PC_N],magnitude[PC_BINS],frequency[PC_BINS];
 int position,count;
} PitchCloud;
static void cloud_init(PitchCloud*p){
 memset(p,0,sizeof(*p));
 for(int i=0;i<PC_N;i++){
  p->window[i]=.5f-.5f*cosf(2*PI*i/PC_N);
  unsigned v=i,r=0;for(int b=0;b<11;b++){r=(r<<1)|(v&1);v>>=1;}p->reverse[i]=r;
 }
 for(int i=0;i<PC_N/2;i++){p->wr[i]=cosf(2*PI*i/PC_N);p->wi[i]=-sinf(2*PI*i/PC_N);}
}
static void cloud_clear(PitchCloud*p){
 memset(p->input,0,sizeof(p->input));memset(p->output,0,sizeof(p->output));
 memset(p->previous,0,sizeof(p->previous));memset(p->phase,0,sizeof(p->phase));
 p->position=p->count=0;
}
static void cloud_fft(PitchCloud*p,int inverse){
 for(int i=0;i<PC_N;i++){
  int j=p->reverse[i];if(j>i){float v=p->real[i];p->real[i]=p->real[j];p->real[j]=v;v=p->imag[i];p->imag[i]=p->imag[j];p->imag[j]=v;}
 }
 for(int length=2;length<=PC_N;length*=2){
  int half=length/2,stride=PC_N/length;
  for(int base=0;base<PC_N;base+=length)for(int j=0;j<half;j++){
   int a=base+j,b=a+half,t=j*stride;
   float wr=p->wr[t],wi=inverse?-p->wi[t]:p->wi[t];
   float re=wr*p->real[b]-wi*p->imag[b],im=wr*p->imag[b]+wi*p->real[b];
   p->real[b]=p->real[a]-re;p->imag[b]=p->imag[a]-im;p->real[a]+=re;p->imag[a]+=im;
  }
 }
 if(inverse)for(int i=0;i<PC_N;i++){p->real[i]/=PC_N;p->imag[i]/=PC_N;}
}
/* Bounded-error phase estimate (under 4 mrad), avoiding atan2 in the audio loop.
   Phase-difference errors telescope, instead of accumulating a frequency bias. */
static float cloud_angle(float y,float x){
 float ax=fabsf(x),ay=fabsf(y),hi=fmaxf(ax,ay),lo=fminf(ax,ay);
 float a=hi>1e-20f?lo/hi:0;
 float angle=a*(PI*.25f+.273f*(1-a));
 if(ay>ax)angle=PI*.5f-angle;
 if(x<0)angle=PI-angle;
 return y<0?-angle:angle;
}
static void cloud_polar(PitchCloud*p,float phase,float magnitude,float*re,float*im){
 float pos=phase*(PC_N/(2*PI));if(pos<0)pos+=PC_N;
 int i=(int)pos;if(i>=PC_N)i=0;
 float fraction=pos-floorf(pos);int j=(i+1)%PC_N;
 float sign_i=i<PC_N/2?1.f:-1.f,sign_j=j<PC_N/2?1.f:-1.f;
 int a=i%(PC_N/2),b=j%(PC_N/2);
 *re=magnitude*(sign_i*p->wr[a]+fraction*(sign_j*p->wr[b]-sign_i*p->wr[a]));
 *im=-magnitude*(sign_i*p->wi[a]+fraction*(sign_j*p->wi[b]-sign_i*p->wi[a]));
}
static void cloud_frame(PitchCloud*p,const float ratio[2],int start){
 /* Pack both real channels into one complex FFT, then unpack their spectra. */
 for(int i=0;i<PC_N;i++){
  int pos=(start+i)%PC_N;
  p->real[i]=p->input[0][pos]*p->window[i];p->imag[i]=p->input[1][pos]*p->window[i];
 }
 cloud_fft(p,0);
 for(int channel=0;channel<2;channel++){
  memset(p->magnitude,0,sizeof(p->magnitude));memset(p->frequency,0,sizeof(p->frequency));
  for(int k=1;k<PC_N/2;k++){
   int mirror=PC_N-k;
   float re=channel?.5f*(p->imag[k]+p->imag[mirror]):.5f*(p->real[k]+p->real[mirror]);
   float im=channel?.5f*(p->real[mirror]-p->real[k]):.5f*(p->imag[k]-p->imag[mirror]);
   float power=re*re+im*im,phase=cloud_angle(im,re);
   float expected=2*PI*PC_HOP*k/PC_N;
   float delta=phase-p->previous[channel][k]-expected;p->previous[channel][k]=phase;
   delta-=2*PI*floorf(delta/(2*PI)+.5f);
   float frequency=(k+delta*PC_N/(2*PI*PC_HOP))*ratio[channel];
   float target=k*ratio[channel];int bin=(int)target;float fraction=target-bin;
   /* Redistribute energy, not summed amplitudes: down-shifts must not amplify the loop. */
   for(int j=0;j<2;j++)if(bin+j>0&&bin+j<PC_N/2){
    float weight=power*(j?fraction:1-fraction);
    p->magnitude[bin+j]+=weight;p->frequency[bin+j]+=weight*frequency;
   }
  }
  for(int k=1;k<PC_N/2;k++){
   float power=p->magnitude[k],magnitude=sqrtf(power);
   float frequency=power>1e-30f?p->frequency[k]/power:(float)k;
   float phase=p->phase[channel][k]+2*PI*PC_HOP*frequency/PC_N;
   phase-=2*PI*floorf(phase/(2*PI)+.5f);p->phase[channel][k]=phase;
   float re,im;cloud_polar(p,phase,magnitude,&re,&im);
   p->synth_real[channel][k]=re;p->synth_imag[channel][k]=im;
  }
 }
 memset(p->real,0,sizeof(p->real));memset(p->imag,0,sizeof(p->imag));
 for(int k=1;k<PC_N/2;k++){
  float lr=p->synth_real[0][k],li=p->synth_imag[0][k],rr=p->synth_real[1][k],ri=p->synth_imag[1][k];
  p->real[k]=lr-ri;p->imag[k]=li+rr;p->real[PC_N-k]=lr+ri;p->imag[PC_N-k]=-li+rr;
 }
 cloud_fft(p,1);
 /* Four periodic Hann windows: sum(window^2) = 1.5, constant over a hop. */
 for(int i=0;i<PC_N;i++){
  int pos=(start+i)%PC_N;float window=p->window[i]*(2.f/3.f);
  p->output[0][pos]+=p->real[i]*window;p->output[1][pos]+=p->imag[i]*window;
 }
}
static void cloud_tick(PitchCloud*p,const float input[2],float output[2],const float ratio[2]){
 int pos=p->position;
 for(int c=0;c<2;c++){
  output[c]=p->output[c][pos];p->output[c][pos]=0;p->input[c][pos]=input[c];
 }
 p->position=(pos+1)%PC_N;
 if(++p->count==PC_HOP){
  p->count=0;
  cloud_frame(p,ratio,p->position);
 }
}
