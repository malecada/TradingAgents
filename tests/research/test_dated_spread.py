"""Invented two-derivative books and retained source envelopes; no network/data I/O."""
import base64
import copy
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import zipfile
import pytest
DIRECTORY=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
sys.path.insert(0,str(DIRECTORY))
import dated_spread_book as engine
import dated_spread_sources as sources
import dated_spread_run as runner


def make_bars(count=56,interval=86400000,start=1777593600000,price=100):
    return [[start+i*interval,str(price),str(price+10),str(price-10),str(price),'1',start+(i+1)*interval-1,'100',1,'0','0','0'] for i in range(count)]


def invented():
    events=[{'symbol':'ETHUSDT','fundingTime':engine.START+i*engine.DAY//3,'fundingRate':'0.0001','markPrice':'100'} for i in range(168)]
    return [make_bars(1344,3600000),make_bars(),make_bars(),make_bars(),events,make_bars()]


def call(data=None,**kwargs):return engine.book(*(data or invented()),asset=kwargs.pop('asset','ETH'),capital=kwargs.pop('capital',1000),cost_scenario=kwargs.pop('cost_scenario','base'),**kwargs)


def synthetic_inputs():
    """Create all raw envelopes through frozen collectors with in-memory transports."""
    carry=sources.carry;archive=sources.archive;mark=sources.mark
    spec=carry.frozen_request_spec();calls=[]
    def carry_fake(url):
        req=spec['requests'][len(calls)];calls.append(url);kind=req['kind']
        if kind=='funding':value=[{'symbol':req['parameters']['symbol'],'fundingTime':carry.START_MS+i*carry.DAY_MS//3,'fundingRate':str(.0001 if i%3 else -.00002),'markPrice':'100'} for i in range(273)]
        elif kind in ('spot','perp','mark'):
            value=make_bars(91,start=carry.START_MS)
            for i,row in enumerate(value):
                price=100+3*math.sin(i*(.31 if req['parameters']['symbol'].startswith('BTC') else .47))
                row[1:5]=[str(price),str(price+10),str(price-10),str(price+.2)]
        elif kind=='exchange-info':value={'symbols':[{'symbol':a+'USDT','contractType':'PERPETUAL','quoteAsset':'USDT','marginAsset':'USDT','status':'TRADING'} for a in ('BTC','ETH')]}
        else:value={'serverTime':int(datetime.now(timezone.utc).timestamp()*1000)}
        return {'body':json.dumps(value).encode(),'http_status':200,'headers':{},'body_complete':True,'error':None}
    cc,ca,_=carry.capture(spec,carry_fake)
    asp=archive.frozen_request_spec();bodies={}
    for req in asp['requests']:
        if req['kind']!='zip':continue
        start,end=archive._month_bounds(req['month']);count=744 if req['month']=='2026-05' else 609
        stream=io.StringIO();writer=csv.writer(stream);writer.writerow(archive.HEADER)
        writer.writerows(make_bars(count,3600000,start=start))
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(req['filename'][:-4]+'.csv',stream.getvalue())
        body=buf.getvalue();bodies[req['url']]=body;bodies[req['url']+'.CHECKSUM']=(hashlib.sha256(body).hexdigest()+'  '+req['filename']+'\n').encode()
    ac,aa,_=archive.capture(asp,lambda url:{'body':bodies[url],'http_status':200,'headers':{},'body_complete':True,'error':None})
    output={}
    mc,ma,_=mark.run(mark.default_spec(),lambda name,value:output.__setitem__(name,value),lambda url:{'body':json.dumps(make_bars()).encode(),'http_status':200,'headers':{},'body_complete':True,'error':None})
    assert all(c['status']=='complete' for a in (ca,aa,ma) for c in a['cells'])
    return {**{name:runner.encoded(value) for name,value in [('carry_capture',cc),('carry_admission',ca),('archive_capture',ac),('archive_admission',aa),('mark_capture',mc),('mark_admission',ma)]},
            **{a+'_dated_mark_receipt':mark.encoded(output[a+'-dated-mark-receipt.json']) for a in ('btc','eth')}}


def test_constant_cash_funding_and_reserve_release():
    result=call();q=result['initial']['quantity'];final=result['final_ledger']
    assert q==3.99 and final['funding_cash']==pytest.approx(167*q*.01)
    assert final['slippage_cost']==pytest.approx(q*.08)
    assert final['all_fees']==pytest.approx(q*.2)
    assert final['cash_profit']==pytest.approx(q*(1.67-.08-.2))
    assert final['dated_wallet_after_close']+final['perp_wallet_after_close']+100==pytest.approx(final['final_cash'])
    assert result['daily_trace'][-1]['gross_market_notional']==0
    assert result['daily_trace'][-1]['pre_exit_components']['gross_market_notional']>0
    assert len(result['stress_states'])==9 and len(result['scalar_diagnostics'])==2


@pytest.mark.parametrize('shift',[-5000,0,5000])
def test_boundary_ownership_uses_first_slot_exclusion(shift):
    data=invented();data[4][0]['fundingTime']+=shift;data[4][0]['fundingRate']='100'
    result=call(data);assert result['metrics']['applied_funding_events']==167
    assert result['metrics']['funding_cash']==pytest.approx(167*3.99*.01)


@pytest.mark.parametrize('bad',['gap','symbol','extra','outside'])
def test_incomplete_or_unowned_funding_rejected(bad):
    data=invented()
    if bad=='gap':data[4].pop(70)
    if bad=='symbol':data[4][1]['symbol']='BTCUSDT'
    if bad=='extra':data[4].append({**data[4][-1],'fundingTime':engine.END-1})
    if bad=='outside':data[4][-1]['fundingTime']=engine.END
    with pytest.raises(ValueError):call(data)


def test_mark_trade_distinction_and_negative_wallet_retained():
    data=invented()
    for row in data[3]:row[1:5]=['1000','1010','990','1000'];row[5]=row[8]=0
    result=call(data)
    assert result['final_ledger']['cash_profit']>0
    assert result['daily_trace'][0]['nav']<0
    assert result['metrics']['path_wallet_deficit'] is True
    assert result['convention_diagnostic']['status']=='unavailable'
    assert result['metrics']['modeled_net_base_fraction_nav'] is None


def test_full_readmission_and_all_denominators():
    books,summary,audit,cells=runner.evaluate(synthetic_inputs())
    assert all(c['status']=='complete' for c in cells)
    assert len(audit['source_states'])==20 and all(s['status']=='complete' for s in audit['source_states'].values())
    assert summary['complete_primary']==8 and summary['complete_scalars']==16 and summary['complete_stresses']==72
    assert all(len(b['daily_trace'])==56 and len(b['funding_events'])==168 for b in books['cases'].values())
    assert all(c['statistics']['market_exposure']['status']=='complete' for c in summary['cases'])
    assert sum(len(runner.encoded(x)) for x in (books,summary,audit))<8*1024**2


@pytest.mark.parametrize('kind',['carry_capture','archive_capture','mark_capture'])
def test_entire_parent_loss_preserves_eight_16_72(kind):
    inputs=synthetic_inputs();inputs[kind]=b'{}'
    books,summary,audit,cells=runner.evaluate(inputs)
    assert len(cells)==8 and summary['unavailable_primary']==8
    assert summary['unavailable_scalars']==16 and summary['unavailable_stresses']==72
    assert len(audit['source_states'])==20
    assert all(c['conditional_screens']['positive_cash_and_3pct_annual_base_and_stress'] is None for c in summary['cases'])


@pytest.mark.parametrize('mutation',['bool_http','bool_bytes','normalized','hash','clock','url'])
def test_source_tamper_only_blocks_affected_asset(mutation):
    inputs=synthetic_inputs();capture=sources.strict(inputs['carry_capture']);admit=sources.strict(inputs['carry_admission'])
    rec=next(x for x in capture['requests'] if x['id']=='btc-funding')
    if mutation=='bool_http':rec['http_status']=True
    elif mutation=='bool_bytes':rec['body_bytes']=True
    elif mutation=='hash':rec['body_sha256']='0'*64
    elif mutation=='clock':rec['retrieval_utc']='2000-01-01T00:00:00+00:00'
    elif mutation=='url':rec['request_url']='https://invalid.invalid'
    else:next(x for x in admit['cells'] if x['id']=='btc-funding')['observations']=274
    inputs['carry_capture']=runner.encoded(capture);inputs['carry_admission']=runner.encoded(admit)
    _,summary,_,cells=runner.evaluate(inputs)
    assert summary['unavailable_primary']==4 and summary['complete_primary']==4
    assert all(c['status']=='unavailable' for c in cells if c['id'].startswith('btc'))
    assert all(c['statistics']['market_exposure']['status']=='complete' for c in summary['cases'] if c['asset']=='ETH')


def test_early_june26_event_does_not_enter_canonical_slice():
    inputs=synthetic_inputs();capture=sources.strict(inputs['carry_capture']);admit=sources.strict(inputs['carry_admission'])
    for rec in capture['requests']:
        if rec['kind']!='funding':continue
        data=sources.strict(base64.b64decode(rec['body_base64']));data[258]['fundingTime']-=1;data[258]['fundingRate']='100'
        raw=runner.encoded(data);rec.update(body_base64=base64.b64encode(raw).decode(),body_bytes=len(raw),body_sha256=sources.sha(raw))
        req=next(x for x in sources.carry.frozen_request_spec()['requests'] if x['id']==rec['id'])
        normal={'id':rec['id'],**sources.carry.admit_response(req,raw),'coverage':sources.carry.funding_coverage(data)}
        admit['cells']=[normal if x['id']==rec['id'] else x for x in admit['cells']]
    inputs['carry_capture']=runner.encoded(capture);inputs['carry_admission']=runner.encoded(admit)
    data,audit=sources.readmit(inputs)
    assert len(data['BTC']['funding'])==168
    assert all(r['fundingRate']!='100' for r in data['BTC']['funding'])
    assert audit['clipping']['BTC']['funding']['canonical_after']==15

GUARDED_DRIVER=r'''
import hashlib,importlib.util,json,os,sys
from pathlib import Path
root=Path(__file__).resolve().parent
source_dir=root/'research/strategy-search-2026-09-11'
sys.path.insert(0,str(source_dir))
import dated_spread_run as runner

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
fixture=load('spread_fixture',root/'test_spread_lifecycle.py')
financial=load('financial_fixture',root/'test_dated_spread.py')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs=financial.synthetic_inputs();mode=sys.argv[1]
if mode=='unavailable':inputs={name:b'{}' for name in inputs}
if mode=='partial':inputs['btc_dated_mark_receipt']=b'{}'
for name,raw in inputs.items():(root/(name+'.json')).write_bytes(raw)
sourcefiles=list(source_dir.glob('*.py'))+[root/'driver.py',root/'resource_guard_v2.py',root/'test_spread_lifecycle.py',root/'test_extended_lifecycle.py',root/'test_dated_spread.py']
updates={'inputs':{name:{'path':name+'.json','sha256':sha(root/(name+'.json')),'dataset':'sample'} for name in runner.INPUTS},
         'source_files':{str(p.relative_to(root)):sha(p) for p in sourcefiles},
         'cells':[runner.case_id(*case) for case in runner.CASES],'outputs':['books.json','summary.json','source-audit.json']}
root,spec,cert,source=fixture.build_spread(root,target_updates=updates)
(source_dir/'gates-dated-spread.json').write_bytes((root/'spread-registration.json').read_bytes());source=fixture.commit(root)
sys.argv=['dated_spread_run.py','--source',source];runner.main()
folder=root/'research_runs/dated-spread-book-20260911';verified=fixture.verify_run(folder)
out=folder/'outputs';summary=json.loads((out/'summary.json').read_text())
complete={'full':8,'partial':4,'unavailable':0}[mode]
assert summary['complete_primary']==complete and summary['unavailable_primary']==8-complete
assert summary['complete_scalars']==complete*2 and summary['unavailable_scalars']==(8-complete)*2
assert summary['complete_stresses']==complete*9 and summary['unavailable_stresses']==(8-complete)*9
assert verified['cell_count']==8 and len(list(out.iterdir()))==3
size=sum(p.stat().st_size for p in out.iterdir());assert size<=8*1024**2 and len(os.sched_getaffinity(0))<=2
(root/'synthetic-result.json').write_text(json.dumps({'mode':mode,'verified':verified,'complete_primary':complete,'unavailable_primary':8-complete,
    'scalars':16,'stresses':72,'output_files':3,'output_bytes':size,'cpu_count':len(os.sched_getaffinity(0)),
    'source_sha256':{str(p.relative_to(root)):sha(p) for p in sourcefiles},'runtime_hashes':fixture.runtime_hashes()}))
'''


@pytest.mark.parametrize('mode',['full','partial','unavailable'])
def test_exact_guarded_cli_and_retention(tmp_path,mode):
    import shutil
    import subprocess
    nested=tmp_path/'research/strategy-search-2026-09-11';nested.mkdir(parents=True)
    for name in ('dated_spread_book.py','dated_spread_sources.py','dated_spread_statistics.py','dated_spread_run.py',
                 'carry_capture.py','dated_archive.py','dated_mark.py','dated_mark_transport.py','dated_statistics.py'):
        shutil.copyfile(DIRECTORY/name,nested/name)
    for name in ('test_spread_lifecycle.py','test_extended_lifecycle.py','test_dated_spread.py'):
        shutil.copyfile(Path(__file__).with_name(name),tmp_path/name)
    shutil.copyfile(DIRECTORY/'resource_guard_v2.py',tmp_path/'resource_guard_v2.py')
    (tmp_path/'driver.py').write_text(GUARDED_DRIVER)
    result=subprocess.run([sys.executable,'-B',str(tmp_path/'resource_guard_v2.py'),'--report',str(tmp_path/'guard-report.json'),'--',sys.executable,'-B',str(tmp_path/'driver.py'),mode],capture_output=True,text=True,timeout=150)
    (tmp_path/'guard-stdout.txt').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads((tmp_path/'guard-report.json').read_text())
    assert report['limit_reason'] is None and report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120
