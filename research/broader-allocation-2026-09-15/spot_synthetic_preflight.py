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
DRIVER="from pathlib import Path\nimport json,subprocess\nfrom tradingagents.research import ResearchRun\nimport spot_source as source\nSPEC=json.loads(Path('spot-source-spec.json').read_text())\ndef payloads():\n    rows=[]\n    for symbol,base in [('BTCUSDC','BTC'),('ETHUSDC','ETH')]:\n        rows.append({'symbol':symbol,'baseAsset':base,'quoteAsset':'USDC','status':'TRADING','isSpotTradingAllowed':True,'filters':[\n            {'filterType':'LOT_SIZE','minQty':'0.001','maxQty':'100','stepSize':'0.001'},\n            {'filterType':'PRICE_FILTER','minPrice':'0','maxPrice':'0','tickSize':'0.01'},\n            {'filterType':'NOTIONAL','minNotional':'5','maxNotional':'100000'},\n            {'filterType':'UNKNOWN_NEW_FILTER','note':'retained but not implemented'}]})\n    return {'clock':{'serverTime':1700000000000},'symbols':{'symbols':rows},\n        'btc_depth':{'lastUpdateId':1,'bids':[['99','2'],['98','4']],'asks':[['101','2'],['102','4']]},\n        'eth_depth':{'lastUpdateId':2,'bids':[['9','20']],'asks':[['11','20']]}}\ndef fake(url):\n    kind=next(r['id'] for r in SPEC['requests'] if r['url']==url)\n    return dict(body=json.dumps(payloads()[kind]).encode(),http_status=200,headers={},error=None,body_complete=True)\ncommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()\nwith ResearchRun.start(root=Path.cwd(),registration='gates.json',experiment='toy-spot-source',source=commit) as run:\n    spec=json.loads(run.read_input('spec'))\n    summary,_=source.capture(spec,fetch=fake,persist=run.write_json)\n    run.write_json('source-summary.json',summary)\n    run.finish([{'id':r['id'],'status':r['status']} for r in summary['cells']])\nassert len(summary['cells'])==4 and summary['attempted_requests']==4\nassert all(r['status']=='complete' for r in summary['cells'])\nassert not summary['implementation_admitted']\n"


def main():
    loader=importlib.util.spec_from_file_location('dex_preflight_launcher',HERE.parent/'strategy-search-2026-09-11/resource_guard_v2.py')
    launcher=importlib.util.module_from_spec(loader);loader.loader.exec_module(launcher)
    with TemporaryDirectory(prefix='dex-source-synthetic-') as directory:
        root=Path(directory)
        for name in ('spot_source.py','spot_transport.py','spot-source-spec.json','dex_source.py','dex_transport.py'):
            (root/name).write_bytes((HERE/name).read_bytes())
        (root/'driver.py').write_text(DRIVER)
        (root/'charter.md').write_text('Invented RPC replies only; no network, account or actual financial inputs.4toy cells.')
        sha=lambda n:hashlib.sha256((root/n).read_bytes()).hexdigest()
        spec=json.loads((root/'spot-source-spec.json').read_text())
        cells=[r['id'] for r in spec['requests']]
        window={'dataset':'toy','start':'2000-01-01T00:00:00Z','end':'2000-01-02T00:00:00Z','availability':'existing'}
        gate={'schema_version':1,'program_id':'synthetic-only','families':{'toy':{'mechanism_id':'invented-spot-source','prior_attempts':0,'attempt_budget':1,'history_reference':'Invented disposable source test'}} ,'datasets':{'toy':{'identity':'invented-spot-source-spec','history_reference':'Authoredtoy','exposures':[{'start':window['start'],'end':window['end'],'state':'exposed'}]}},'experiments':{'toy-spot-source':{'family':'toy','parent':None,'question':'Can the real capture publish4invented source cells and all receipts?','charter':{'path':'charter.md','sha256':sha('charter.md')},'stage':'discovery','reuse':'exploratory','selection':None,'source_files':{n:sha(n) for n in ('driver.py','spot_source.py','spot_transport.py','dex_source.py','dex_transport.py')},'runtime_hashes':runtime_hashes(),'windows':[window],'inputs':{'spec':{'path':'spot-source-spec.json','sha256':sha('spot-source-spec.json'),'dataset':'toy'}},'cells':cells,'outputs':[c+'-receipt.json' for c in cells]+['source-summary.json']}}}
        (root/'gates.json').write_text(json.dumps(gate,indent=2))
        def git(*args):
            return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE,text=True).strip()
        git('init','-q');git('add','.');git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','invented source preflight')
        # The launch function is unchanged; only this disposable driver substitutes replies.
        import os
        previous=Path.cwd()
        os.chdir(root)
        try:
            resource=launcher.run_guard([sys.executable,'-B',str(root/'driver.py')])
        finally:
            os.chdir(previous)
        assert resource['child_exit_code']==0 and resource['limit_reason'] is None, resource
        verified=verify_run(root/'research_runs/toy-spot-source')
        assert verified['cell_count']==4
        return {'synthetic_only':True,'no_external_requests':True,'disposable_repository_removed_after_return':True,'resource':resource,'verification':verified}


if __name__=='__main__':
    print(json.dumps(main(),indent=2))
