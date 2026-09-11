"""Maximum raw-size invented inputs through the actual guarded proxy CLI lifecycle."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

DIRECTORY = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11"

DRIVER = r'''
import hashlib,json,os,subprocess
from pathlib import Path
import triangle_capture as collector
from tradingagents.research import ResearchRun,runtime_hashes
root=Path(__file__).resolve().parent
assert len(os.sched_getaffinity(0))<=2
spec=json.loads((root/'triangle-request-spec.json').read_text())
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def sha(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
import sys
import triangle_proxy_run as proxy_runner
from options_metadata import lifecycle_bytes
calls=[]
def fake(url):
    kind=spec['requests'][len(calls)]['kind'];calls.append(url)
    if kind=='exchange-info':data={'symbols':[{'symbol':s,'baseAsset':p[0],'quoteAsset':p[1],'status':'TRADING','isSpotTradingAllowed':True,'filters':[]} for s,p in collector.PAIRS.items()]}
    elif kind=='server-time':data={'serverTime':1800000000000}
    elif kind=='book-ticker':data=[{'symbol':s,'bidPrice':'100','askPrice':'101','bidQty':'2','askQty':'3'} for s in collector.PAIRS]
    else:data={'lastUpdateId':0,'bids':[['100','2']],'asks':[['101','3']]}
    raw=json.dumps(data).encode();raw+=b' '*(spec['max_response_bytes']-len(raw))
    return {'body':raw,'http_status':200,'body_complete':True,'error':None,'headers':{}}

raw,admission,source_cells=collector.capture(spec,fake)
assert raw['total_body_bytes']==30*1024**2 and all(c['status']=='complete' for c in source_cells)
(root/'capture.json').write_bytes(lifecycle_bytes(raw))
(root/'admission.json').write_bytes(lifecycle_bytes(admission))
del raw,admission
git('init','-q')
(root/'charter.md').write_text('Synthetic source-only pipeline, no financial observations.')
ids=list(proxy_runner.triangle_bound.evaluate({})['cases'])
outputs=['proxy.json']
registration={'schema_version':1,'program_id':'synthetic-triangle','families':{'s':{'mechanism_id':'synthetic-triangle-source','attempt_budget':1,'prior_attempts':0,'history_reference':'invented'}},'datasets':{'s':{'identity':'invented-triangle','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},'experiments':{'synthetic-triangle':{'family':'s','parent':None,'charter':{'path':'charter.md','sha256':sha('charter.md')},'question':'Synthetic resource admission','stage':'development','reuse':'exploratory','windows':[{'dataset':'s','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],'inputs':{name:{'path':name+'.json','sha256':sha(name+'.json'),'dataset':'s'} for name in ('capture','admission')},'source_files':{n:sha(n) for n in ('driver.py','triangle_capture.py','options_metadata.py','carry_capture.py','triangle_bound.py','triangle_proxy_run.py')},'runtime_hashes':runtime_hashes(),'selection':None,'cells':ids,'outputs':outputs}}}
(root/'registration.json').write_text(json.dumps(registration))
git('add','.')
git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','synthetic')
source=git('rev-parse','HEAD')

proxy_runner.REGISTRATION='registration.json'
proxy_runner.EXPERIMENT='synthetic-triangle'
# main resolves root from its module path; synthetic copy keeps a nested layout.
proxy_runner.__file__=str(root/'research/fixture/triangle_proxy_run.py')
sys.argv=['triangle_proxy_run.py','--source',source]
proxy_runner.main()
directory=root/'research_runs/synthetic-triangle/outputs'
actual=(directory/'proxy.json').stat().st_size
output=json.loads((directory/'proxy.json').read_text())
assert len(output['cells'])==8 and all(c['status']=='complete' for c in output['cells'])
assert actual<=2*1024**2
(root/'synthetic-result.json').write_text(json.dumps({'output_bytes':actual,'raw_bytes':30*1024**2,'cpu_count':len(os.sched_getaffinity(0)),'cells':8,'source_sha256':{n:sha(n) for n in ('triangle_proxy_run.py','triangle_bound.py','triangle_capture.py','options_metadata.py','carry_capture.py')}}))
'''

def test_maximum_raw_proxy_lifecycle_under_guard(tmp_path):
    spec=importlib.util.spec_from_file_location("proxy_guard",DIRECTORY/"resource_guard_v2.py")
    guard=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    for name in ("triangle_capture.py","options_metadata.py","carry_capture.py","triangle_bound.py","triangle_proxy_run.py","triangle-request-spec.json"):
        shutil.copyfile(DIRECTORY/name,tmp_path/name)
    (tmp_path/"driver.py").write_text(DRIVER)
    report=guard.run_guard([sys.executable,"-B",str(tmp_path/"driver.py")])
    (tmp_path/"guard-report.json").write_text(json.dumps(report,indent=2)+"\n")
    assert report["child_exit_code"]==0 and report["limit_reason"] is None,report
    assert report["rss_limit_bytes"]==512*1024**2 and report["wall_limit_seconds"]==120
    result=json.loads((tmp_path/"synthetic-result.json").read_text())
    assert result["cells"]==8 and result["raw_bytes"]==30*1024**2
    assert result["output_bytes"]<=2*1024**2 and result["cpu_count"]<=2
