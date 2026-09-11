"""Full invented metadata/cash/exposure pipeline, no network or real data."""
import base64
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

import pytest
DIRECTORY=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
for name in ('options_metadata','carry_capture','wbeth_inputs','wbeth_book','carry_statistics','wbeth_book_run'):
    loader=importlib.util.spec_from_file_location(name,DIRECTORY/(name+'.py'))
    loaded=importlib.util.module_from_spec(loader);sys.modules[name]=loaded;loader.loader.exec_module(loaded)
runner=sys.modules['wbeth_book_run']


def bars(asset):
    rows=[]
    for i in range(91):
        price=100+2*math.sin(i*.31) if asset=='BTC' else 100+3*math.cos(i*.19)
        if asset=='WBETH':price*=2*(1+.04*i/90)
        stamp=runner.carry_source.START_MS+i*runner.carry_source.DAY_MS
        rows.append([stamp,price,price,price,price,1,stamp+runner.carry_source.DAY_MS-1,100,1,.5,50,0])
    return rows


def response(data):
    return {'body':json.dumps(data).encode(),'http_status':200,'body_complete':True,'error':None,'headers':{}}


def synthetic_sources():
    wb_spec=json.loads((DIRECTORY/'wbeth-request-spec.json').read_text())
    def wb_fake(url):
        if 'exchangeInfo' in url:
            return response({'symbols':[{'symbol':'WBETHUSDT','baseAsset':'WBETH','quoteAsset':'USDT','status':'TRADING','isSpotTradingAllowed':True,'filters':[{'filterType':'LOT_SIZE','stepSize':'0.0001'}]}]})
        return response(bars('WBETH'))
    wraw,wadmission,_=runner.wbeth_source.capture(wb_spec,wb_fake)
    spec=runner.carry_source.frozen_request_spec();counter=iter(spec['requests'])
    def carry_fake(url):
        req=next(counter);kind=req['kind'];asset=req['parameters'].get('symbol','ETHUSDT')[:-4]
        if kind in ('spot','perp','mark'):return response(bars(asset))
        if kind=='funding':
            return response([{'symbol':asset+'USDT','fundingTime':runner.carry_source.START_MS+i*runner.carry_source.DAY_MS//3,'fundingRate':.0001,'markPrice':100} for i in range(273)])
        if kind=='server-time':return response({'serverTime':int(time.time()*1000)})
        return response({'symbols':[{'symbol':symbol,'contractType':'PERPETUAL','quoteAsset':'USDT','marginAsset':'USDT','status':'TRADING'} for symbol in ('BTCUSDT','ETHUSDT')]})
    craw,cadmission,_=runner.carry_source.capture(spec,carry_fake)
    return wraw,wadmission,craw,cadmission


def row(envelope,identity):return next(item for item in envelope['requests'] if item['id']==identity)
def admitted(envelope,identity):return next(item for item in envelope['cells'] if item['id']==identity)


def test_full_source_pipeline_real_hac_and_paired_quantities():
    books,summary,cells=runner.evaluate(*synthetic_sources())
    assert len(cells)==len(books['cases'])==8 and all(cell['status']=='complete' for cell in cells)
    assert len(books['source_availability'])==12 and all(value['status']=='complete' for value in books['source_availability'].values())
    for case in summary['cases']:
        assert case['statistics']['market_exposure']['status']=='complete'
        assert case['statistics']['market_exposure']['observations']==91
        assert case['statistics']['expected_return_confidence']['status']==case['statistics']['power']['status']=='unavailable'
        assert case['realized_net_base_delta_at_most_1pct_nav']['status']=='unavailable'
        assert case['graduation'] is False
    for capital in (1000,10000):
        for scenario in ('base','stress'):
            observed=books['cases'][runner.case_id(capital,scenario,False)]
            zero=books['cases'][runner.case_id(capital,scenario,True)]
            assert observed['initial']==zero['initial']
            assert observed['metrics']['cash_profit']-zero['metrics']['cash_profit']==pytest.approx(observed['metrics']['funding_cash'])
    assert len(runner.lifecycle_bytes(books))+len(runner.lifecycle_bytes(summary))<=runner.MAX_OUTPUT_BYTES


@pytest.mark.parametrize('failure',['wb_norm','wb_hash','eth_coverage','eth_parent','typed_flag','request_identity','spec'])
def test_required_source_failures_keep_eight_unavailable(failure):
    values=list(synthetic_sources())
    if failure=='wb_norm':admitted(values[1],'wbeth-spot')['observations']=90
    elif failure=='wb_hash':row(values[0],'wbeth-spot')['body_sha256']='0'*64
    elif failure=='eth_coverage':admitted(values[3],'eth-funding')['coverage']['observed_events']=272
    elif failure=='eth_parent':admitted(values[3],'eth-perp')['status']='unavailable'
    elif failure=='typed_flag':row(values[2],'eth-mark')['body_complete']=1
    elif failure=='request_identity':row(values[2],'eth-spot')['request_url']='https://invalid.invalid/'
    else:values[2]['request_spec']['requests'][0]['parameters']['limit']=999
    books,summary,cells=runner.evaluate(*values)
    assert len(cells)==8 and all(cell['status']=='unavailable' for cell in cells)
    assert len(books['source_availability'])==12
    assert summary['graduation'] is False


def test_btc_spot_unavailable_retains_cash_but_not_beta():
    values=list(synthetic_sources());row(values[2],'btc-spot')['body_sha256']='0'*64
    _,summary,cells=runner.evaluate(*values)
    assert all(cell['status']=='complete' for cell in cells)
    assert all(case['statistics']['market_exposure']['status']=='unavailable' for case in summary['cases'])
    assert all(case['necessary_historical_screens']['beta']['passes'] is None for case in summary['cases'])


@pytest.mark.parametrize('identity',['btc-funding','btc-perp','btc-mark','exchange-info','server-time'])
def test_unrelated_source_failure_remains_explicit_without_price_substitution(identity):
    values=list(synthetic_sources());admitted(values[3],identity)['invented']=True
    books,summary,cells=runner.evaluate(*values)
    assert all(cell['status']=='complete' for cell in cells)
    assert books['source_availability'][identity]['status']=='unavailable'
    assert all(case['statistics']['market_exposure']['status']=='complete' for case in summary['cases'])


def test_duplicate_raw_json_field_cannot_hide_behind_matching_parent():
    values=list(synthetic_sources());record=row(values[2],'eth-funding')
    raw=base64.b64decode(record['body_base64']).replace(b'"fundingRate": 0.0001',b'"fundingRate": 1, "fundingRate": 0.0001',1)
    record.update(body_base64=base64.b64encode(raw).decode(),body_bytes=len(raw),body_sha256=hashlib.sha256(raw).hexdigest())
    _,_,cells=runner.evaluate(*values)
    assert all(cell['status']=='unavailable' for cell in cells)


def test_benchmark_first_return_uses_first_open():
    values=bars('BTC');values[0][1]=50
    returns=runner.returns(values)
    assert returns[0]==pytest.approx(values[0][4]/50-1)
    assert returns[1]==pytest.approx(values[1][4]/values[0][4]-1)


def test_actual_combined_output_cap_before_any_write(monkeypatch):
    values=synthetic_sources();names=('wbeth_capture','wbeth_admission','carry_capture','carry_admission');saved=dict(zip(names,values))
    writes=[]
    class Fake:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read_input(self,name):return json.dumps(saved[name]).encode()
        def write_json(self,*args):writes.append(args)
        def finish(self,*args):pytest.fail('oversized output cannot finish')
    monkeypatch.setattr(runner.ResearchRun,'start',lambda **kwargs:Fake())
    monkeypatch.setattr(sys,'argv',['wbeth_book_run.py','--source','synthetic'])
    monkeypatch.setattr(runner,'evaluate',lambda *_:({'x':'x'*(11*1024**2)},{'x':'x'*(11*1024**2)},[]))
    with pytest.raises(ValueError,match='20MiB'):runner.main()
    assert writes==[]


LIFECYCLE_DRIVER=r'''
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
program=root/'research/strategy-search-2026-09-11'
sys.path.insert(0,str(root));sys.path.insert(0,str(program))
loader=importlib.util.spec_from_file_location('synthetic_fixture',root/'tests/research/test_wbeth_book_run.py')
fixture=importlib.util.module_from_spec(loader);loader.loader.exec_module(fixture)
from tradingagents.research import runtime_hashes
from tradingagents.research.verify import verify_run
sources=fixture.synthetic_sources()
for name,value in zip(('wbeth_capture','wbeth_admission','carry_capture','carry_admission'),sources):
    (root/(name+'.json')).write_text(json.dumps(value))
del sources
def sha(path):return hashlib.sha256((root/path).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
git('init','-q')
(root/'charter.md').write_text('Invented fixed WBETH quantity, cash and exposure lifecycle. No market observations.')
source_files={str(path.relative_to(root)):sha(path.relative_to(root)) for path in program.glob('*.py')}
source_files['driver.py']=sha('driver.py')
exp={'family':'synthetic','parent':None,'charter':{'path':'charter.md','sha256':sha('charter.md')},'question':'invented fixed WBETH lifecycle',
     'stage':'development','reuse':'exploratory','windows':[{'dataset':'synthetic','start':'2026-04-01T00:00:00Z','end':'2026-07-01T00:00:00Z','availability':'existing'}],
     'inputs':{name:{'path':name+'.json','sha256':sha(name+'.json'),'dataset':'synthetic'} for name in ('wbeth_capture','wbeth_admission','carry_capture','carry_admission')},
     'source_files':source_files,'runtime_hashes':runtime_hashes(),'selection':None,
     'cells':[fixture.runner.case_id(*case) for case in fixture.runner.CASES],'outputs':['books.json','summary.json']}
spec={'schema_version':1,'program_id':'synthetic-wbeth','families':{'synthetic':{'mechanism_id':'synthetic','attempt_budget':1,'prior_attempts':0,'history_reference':'invented'}},
      'datasets':{'synthetic':{'identity':'invented-wbeth','history_reference':'invented','exposures':[{'start':'2026-04-01T00:00:00Z','end':'2026-07-01T00:00:00Z','state':'spent'}]}},
      'experiments':{'wbeth-book-20260911':exp}}
(program/'gates-wbeth-book.json').write_text(json.dumps(spec))
git('add','.')
git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','synthetic WBETH lifecycle')
source=git('rev-parse','HEAD')
sys.argv=['wbeth_book_run.py','--source',source]
fixture.runner.main()
directory=root/'research_runs/wbeth-book-20260911'
verified=verify_run(directory)
summary=json.loads((directory/'outputs/summary.json').read_text())
assert verified['cell_count']==8 and verified['unavailable_count']==0 and verified['output_count']==2
assert all(row['statistics']['market_exposure']['status']=='complete' for row in summary['cases'])
actual=sum(p.stat().st_size for p in (directory/'outputs').iterdir())
assert actual<=20*1024**2
(root/'synthetic-result.json').write_text(json.dumps({'verification':verified,'exposure_complete':8,'output_bytes':actual,'cpus':len(os.sched_getaffinity(0)),'source_files':source_files}))
'''


def test_actual_wbeth_cli_lifecycle_under_guard(tmp_path):
    import shutil
    loader=importlib.util.spec_from_file_location('wbeth_guard',DIRECTORY/'resource_guard_v2.py')
    guard=importlib.util.module_from_spec(loader);loader.loader.exec_module(guard)
    program=tmp_path/'research/strategy-search-2026-09-11';program.mkdir(parents=True)
    for name in ('wbeth_book_run.py','wbeth_book.py','wbeth_inputs.py','wbeth-request-spec.json','carry_capture.py','carry_book.py','carry_statistics.py','options_metadata.py'):
        shutil.copyfile(DIRECTORY/name,program/name)
    root=DIRECTORY.parents[1]
    package=tmp_path/'tradingagents';package.mkdir()
    shutil.copyfile(root/'tradingagents/__init__.py',package/'__init__.py')
    shutil.copytree(root/'tradingagents/research',package/'research',ignore=shutil.ignore_patterns('__pycache__'))
    tests=tmp_path/'tests/research';tests.mkdir(parents=True)
    shutil.copyfile(Path(__file__),tests/'test_wbeth_book_run.py')
    (tmp_path/'driver.py').write_text(LIFECYCLE_DRIVER)
    report=guard.run_guard([sys.executable,'-B',str(tmp_path/'driver.py')])
    (tmp_path/'guard-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120
    result=json.loads((tmp_path/'synthetic-result.json').read_text())
    assert result['exposure_complete']==8 and result['cpus']<=2
