"""Actual capture/lifecycle paths with invented replies in a disposable repository."""
from pathlib import Path
import importlib.util
import hashlib
import json
import subprocess
import sys
from tempfile import TemporaryDirectory
from tradingagents.research import runtime_hashes
from tradingagents.research.verify import verify_run

HERE=Path(__file__).resolve().parent
DRIVER='''from pathlib import Path
import json
from tradingagents.research import ResearchRun
import dex_source as source
SPEC=json.loads(Path('dex-source-spec.json').read_text())
def fake(url,payload):
    chain=next(c for c in SPEC['chains'] if c['url']==url)
    kind=payload['id'].split('-',1)[1]
    value={'chain':hex(chain['chain_id']),'finalized':{'number':hex(chain['historical_block']+100),'hash':'0x'+'ab'*32,'timestamp':hex(1700000100)},'pool':'0x'+'0'*24+'12'*20,'gas':'0x64','history_header':{'number':hex(chain['historical_block']),'hash':'0x'+'cd'*32,'timestamp':hex(1700000000)},'history_code':'0x6001600055'}[kind]
    return {'body':json.dumps({'jsonrpc':'2.0','id':payload['id'],'result':value}).encode(),'http_status':200,'headers':{},'error':None,'body_complete':True}
import subprocess
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
with ResearchRun.start(root=Path.cwd(),registration='gates.json',experiment='toy-dex-source',source=commit) as run:
    spec=json.loads(run.read_input('spec'))
    summary,_=source.capture(spec,fetch=fake,persist=run.write_json)
    run.write_json('source-summary.json',summary)
    run.finish([{'id':row['id'],'status':row['status']} for row in summary['cells']])
assert len(summary['cells'])==18 and summary['attempted_requests']==18
assert all(row['status']=='complete' for row in summary['cells'])
assert summary['implementation_admitted'] is False
'''


def main():
    loader=importlib.util.spec_from_file_location('dex_preflight_launcher',HERE/'dex_launcher.py')
    launcher=importlib.util.module_from_spec(loader);loader.loader.exec_module(launcher)
    with TemporaryDirectory(prefix='dex-source-synthetic-') as directory:
        root=Path(directory)
        for name in ('dex_source.py','dex_transport.py','dex-source-spec.json'):
            (root/name).write_bytes((HERE/name).read_bytes())
        (root/'driver.py').write_text(DRIVER)
        (root/'charter.md').write_text('Invented RPC replies only; no network, account or actual financial inputs.18toy cells.')
        sha=lambda n:hashlib.sha256((root/n).read_bytes()).hexdigest()
        spec=json.loads((root/'dex-source-spec.json').read_text())
        cells=[c['name']+'-'+k for c in spec['chains'] for k in spec['groups']]
        window={'dataset':'toy','start':'2000-01-01T00:00:00Z','end':'2000-01-02T00:00:00Z','availability':'existing'}
        gate={'schema_version':1,'program_id':'synthetic-only','families':{'toy':{'mechanism_id':'invented-dex-source','prior_attempts':0,'attempt_budget':1,'history_reference':'Invented disposable source test'}} ,'datasets':{'toy':{'identity':'invented-dex-source-spec','history_reference':'Authoredtoy','exposures':[{'start':window['start'],'end':window['end'],'state':'exposed'}]}},'experiments':{'toy-dex-source':{'family':'toy','parent':None,'question':'Can the real capture publish18invented source cells and all receipts?','charter':{'path':'charter.md','sha256':sha('charter.md')},'stage':'discovery','reuse':'exploratory','selection':None,'source_files':{n:sha(n) for n in ('driver.py','dex_source.py','dex_transport.py')},'runtime_hashes':runtime_hashes(),'windows':[window],'inputs':{'spec':{'path':'dex-source-spec.json','sha256':sha('dex-source-spec.json'),'dataset':'toy'}},'cells':cells,'outputs':[c+'-receipt.json' for c in cells]+['source-summary.json']}}}
        (root/'gates.json').write_text(json.dumps(gate,indent=2))
        def git(*args):
            return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE,text=True).strip()
        git('init','-q');git('add','.');git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','invented source preflight')
        # The launch function is unchanged; only this disposable driver substitutes replies.
        import os
        previous=Path.cwd()
        os.chdir(root)
        try:
            resource=launcher.launch([sys.executable,'-B',str(root/'driver.py')])
        finally:
            os.chdir(previous)
        assert resource['child_exit_code']==0 and resource['limit_reason'] is None, resource
        verified=verify_run(root/'research_runs/toy-dex-source')
        assert verified['cell_count']==18
        return {'synthetic_only':True,'no_external_requests':True,'disposable_repository_removed_after_return':True,'resource':resource,'verification':verified}


if __name__=='__main__':
    print(json.dumps(main(),indent=2))
