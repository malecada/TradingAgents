"""Maximum raw metadata fixtures in a disposable guarded research lifecycle."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
DIRECTORY=Path(__file__).resolve().parents[2]/"research/strategy-search-2026-09-11"

DRIVER = r'''
import hashlib,json,os,subprocess
from pathlib import Path
import bitrue_metadata as collector
from tradingagents.research import ResearchRun,runtime_hashes
root=Path(__file__).resolve().parent
assert len(os.sched_getaffinity(0))<=2
spec=json.loads((root/'bitrue-request-spec.json').read_text())
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def sha(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
git('init','-q')
(root/'charter.md').write_text('Synthetic source-only pipeline, no financial observations.')
ids=[r['id'] for r in spec['requests']]
outputs=[name+'-receipt.json' for name in ids]+['metadata-capture.json','metadata-admission.json']
registration={'schema_version':1,'program_id':'synthetic-bitrue','families':{'s':{'mechanism_id':'synthetic-bitrue-source','attempt_budget':1,'prior_attempts':0,'history_reference':'invented'}},'datasets':{'s':{'identity':'invented-triangle','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},'experiments':{'synthetic-bitrue':{'family':'s','parent':None,'charter':{'path':'charter.md','sha256':sha('charter.md')},'question':'Synthetic resource admission','stage':'development','reuse':'exploratory','windows':[{'dataset':'s','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],'inputs':{'request_spec':{'path':'bitrue-request-spec.json','sha256':sha('bitrue-request-spec.json'),'dataset':'s'}},'source_files':{n:sha(n) for n in ('driver.py','bitrue_metadata.py','options_metadata.py','carry_capture.py')},'runtime_hashes':runtime_hashes(),'selection':None,'cells':ids,'outputs':outputs}}}
(root/'registration.json').write_text(json.dumps(registration))
git('add','driver.py','bitrue_metadata.py','options_metadata.py','carry_capture.py','bitrue-request-spec.json','charter.md','registration.json')
git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','synthetic')
source=git('rev-parse','HEAD')
calls=[]
def fake(url):
    kind=spec['requests'][len(calls)]['kind'];calls.append(url)
    if kind=='contracts':data=[{'symbol':'E-BTC-USDT','multiplierCoin':'BTC','type':'E','side':1,'status':1,'multiplier':0.01,'minOrderVolume':1,'minOrderMoney':0.01}]
    else:data={}
    raw=json.dumps(data).encode();raw+=b' '*(spec['max_response_bytes']-len(raw))
    return {'body':raw,'http_status':200,'body_complete':True,'error':None,'headers':{}}
with ResearchRun.start(root=root,registration='registration.json',experiment='synthetic-bitrue',source=source) as run:
    raw,admission,cells=collector.capture(json.loads(run.read_input('request_spec')),fake,run.write_json)
    run.write_json('metadata-capture.json',raw);run.write_json('metadata-admission.json',admission);run.finish(cells)
directory=root/'research_runs/synthetic-bitrue/outputs'
actual=sum((directory/n).stat().st_size for n in outputs)
assert len(calls)==len(cells)==2 and all(c['status']=='complete' for c in cells)
assert raw['total_body_bytes']==10*1024**2 and actual<=40*1024**2
(root/'synthetic-result.json').write_text(json.dumps({'output_bytes':actual,'raw_bytes':raw['total_body_bytes'],'cpu_count':len(os.sched_getaffinity(0)),'cells':len(cells)}))
'''

def test_maximum_raw_bitrue_lifecycle(tmp_path):
    spec=importlib.util.spec_from_file_location('bitrue_guard',DIRECTORY/'resource_guard_v2.py')
    guard=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    for name in ('bitrue_metadata.py','options_metadata.py','carry_capture.py','bitrue-request-spec.json'):
        shutil.copyfile(DIRECTORY/name,tmp_path/name)
    (tmp_path/'driver.py').write_text(DRIVER)
    report=guard.run_guard([sys.executable,'-B',str(tmp_path/'driver.py')])
    (tmp_path/'guard-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120
    result=json.loads((tmp_path/'synthetic-result.json').read_text())
    assert result['cells']==2 and result['raw_bytes']==10*1024**2
    assert result['output_bytes']<=40*1024**2 and result['cpu_count']<=2
