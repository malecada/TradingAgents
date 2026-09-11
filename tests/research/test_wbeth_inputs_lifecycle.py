"""Maximum raw metadata fixtures in a disposable guarded research lifecycle."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import pytest
DIRECTORY=Path(__file__).resolve().parents[2]/"research/strategy-search-2026-09-11"

DRIVER = r'''
import hashlib,json,os,subprocess,sys
from pathlib import Path
import wbeth_inputs as collector
from tradingagents.research import ResearchRun,runtime_hashes
root=Path(__file__).resolve().parent
mode=sys.argv[1]
assert len(os.sched_getaffinity(0))<=2
spec=json.loads((root/'wbeth-request-spec.json').read_text())
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def sha(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
git('init','-q')
(root/'charter.md').write_text('Synthetic source-only pipeline, no financial observations.')
ids=[r['id'] for r in spec['requests']]
outputs=[name+'-receipt.json' for name in ids]+['wbeth-capture.json','wbeth-admission.json']
registration={'schema_version':1,'program_id':'synthetic-wbeth','families':{'s':{'mechanism_id':'synthetic-wbeth-source','attempt_budget':1,'prior_attempts':0,'history_reference':'invented'}},'datasets':{'s':{'identity':'invented-triangle','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},'experiments':{'synthetic-wbeth':{'family':'s','parent':None,'charter':{'path':'charter.md','sha256':sha('charter.md')},'question':'Synthetic resource admission','stage':'development','reuse':'exploratory','windows':[{'dataset':'s','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],'inputs':{'request_spec':{'path':'wbeth-request-spec.json','sha256':sha('wbeth-request-spec.json'),'dataset':'s'}},'source_files':{n:sha(n) for n in ('driver.py','wbeth_inputs.py','options_metadata.py','carry_capture.py')},'runtime_hashes':runtime_hashes(),'selection':None,'cells':ids,'outputs':outputs}}}
(root/'registration.json').write_text(json.dumps(registration))
git('add','driver.py','wbeth_inputs.py','options_metadata.py','carry_capture.py','wbeth-request-spec.json','charter.md','registration.json')
git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','synthetic')
source=git('rev-parse','HEAD')
calls=[]
def fake(url):
    kind=spec['requests'][len(calls)]['kind'];calls.append(url)
    if kind=='exchange-info':
        data={'symbols':[{'symbol':'WBETHUSDT','baseAsset':'WBETH','quoteAsset':'USDT','status':'TRADING','isSpotTradingAllowed':True,'filters':[{'filterType':'LOT_SIZE','stepSize':'0.0001'}],'opaque':''}]}
        plain=json.dumps(data).encode();data['symbols'][0]['opaque']='x'*(spec['max_response_bytes']-len(plain))
        if mode=='expansion': data['symbols'][0]['opaque']=[0]*1000000
    else:
        data=[[collector.START_MS+i*collector.DAY_MS,'100','102','99','101','5',collector.START_MS+(i+1)*collector.DAY_MS-1,'500',2,'2','200',''] for i in range(91)]
        plain=json.dumps(data).encode();data[0][11]='x'*(spec['max_response_bytes']-len(plain))
    raw=json.dumps(data).encode();raw+=b' '*(spec['max_response_bytes']-len(raw));assert len(raw)==spec['max_response_bytes']
    return {'body':raw,'http_status':200,'body_complete':True,'error':None,'headers':{}}
with ResearchRun.start(root=root,registration='registration.json',experiment='synthetic-wbeth',source=source) as run:
    raw,admission,cells=collector.capture(json.loads(run.read_input('request_spec')),fake,run.write_json)
    run.write_json('wbeth-capture.json',raw);run.write_json('wbeth-admission.json',admission);run.finish(cells)
directory=root/'research_runs/synthetic-wbeth/outputs'
actual=sum((directory/n).stat().st_size for n in outputs)
assert len(calls)==len(cells)==2
assert [c['status'] for c in cells]==(['complete','complete'] if mode=='structured' else ['unavailable','complete'])
assert raw['total_body_bytes']==10*1024**2 and actual<=40*1024**2
(root/'synthetic-result.json').write_text(json.dumps({'output_bytes':actual,'raw_bytes':raw['total_body_bytes'],'cpu_count':len(os.sched_getaffinity(0)),'cells':len(cells),'cell_statuses':[c['status'] for c in cells],'mode':mode}))
'''

@pytest.mark.parametrize('mode',['structured','expansion'])
def test_maximum_raw_wbeth_lifecycle(tmp_path,mode):
    spec=importlib.util.spec_from_file_location('wbeth_guard',DIRECTORY/'resource_guard_v2.py')
    guard=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    for name in ('wbeth_inputs.py','options_metadata.py','carry_capture.py','wbeth-request-spec.json'):
        shutil.copyfile(DIRECTORY/name,tmp_path/name)
    (tmp_path/'driver.py').write_text(DRIVER)
    report=guard.run_guard([sys.executable,'-B',str(tmp_path/'driver.py'),mode])
    (tmp_path/'guard-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120
    result=json.loads((tmp_path/'synthetic-result.json').read_text())
    assert result['cells']==2 and result['raw_bytes']==10*1024**2
    assert result['output_bytes']<=40*1024**2 and result['cpu_count']<=2
