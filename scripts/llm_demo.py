"""Use the configured local planner; publish only response and nonsecret metadata."""
from pathlib import Path
import os
import sys
import json
import shlex
import time
import contextlib
import io
root=Path(__file__).resolve().parents[1]
workspace=Path(os.environ['SPOTATS_WORKSPACE'])
allowed={'ATS_LLM_PROVIDER','GEMINI_API_KEY','GEMINI_MODEL','GEMINI_BASE_URL','OPENAI_API_KEY','OPENAI_MODEL','OPENAI_BASE_URL','OLLAMA_MODEL','OLLAMA_URL'}
config=workspace/'.runtime/llm.env'
if config.exists():
    for line in config.read_text().splitlines():
        line=line.strip().removeprefix('export ')
        if not line or line.startswith('#') or '=' not in line:continue
        k,v=line.split('=',1)
        if k in allowed:
            parts=shlex.split(v,comments=True)
            if len(parts)==1:os.environ[k]=parts[0]
provider=os.environ.get('ATS_LLM_PROVIDER','rules')
if provider=='rules':
    print('Configured provider is rules; no LLM claim or silent fallback')
    raise SystemExit(2)
os.environ['ATS_LLM_FALLBACK']='error'
os.environ['ATS_LLM_TIMEOUT']='40'
sys.path.insert(0,str(workspace/'phyAI_ws/src/ats_system2'))
from ats_system2.llm_planner import build_plan_dict
commands=[
    '현재 odom 좌표 기준 x=2.0m, y=0.5m 위치로 이동한 다음 결과를 보고하고 기다려.',
    'A구역에 가서 주변에 사람이 있는지 확인하고 관측 결과를 보고해.',
]
records=[]
for command in commands:
    start=time.monotonic()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            plan=build_plan_dict(command,None,{'purpose':'simulation demonstration','robot':'Spot ATS','current_pose':{'x':0.0,'y':0.0}})
    except Exception as exc:
        # Never publish arbitrary provider exception bodies or credential URLs.
        print('Planner failed:',type(exc).__name__)
        raise SystemExit(1)
    records.append({'command':command,'provider':provider,'model':os.environ.get({'gemini':'GEMINI_MODEL','openai':'OPENAI_MODEL','ollama':'OLLAMA_MODEL'}.get(provider,''),'provider default'),'latency_seconds':time.monotonic()-start,'fallback':False,'plan':plan})
(root/'results/llm_plans.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print(json.dumps({'provider':provider,'models':[r['model'] for r in records],'tasks':[[s['task'] for s in r['plan']['steps']] for r in records]},ensure_ascii=False))
