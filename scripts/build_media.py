"""Build explanatory figures and playable media from captured evidence."""
from pathlib import Path
import json
import subprocess
import shutil
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Rectangle,Circle
from matplotlib.font_manager import FontProperties

root=Path(__file__).resolve().parents[1]
evidence=root.parent/'evidence'
media=root/'media'
media.mkdir(exist_ok=True)
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams['font.family']=font.get_name()
plt.rcParams['axes.unicode_minus']=False
BG='#101c2d';FG='#eff5ff';SUB='#adc3da';BLUE='#58baff';GREEN='#60ddbb';GOLD='#ffcb65'
def canvas(title,subtitle):
    f,ax=plt.subplots(figsize=(16,9),facecolor=BG)
    ax.set_facecolor(BG);ax.set_xlim(0,16);ax.set_ylim(0,9);ax.axis('off')
    ax.text(.6,8.25,title,color=FG,size=25,weight='bold')
    ax.text(.6,7.65,subtitle,color=SUB,size=13)
    return f,ax
def box(ax,x,y,w,h,title,body,color=BLUE):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.12,rounding_size=.15',facecolor='#1b2d43',edgecolor=color,lw=1.8))
    ax.text(x+.2,y+h-.42,title,color=color,size=17,weight='bold')
    ax.text(x+.2,y+h-.88,body,color=FG,size=12,va='top',linespacing=1.6)
def arrow(ax,start,end,label=''):
    ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='-|>',color=SUB,lw=2))
    if label:ax.text((start[0]+end[0])/2,(start[1]+end[1])/2+.12,label,color=SUB,size=10,ha='center')
def save(f,name):
    f.savefig(media/name,dpi=130,bbox_inches='tight',facecolor=BG);plt.close(f)

f,ax=canvas('SPOT + ATS  |  이동하면서 관측하는 순찰 시스템','사족보행 플랫폼과 2축 관측 장치를 하나의 물리·통신 시간축으로 연결한다')
box(ax,.7,4.45,4.1,2.2,'01  이동 · Spot','4개 다리 × 3개 관절 = 12축\n학습 정책이 발 디딤과 자세를 제어한다\nNav2의 속도 명령을 실제 보행으로 바꾼다')
box(ax,5.9,4.45,4.1,2.2,'02  관측 · ATS','상하·좌우 2개 구동 관절\n다리와 독립적으로 시선을 조절한다\n관절 제한을 적용한 위치 목표를 사용한다',GOLD)
box(ax,11.1,4.45,4.1,2.2,'03  판단 · ROS 2','RGB·깊이·LiDAR·관절 상태\nYOLO 인식 / Nav2 경로 계획\nRViz에서 센서와 이동 경로를 확인한다',GREEN)
arrow(ax,(4.9,5.5),(5.75,5.5));arrow(ax,(10.1,5.5),(10.95,5.5))
box(ax,1,1.25,14,2,'왜 결합하는가','넓은 공간의 관찰 위치까지 이동하고, 필요한 방향을 관측하는 작업을 같은 시스템에서 다룬다.\n물리적 보행과 고수준 이동 계획을 분리하여 정책·센서·임무 알고리즘을 교체할 수 있도록 한다.',GREEN)
save(f,'overview_diagram.png')

f,ax=canvas('14개 구동 관절의 역할','기구 개념도 · 실제 모델의 관절 이름에 대응한다 · 축척을 나타내는 도면이 아니다')
ax.add_patch(FancyBboxPatch((5.5,3.1),5,2,boxstyle='round,pad=.1',fc=GOLD,ec=GOLD))
ax.text(8,4.15,'Spot body',ha='center',size=22,color=BG,weight='bold')
for x,y,name in [(5.8,3.1,'FL'),(9.9,3.1,'FR'),(5.8,5.1,'HL'),(9.9,5.1,'HR')]:
    sign=-1 if y<4 else 1
    points=[(x,y),(x-.55,y+sign*.5),(x+.1,y+sign*1.0),(x-.4,y+sign*1.45)]
    ax.plot(*zip(*points),color=BLUE,lw=8,solid_capstyle='round')
    for xx,yy in points[:3]:ax.add_patch(Circle((xx,yy),.11,fc=FG,zorder=3))
    ax.text(x+(.4 if x>8 else -1.3),y+sign*1.45,name,color=FG,size=15)
box(ax,.65,2.8,3.2,3.3,'각 다리 3축','hx : 옆으로 벌림\nhy : 앞뒤 고관절\nkn : 무릎 굽힘\n\n흰 점 : 구동 관절',BLUE)
box(ax,12.0,2.8,3.0,3.3,'ATS 2축','joint1 : 좌우 관측\njoint2 : 상하 관측\n\n상하 제한\n−1.57 ~ 0 rad',GOLD)
ax.add_patch(Rectangle((7.35,4.4),1.3,.55,fc='#375268',ec=FG));ax.add_patch(Circle((8,4.9),.35,fc=GREEN));ax.text(8,5.55,'ATS',color=GREEN,size=19,ha='center')
arrow(ax,(12,4.5),(8.5,4.9));ax.text(8,.7,'보행 정책 12축  +  독립 관측 제어 2축  =  총 14축',ha='center',color=FG,size=19)
save(f,'mechanism.png')

f,ax=canvas('ROS 2에서 무엇이 어디로 흐르는가','보행·인지·경로 계획을 토픽과 좌표계로 연결한다')
box(ax,.6,4.3,4.1,2.4,'Isaac Sim / Isaac Lab','물리 상태 → /odom · /tf · /clock\n센서 → /scan · /point_cloud\n영상 → /yolo/image_raw · /depth')
box(ax,5.8,4.3,4.0,2.4,'인지 · 계획','YOLO : 영상 속 객체 위치\nNav2 : 경로 → 속도 명령\nRViz : 상태와 센서의 의미를 확인',GREEN)
box(ax,10.9,4.3,4.5,2.4,'제어 · 물리 반영','/cmd_vel → 보행 정책 → 12축\n/ats_twist → 목표각 적분 → 2축\n제한·기울기 검사 후 다음 물리 스텝',GOLD)
arrow(ax,(4.8,5.5),(5.65,5.5));arrow(ax,(9.9,5.5),(10.75,5.5))
box(ax,1,1.3,14,1.8,'좌표계와 실행 환경','odom → body → 센서 프레임을 기준으로 데이터를 해석한다.\nIsaac Python 3.11과 ROS Python 3.10은 DDS로 통신한다. 예제 ROS_DOMAIN_ID는 91이다.',BLUE)
save(f,'ros_architecture.png')

f,ax=canvas('센서는 서로 다른 질문에 답한다','실행에 사용한 구현 범위와 관측 결과의 의미')
box(ax,.7,3.8,4.25,2.9,'RGB + YOLO','질문 : 무엇이 보이는가?\n출력 : 클래스·신뢰도·바운딩 박스\n검증 : 촬영 프레임에 실제 추론\n\n박스만으로 실제 거리는 알 수 없다',GREEN)
box(ax,5.8,3.8,4.25,2.9,'Depth','질문 : 각 픽셀까지 얼마나 먼가?\n출력 : 카메라 영상 평면 기준 깊이\n검증 : 색상 범위와 유효 픽셀 표시\n\n실제 센서 잡음 검증과는 구별한다',BLUE)
box(ax,10.9,3.8,4.25,2.9,'2D / 3D LiDAR','질문 : 주변 형상은 어디인가?\n2D : 360개 수평 광선\n3D : 16채널 / 수평 간격 2°\n\n등록된 상자·바닥의 해석적 교차',GOLD)
ax.text(.85,2.55,'선택한 LiDAR는 RTX 재질 반사 모델이 아니다.',color=FG,size=20)
ax.text(.85,1.8,'등록되지 않은 동적 객체의 회피와 센서 노이즈는 후속 검증 항목이다.',color=SUB,size=17)
save(f,'sensors.png')

for name in ('walk','ats','perception','ros'):
    src=evidence/name/'overview'
    frames=sorted(src.glob('*.png'))
    if len(frames)<2 or not (evidence/name/'telemetry.json').exists():continue
    mp4=media/f'{name}.mp4';gif=media/f'{name}.gif'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','10','-i',str(src/'%05d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart','-crf','22',str(mp4)],check=True)
    trim=['-ss','23'] if name=='ros' else []
    subprocess.run(['ffmpeg','-y','-loglevel','error',*trim,'-i',str(mp4),'-filter_complex','fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer','-loop','0',str(gif)],check=True)
    if name=='walk':shutil.copy2(frames[len(frames)//3],media/'hero.png')
    tele=evidence/name/'telemetry.json'
    if tele.exists():
        d=json.loads(tele.read_text())
        def finite(v):
            if isinstance(v,float) and not np.isfinite(v):return None
            if isinstance(v,list):return [finite(x) for x in v]
            if isinstance(v,dict):return {k:finite(x) for k,x in v.items()}
            return v
        (root/'results'/f'{name}.json').write_text(json.dumps(finite(d),indent=2,allow_nan=False))
print('Media generated:',len(list(media.iterdir())))
plans=root/'results/llm_plans.json'
if plans.exists():
    p=json.loads(plans.read_text())[1]
    frames=[]
    stages=[('자연어 명령',p['command']),('LLM 임무 분해','move_to (5, 5)  →  scan (person)  →  report_and_wait'),('실행 경계','계획 검증 → System-1 → Nav2 / ATS / 센서 → 관측 결과 보고')]
    for active in range(3):
        f,ax=canvas('Physical AI  |  언어를 물리적 행동 계획으로 바꾼다','실제 Gemini 응답 기록을 단계별로 재구성한 설명 화면이다. 전체 임무 완료 영상은 아니다.')
        for i,(title,body) in enumerate(stages):
            box(ax,.8,5.4-i*1.9,14.4,1.35,f'{i+1:02d}  {title}',body,GREEN if i==active else BLUE)
        ax.text(.9,.55,f"실제 모델: {p['model']}   |   응답 {p['latency_seconds']:.2f}초   |   규칙 fallback 없음",color=SUB,size=13)
        name=f'llm_step_{active}.png';save(f,name)
        frames.append(Image.open(media/name).convert('RGB').resize((1000,570)))
    frames[0].save(media/'llm_command.gif',save_all=True,append_images=frames[1:],duration=2200,loop=0)
    shutil.copy2(media/'llm_step_2.png',media/'physical_ai.png')
    for i in range(3):(media/f'llm_step_{i}.png').unlink()
for name in ('nav_ros','nav_ros_retry'):
    path=evidence/f'{name}.json'
    if path.exists():
        record=json.loads(path.read_text());record.pop('nodes',None)
        (root/'results'/f'{name}.json').write_text(json.dumps(record,indent=2))
for name in ('ats.gif','ats.mp4'):
    if not (evidence/'ats/telemetry.json').exists() and (media/name).exists():(media/name).unlink()
