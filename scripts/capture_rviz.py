"""Capture only the RViz application window, never the desktop."""
from pathlib import Path
import os
import re
import subprocess
import time
root=Path(__file__).resolve().parents[1]
for _ in range(60):
    windows=subprocess.check_output(['xwininfo','-root','-tree'],text=True)
    matches=[line for line in windows.splitlines() if 'rviz' in line.lower() and '1280x' in line]
    if matches:break
    time.sleep(.5)
else:raise RuntimeError('No RViz window found')
window=re.search(r'0x[0-9a-f]+',matches[0]).group()
dest=root/'media'/'rviz.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','x11grab','-framerate','10','-window_id',window,'-i',os.environ.get('DISPLAY',':1'),'-t','12','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(dest),'-filter_complex','fps=8,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse','-loop','0',str(root/'media'/'rviz.gif')],check=True)
print('Captured RViz window',window)
