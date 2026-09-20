"""Run real local YOLO inference on recorded simulator RGB, with metric depth."""
from pathlib import Path
import json
import os
import sys
import numpy as np
import cv2
import torch
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
evidence=root.parent/'evidence/perception'
workspace=Path(os.environ['SPOTATS_WORKSPACE'])
weights=workspace/'phyAI_ws/yolov8m.pt'
# Explicitly opted-in local project checkpoint, never a downloaded arbitrary file.
original_load=torch.load
def load_trusted(*args,**kwargs):
    kwargs.setdefault('weights_only',False)
    return original_load(*args,**kwargs)
torch.load=load_trusted
from ultralytics import YOLO
model=YOLO(str(weights))
dest=root.parent/'evidence/perception_panels'
dest.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
records=[]
for j,path in enumerate(sorted((evidence/'rgb').glob('*.png'))[::2]):
    rgb=np.asarray(Image.open(path).convert('RGB'))
    result=model.predict(rgb[:,:,::-1],conf=.25,device='cpu',verbose=False)[0]
    detections=[{'class':result.names[int(b.cls.item())],'confidence':float(b.conf.item()),'xyxy':b.xyxy[0].tolist()} for b in result.boxes]
    records.append({'frame':path.name,'detections':detections})
    annotated=result.plot()[:,:,::-1]
    depth=np.load(evidence/'depth'/f'{path.stem}.npy')
    depth_img=cv2.applyColorMap((np.clip(np.nan_to_num(depth,nan=10,posinf=10),0,10)/10*255).astype('uint8'),cv2.COLORMAP_TURBO)[:,:,::-1]
    depth_img[~np.isfinite(depth)]=0
    panel=Image.new('RGB',(1280,570),'#101c2d')
    panel.paste(Image.fromarray(annotated),(0,60));panel.paste(Image.fromarray(depth_img),(640,60))
    draw=ImageDraw.Draw(panel)
    draw.text((20,18),'RGB + YOLOv8m | actual recorded-frame inference',font=font,fill='white')
    draw.text((660,18),'DEPTH | metres to image plane',font=font,fill='white')
    draw.text((20,543),'Controlled scene / static person / threshold 0.25',font=font,fill='#adc3da')
    draw.text((660,543),'Blue: near 0 m   /   Red: 10 m   /   Black: invalid',font=font,fill='#adc3da')
    panel.save(dest/f'{j:05d}.png')
    if j==min(10,len(records)-1):panel.save(root/'media/perception_detail.png')
(root/'results/detections.json').write_text(json.dumps(records,indent=2))
print('Replay frames:',len(records),'person detections:',sum(any(d['class']=='person' for d in r['detections']) for r in records))
import subprocess
mp4=root/'media/perception_sensor.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','5','-i',str(dest/'%05d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(mp4)],check=True)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(mp4),'-filter_complex','fps=5,scale=1000:-1,split[a][b];[a]palettegen[p];[b][p]paletteuse','-loop','0',str(root/'media/perception_sensor.gif')],check=True)
