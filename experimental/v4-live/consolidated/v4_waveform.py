"""Fill display-column gaps in the original waveform; audio and markers stay native."""
import numpy as np


def install():
    from ui.waveform import WaveformView
    original=WaveformView.draw
    if getattr(original,'_v4_continuous_waveform',False):return

    def draw(self,surface,rect,*args,**kwargs):
        points=self.points
        width=int(rect[2])
        # Native draw spreads isolated one-pixel strokes across the entire rect.
        # Slightly over one peak per pixel avoids holes from integer rounding.
        if len(points)<2 or width<=0 or len(points)>=width+2:
            return original(self,surface,rect,*args,**kwargs)
        cached=getattr(self,'_v4_continuous_peaks',None)
        if cached is None or cached[0] is not points or cached[1]!=width:
            dense=np.interp(np.linspace(0,len(points)-1,width+2),np.arange(len(points)),points).tolist()
            cached=(points,width,dense)
            self._v4_continuous_peaks=cached
        self.points=cached[2]
        try:return original(self,surface,rect,*args,**kwargs)
        finally:self.points=points

    draw._v4_continuous_waveform=True
    WaveformView.draw=draw
