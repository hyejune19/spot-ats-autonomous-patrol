"""Readable visual explanations using measured results and actual robot captures."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'media'
plt.rcParams['font.family']=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name()
plt.rcParams['axes.unicode_minus']=False
BG='#f5f3ed';INK='#172b38';MUTED='#536676';BLUE='#2266c3';TEAL='#007c73';ORANGE='#b65a13'
def page(kicker,title,subtitle):
    fig=plt.figure(figsize=(14,8),facecolor=BG)
    ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,14),ylim=(0,8));ax.axis('off');ax.set_zorder(2)
    ax.text(.65,7.45,kicker,color=TEAL,size=14,weight='bold')
    ax.text(.65,6.75,title,color=INK,size=29,weight='bold')
    ax.text(.65,6.18,subtitle,color=MUTED,size=15)
    return fig,ax
def txt(ax,x,y,s,size=20,color=INK,**kw):ax.text(x,y,s,size=size,color=color,**kw)
def card(ax,x,y,w,h,title,body,accent=TEAL):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.15,rounding_size=.15',fc='white',ec='#d6dedc',lw=1))
    ax.plot([x+.25,x+.25],[y+.3,y+h-.3],color=accent,lw=4)
    txt(ax,x+.5,y+h-.55,title,22,accent,weight='bold')
    txt(ax,x+.5,y+h-1.15,body,17,linespacing=1.65,va='top')
def arrow(ax,a,b):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='-|>',color=MUTED,lw=2))
def save(fig,name):fig.savefig(OUT/name,dpi=120,facecolor=BG);plt.close(fig)
def photo(fig,rect):
    ax=fig.add_axes(rect)
    ax.imshow(Image.open(OUT/'hero.png'));ax.set_xlim(410,875);ax.set_ylim(580,210);ax.axis('off')
    return ax

# A real robot photo anchors the introduction instead of a row of text boxes.
f,a=page('01 / ROBOT','Spot은 이동하고, ATS는 방향을 바꾼다','SPOT + Auto Targeting System · 실제 시뮬레이션 모델')
photo(f,[.03,.16,.56,.55])
card(a,8.25,3.5,4.8,1.75,'ATS · 2축','상부 기구의 좌우·상하 회전',ORANGE)
card(a,8.25,1.15,4.8,1.75,'Spot · 12축','네 다리로 이동과 자세를 제어',BLUE)
txt(a,.7,.48,'역할을 나누고, 하나의 물리 시뮬레이션에서 실행한다.',18)
save(f,'overview_diagram.png')

f,a=page('02 / MECHANISM','어디가 움직이는가','실제 모델의 관절 구성 · 사진은 구조 설명용이며 치수 도면이 아니다')
photo(f,[.34,.18,.32,.49])
card(a,.65,3.15,3.7,2.0,'ATS 2축','joint1 : 좌우 회전\njoint2 : 상하 회전',ORANGE)
card(a,9.55,1.9,3.75,2.9,'각 다리 3축','고관절 옆 벌림\n고관절 앞뒤 회전\n무릎 굽힘',BLUE)
arrow(a,(4.45,4.05),(6.35,4.55));arrow(a,(9.45,3.0),(7.75,2.1))
txt(a,.8,1.65,'12 + 2 = 14',35,TEAL,weight='bold')
txt(a,.8,1.12,'총 구동 관절 수',18,MUTED)
txt(a,.75,.42,'상하 관절 제한 −1.57 ~ 0 rad  ·  보행 정책은 다리 12축만 제어한다.',16,MUTED)
save(f,'mechanism.png')

plans=json.loads((ROOT/'results/llm_plans.json').read_text())
record=plans[1];animation=[]
for selected in range(3):
    f,a=page('03 / PHYSICAL AI','한 문장의 명령이 세 단계의 계획이 된다','실제 Gemini 응답을 재구성한 설명이다. 연속 임무 완료 영상은 아니다.')
    a.add_patch(FancyBboxPatch((.8,4.85),12.4,.8,boxstyle='round,pad=.15',fc=INK,ec=INK))
    txt(a,1.1,5.1,'“A구역에 가서 사람이 있는지 확인하고 보고해.”',23,'white')
    steps=[('01  이동','A구역 (5, 5)로 이동','move_to'),('02  탐색','사람이 보이는지 관측','scan · person'),('03  보고','결과를 전달하고 대기','report_and_wait')]
    for i,(title,body,code) in enumerate(steps):
        x=.8+i*4.3
        card(a,x,1.85,3.75,2.2,title,body,TEAL if i==selected else MUTED)
        txt(a,x+.5,2.15,code,14,MUTED)
        if i<2:arrow(a,(x+3.92,2.95),(x+4.1,2.95))
    txt(a,.9,.98,f"{record['model']}  ·  실제 응답 {record['latency_seconds']:.2f}초  ·  규칙 대체 없음",16,MUTED)
    txt(a,.9,.48,'LLM은 임무를 계획한다. 경로와 관절 동작은 실행 계층이 담당한다.',18,INK)
    tmp=OUT/f'_llm_{selected}.png';save(f,tmp.name)
    animation.append(Image.open(tmp).convert('RGB').resize((1120,640)))
    if selected==2:Image.open(tmp).save(OUT/'physical_ai.png')
    tmp.unlink()
animation[0].save(OUT/'llm_command.gif',save_all=True,append_images=animation[1:],duration=2000,loop=0)

f,a=page('04 / CONNECTION','명령은 내려가고, 관측 결과는 돌아온다','언어 → 계획 → 행동 → 센서 피드백의 연결 구조')
card(a,.8,3.5,3.5,2.05,'의도 해석','자연어 → 실행 단계\nLLM / System-2',TEAL)
card(a,5.1,3.5,3.5,2.05,'행동 실행','경로 → 속도 → 관절\nNav2 / 보행 / ATS',BLUE)
card(a,9.4,3.5,3.5,2.05,'물리 세계','이동과 주변 관측\nIsaac Sim',ORANGE)
arrow(a,(4.5,4.5),(4.9,4.5));arrow(a,(8.8,4.5),(9.2,4.5))
a.plot([11.1,11.1,2.5,2.5],[3.25,2.4,2.4,3.25],color=TEAL,lw=2)
arrow(a,(2.5,3.0),(2.5,3.35))
txt(a,4.55,2.62,'위치 · 영상 · 거리 · 실행 상태',20,TEAL)
txt(a,.85,1.28,'ROS 2가 전달한다',21,INK,weight='bold')
txt(a,.85,.68,'/cmd_vel   /ats_twist     |     /odom   /scan   /point_cloud   /depth',16,MUTED)
save(f,'ros_architecture.png')

f,a=page('05 / PERCEPTION','무엇인가? 얼마나 먼가? 어디가 막혔는가?','센서마다 답하는 질문이 다르다')
titles=[('RGB + YOLO','무엇이 보이는가','사람 · 물체의 종류',TEAL),('깊이 영상','얼마나 떨어져 있는가','픽셀별 깊이',BLUE),('LiDAR','주변 형상은 어디인가','거리 · 장애물 배치',ORANGE)]
for i,(title,question,answer,color) in enumerate(titles):
    x=.85+4.3*i
    txt(a,x,5.2,title,25,color,weight='bold');txt(a,x,4.55,question,19);txt(a,x,3.95,answer,17,MUTED)
    a.plot([x,x+3.6],[3.6,3.6],color=color,lw=3)
detail=Image.open(OUT/'perception_detail.png')
for bounds,rect in [((0,60,640,540),[.06,.15,.255,.27]),((640,60,1280,540),[.365,.15,.255,.27])]:
    pane=f.add_axes(rect);pane.imshow(detail);pane.set_xlim(bounds[0],bounds[2]);pane.set_ylim(bounds[3],bounds[1]);pane.axis('off')
txt(a,9.6,2.8,'360° / 2D',27,ORANGE,weight='bold')
txt(a,9.6,2.05,'16채널 / 3D',25,ORANGE,weight='bold')
txt(a,9.6,1.4,'등록된 상자·바닥과\n광선의 교차 계산',16,MUTED,linespacing=1.5)
txt(a,.85,.42,'실제 촬영 + 실제 영상 추론   |   LiDAR는 해석적 모델이며 RTX 반사 센서가 아니다.',15,MUTED)
save(f,'sensors.png')
print('Updated five explanations and the LLM animation')
