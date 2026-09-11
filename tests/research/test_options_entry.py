"""Invented option metadata and quotes; no network or empirical reads."""
import base64
from datetime import datetime,timezone
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import sys
import pytest
DIRECTORY=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
sys.path.insert(0,str(DIRECTORY))
import options_entry as entry
NOW=1800000000000
CLOCK=datetime.fromtimestamp(NOW/1000,timezone.utc).isoformat()


def row(asset='BTC',days=30,strike='100',**extra):
    expiry=NOW+days*entry.DAY
    symbol=f"{asset}-{datetime.fromtimestamp(expiry/1000,timezone.utc).strftime('%y%m%d')}-{strike}-C"
    return {'symbol':symbol,'underlying':asset+'USDT','quoteAsset':'USDT','side':'CALL','status':'TRADING','expiryDate':expiry,'strikePrice':strike,
            'unit':'2','minQty':'0.1','maxQty':'10','filters':[{'filterType':'LOT_SIZE','minQty':'0.1','maxQty':'10','stepSize':'0.1'}],**extra}


def metadata(rows=None):
    data={'optionSymbols':rows if rows is not None else [row(asset) for asset in entry.ASSETS],
          'optionContracts':[{'underlying':a+'USDT','baseAsset':a,'quoteAsset':'USDT','settleAsset':'USDT'} for a in entry.ASSETS]}
    spec=json.loads((DIRECTORY/'options-request-spec.json').read_text())
    request=next(r for r in spec['requests'] if r['kind']=='exchange-info')
    raw=json.dumps(data).encode()
    receipt={**request,'attempted':True,'http_status':200,'body_complete':True,'error':None,'body_base64':base64.b64encode(raw).decode(),
             'body_bytes':len(raw),'body_sha256':entry.sha(raw),'request_utc':CLOCK,'retrieval_utc':CLOCK}
    admission={'cells':[{'id':request['id'],**entry.options_metadata.parse_exchange_info(raw)}]}
    return {'request_spec':spec,'requests':[receipt]},admission,receipt


def fake_response(url):
    from urllib.parse import urlsplit,parse_qs
    parsed=urlsplit(url);query=parse_qs(parsed.query)
    if parsed.path.endswith('/time'):data={'serverTime':NOW}
    elif parsed.path.endswith('/index'):data={'time':NOW,'indexPrice':'100'}
    elif parsed.path.endswith('/depth'):data={'bids':[['9','1']],'asks':[['10','1']],'T':NOW,'lastUpdateId':1}
    else:data=[{'symbol':query['symbol'][0],'markPrice':'9.5','delta':'0.5'}]
    return {'body':json.dumps(data).encode(),'http_status':200,'body_complete':True,'headers':{},'error':None}


def execute(monkeypatch,transport=fake_response,parents=None):
    monkeypatch.setattr(entry,'utc',lambda:CLOCK)
    store={}
    result=entry.run(entry.default_spec(),*(parents or metadata()),lambda n,v:store.__setitem__(n,v),transport)
    return result,store


def test_all_cells_and_no_second_unit_multiplication(monkeypatch):
    (capture,book,summary,cells),store=execute(monkeypatch)
    assert len(cells)==15 and all(c['status']=='complete' for c in cells)
    assert len(store)==10 and summary['graduation'] is False
    value=book['cases']['btc-1000-0.00024']
    assert Decimal(value['premium_usdt'])==1
    assert Decimal(value['fee_usdt'])==Decimal('0.0048')
    assert value['component_fits_capital'] and value['visible_ask_size_sufficient']
    assert all('body_base64' not in ref for ref in capture['receipts'])


def test_persist_before_parse_and_only_selection_parsing_during_capture(monkeypatch):
    monkeypatch.setattr(entry,'utc',lambda:CLOCK);store={};calls=[];original=entry.parse_response
    def parse(raw,request,receipt):
        assert request['id']+'-receipt.json' in store
        if request['kind'] in ('depth','mark'):assert len(calls)==7
        return original(raw,request,receipt)
    def transport(url):calls.append(url);return fake_response(url)
    monkeypatch.setattr(entry,'parse_response',parse)
    entry.run(entry.default_spec(),*metadata(),lambda n,v:store.__setitem__(n,v),transport)
    assert len(calls)==7


def test_denial_suppresses_all_remaining_slots(monkeypatch):
    calls=[]
    def denied(url):calls.append(url);return {'body':b'denied','http_status':451,'body_complete':True,'headers':{},'error':'HTTP451'}
    (_,book,_,cells),store=execute(monkeypatch,denied)
    assert len(calls)==1 and len(cells)==15 and all(v['status']=='unavailable' for v in book['cases'].values())
    assert sum(v['attempted'] for k,v in store.items() if k.endswith('-receipt.json'))==1


def test_missing_mark_does_not_erase_buyer_and_index_only_blocks_its_asset(monkeypatch):
    def missing_mark(url):
        result=fake_response(url)
        if '/mark?' in url:result['body']=b'[]'
        return result
    (_,book,_,cells),_=execute(monkeypatch,missing_mark)
    assert all(v['status']=='complete' for v in book['cases'].values())
    assert sum(c['status']=='unavailable' for c in cells)==2
    def missing_index(url):
        result=fake_response(url)
        if '/index?underlying=BTCUSDT' in url:result['body']=b'{}'
        return result
    (_,book,_,cells),store=execute(monkeypatch,missing_index)
    assert all(v['status']==('unavailable' if k.startswith('btc') else 'complete') for k,v in book['cases'].items())
    assert not store['btc-depth-receipt.json']['attempted']


def test_selection_ties_status_and_lot_conflicts():
    rows=[row(days=29,strike='90'),row(days=31,strike='100'),row(days=29,strike='110')]
    data,_=entry.metadata(*metadata(rows));result=entry.select(data,'BTC',NOW,Decimal(100))
    assert result['selected']['strike']=='90'
    del rows[0]['status'];data,_=entry.metadata(*metadata(rows))
    assert entry.select(data,'BTC',NOW,Decimal(100))['selected']['metadata_status']=='unverified'
    rows[0]['filters'][0]['stepSize']='0.03'
    data,_=entry.metadata(*metadata(rows))
    assert entry.select(data,'BTC',NOW,Decimal(100))['selected']['strike']=='110'


@pytest.mark.parametrize('field,value',[('body_complete',1),('attempted',1),('http_status',200.0),('body_sha256','bad')])
def test_parent_receipt_mismatch_retains_all_cells(monkeypatch,field,value):
    parents=metadata();parents[2][field]=value
    (_,book,_,cells),store=execute(monkeypatch,lambda _:pytest.fail('network attempt with invalid metadata'),parents)
    assert len(cells)==15 and all(v['status']=='unavailable' for v in book['cases'].values())
    assert len(store)==10


def test_fee_cap_exact_comparison_and_insufficient_visible_size():
    selection={'selected':{'symbol':'invented','minQty':'1','unit':'2'}}
    depth={'asks':[['1000','0']]}
    value=entry.component(selection,depth,Decimal('1000000000'),1000,'0.00024')
    assert Decimal(value['fee_usdt'])==Decimal('100') and not value['component_fits_capital'] and not value['visible_ask_size_sufficient']
    value=entry.component(selection,{'asks':[['1','1']]},Decimal('1'),1,'0.00024')
    assert Decimal(value['entry_component_usdt'])==Decimal('1.00048') and not value['component_fits_capital']


@pytest.mark.parametrize('raw',[b'{"time":1,"time":2}',b'{"indexPrice":"NaN","time":1}',b'{"x":'+b'['*12000+b'0'+b']'*12000+b'}'])
def test_malformed_prerequisite_retains_denominator(monkeypatch,raw):
    def transport(url):
        result=fake_response(url)
        if '/index?' in url:result['body']=raw
        return result
    (_,_,_,cells),store=execute(monkeypatch,transport)
    assert len(cells)==15 and len(store)==10

@pytest.mark.parametrize('overflow',[False,True])
def test_bounded_transport_real_http_response(monkeypatch,overflow):
    import io
    transport=entry.transport_module
    body=b'x'*(transport.MAX_BYTES+1) if overflow else b'{}'
    declared=len(body) if overflow else 100
    class Socket:
        def makefile(self,*args):return io.BytesIO(f'HTTP/1.1 200 OK\r\nContent-Length: {declared}\r\n\r\n'.encode()+body)
    response=transport.http.client.HTTPResponse(Socket());response.begin()
    class Opener:
        def open(self,*args,**kwargs):return response
    monkeypatch.setattr(transport.urllib.request,'build_opener',lambda *args:Opener())
    result=transport.public_get('https://eapi.binance.com/eapi/v1/time')
    assert result['body_complete'] is False
    assert result['body']==body[:transport.MAX_BYTES]
    assert ('256KiB' if overflow else 'Content-Length EOF') in result['error']


DRIVER=r'''
import hashlib,json,os,subprocess,sys
from pathlib import Path
import fixture
import options_entry as runner
from tradingagents.research import runtime_hashes
root=Path(__file__).resolve().parent
fixture.DIRECTORY=root
mode=sys.argv[1]
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def sha(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
# Invented large old metadata, not selected by premium or other outcome.
rows=[fixture.row(asset,days=30 if i<5 else 100,strike=str(i+1),padding='x'*1500) for asset in runner.ASSETS for i in range(1000)]
capture,admission,receipt=fixture.metadata(rows)
values={'request_spec':runner.default_spec(),'metadata_capture':capture,'metadata_admission':admission,'metadata_receipt':receipt}
for name,value in values.items():(root/(name+'.json')).write_bytes(runner.lifecycle_bytes(value))
del values,capture,admission,receipt,rows
(root/'charter.md').write_text('Invented options resource prerequisite; no real data.')
git('init','-q')
names=['driver.py','fixture.py','options_entry.py','options_entry_transport.py','options_metadata.py','carry_capture.py']
ids=[r['id'] for r in runner.default_spec()['requests']]+[runner.component_id(a,c,f) for a in runner.ASSETS for c in (1000,10000) for f in runner.FEES]
outputs=[r['id']+'-receipt.json' for r in runner.default_spec()['requests']]+['capture.json','entry.json','summary.json']
registration={'schema_version':1,'program_id':'synthetic-entry','families':{'s':{'mechanism_id':'synthetic-entry','attempt_budget':1,'prior_attempts':0,'history_reference':'invented'}},'datasets':{'s':{'identity':'invented','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},'experiments':{'synthetic-entry':{'family':'s','parent':None,'charter':{'path':'charter.md','sha256':sha('charter.md')},'question':'Synthetic resource validation','stage':'development','reuse':'exploratory','windows':[{'dataset':'s','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],'inputs':{n:{'path':n+'.json','sha256':sha(n+'.json'),'dataset':'s'} for n in ['request_spec','metadata_capture','metadata_admission','metadata_receipt']},'source_files':{n:sha(n) for n in names},'runtime_hashes':runtime_hashes(),'selection':None,'cells':ids,'outputs':outputs}}}
(root/'registration.json').write_text(json.dumps(registration))
git('add','.')
git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','invented')
source=git('rev-parse','HEAD')
calls=[]
def fake(url):
    calls.append(url)
    if mode=='denied':return {'body':b'x'*(256*1024),'http_status':451,'body_complete':True,'error':'HTTP451','headers':{}}
    result=fixture.fake_response(url);data=json.loads(result['body'])
    # Numerous ignored structured fields stress bounded decoding, not only whitespace.
    target=data[0] if isinstance(data,list) else data
    target['unknown_structured']=[{'n':i,'v':'x'*20} for i in range(4000)]
    raw=json.dumps(data).encode()
    assert len(raw)<256*1024
    result['body']=raw+b' '*(256*1024-len(raw))
    return result
runner.transport_module.public_get=fake
runner.utc=lambda:fixture.CLOCK
runner.REGISTRATION='registration.json';runner.EXPERIMENT='synthetic-entry'
runner.__file__=str(root/'research/fixture/options_entry.py')
sys.argv=['options_entry.py','--source',source]
runner.main()
folder=root/'research_runs/synthetic-entry/outputs'
actual=sum(p.stat().st_size for p in folder.iterdir())
book=json.loads((folder/'entry.json').read_text())
complete=json.loads((folder.parent/'complete.json').read_text())
assert len(list(folder.iterdir()))==10 and len(book['cases'])==8
assert all(value['status']==('complete' if mode=='max' else 'unavailable') for value in book['cases'].values())
assert len(calls)==(7 if mode=='max' else 1)
assert actual<=12*1024**2
(root/'synthetic-result.json').write_text(json.dumps({'mode':mode,'output_bytes':actual,'request_count':len(calls),'cpu_count':len(os.sched_getaffinity(0)),'top_cells':15,'source_sha256':{n:sha(n) for n in names}}))
'''

@pytest.mark.parametrize('mode',['max','denied'])
def test_actual_guarded_options_lifecycle(tmp_path,mode):
    import shutil,subprocess
    for name in ['options_entry.py','options_entry_transport.py','options_metadata.py','carry_capture.py','options-request-spec.json','options_entry_guard.py','resource_guard_v2.py']:
        shutil.copyfile(DIRECTORY/name,tmp_path/name)
    shutil.copyfile(__file__,tmp_path/'fixture.py')
    (tmp_path/'driver.py').write_text(DRIVER)
    result=subprocess.run([sys.executable,'-B',str(tmp_path/'options_entry_guard.py'),'--report',str(tmp_path/'guard-report.json'),'--',sys.executable,'-B',str(tmp_path/'driver.py'),mode],capture_output=True,text=True,timeout=90)
    (tmp_path/'guard-stdout.txt').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads((tmp_path/'guard-report.json').read_text())
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==240 and report['limit_reason'] is None


def test_parent_normalization_duplicate_parent_and_nontrading(monkeypatch):
    parents=metadata();parents[1]['cells'][0]['scope']='changed normalization'
    (_,_,_,cells),store=execute(monkeypatch,lambda _:pytest.fail('invalid metadata requested'),parents)
    assert all(c['status']=='unavailable' for c in cells)
    data,_=entry.metadata(*metadata())
    data['optionContracts'].append(dict(data['optionContracts'][0]))
    with pytest.raises(ValueError,match='duplicate'):entry.select(data,'BTC',NOW,Decimal(100))
    data,_=entry.metadata(*metadata([row(status='HALT')]))
    with pytest.raises(ValueError,match='no eligible'):entry.select(data,'BTC',NOW,Decimal(100))


@pytest.mark.parametrize('kind,changes',[('time',{'serverTime':NOW+5001}),('index',{'underlying':'WRONG'}),('depth',{'symbol':'WRONG'}),
                                       ('depth',{'lastUpdateId':True}),('depth',{'asks':[['8','1']]}),('depth',{'bids':[['9','1'],['10','1']]}),
                                       ('mark',{'symbol':'WRONG'}),('mark',{'delta':'Infinity'})])
def test_source_clock_identity_and_structure_failures(monkeypatch,kind,changes):
    def transport(url):
        result=fake_response(url)
        if '/'+kind in url:
            data=json.loads(result['body']);target=data[0] if isinstance(data,list) else data;target.update(changes)
            result['body']=json.dumps(data).encode()
        return result
    (capture,book,_,cells),_=execute(monkeypatch,transport)
    assert len(cells)==15
    relevant=[value for key,value in capture['source_admission'].items() if key.endswith('-'+kind) or kind=='time' and key=='options-time']
    assert relevant and all(value['status']=='unavailable' for value in relevant)
    if kind=='mark':assert all(v['status']=='complete' for v in book['cases'].values())


def test_exact_long_precision_fee_and_size_boundary():
    # A difference far below default Decimal precision must still fail size/capital.
    q='1.'+'0'*60+'1'
    selection={'selected':{'symbol':'invented','minQty':q,'unit':'1'}}
    value=entry.component(selection,{'asks':[['1000','1']]},Decimal('1e-32'),1000,'0.00024')
    assert not value['component_fits_capital'] and not value['visible_ask_size_sufficient']


def test_denied_later_receipt_retains_previously_selected_identity(monkeypatch):
    def transport(url):
        result=fake_response(url)
        if '/depth?' in url and 'symbol=ETH-' in url:result.update(http_status=451,error='HTTP451')
        return result
    (_,_,_,cells),store=execute(monkeypatch,transport)
    assert len(cells)==15
    assert store['btc-mark-receipt.json']['parameters']['symbol'].startswith('BTC-')
    assert not store['btc-mark-receipt.json']['attempted']


@pytest.mark.parametrize('expiry',[NOW-entry.DAY,2**63,True])
def test_expired_or_non_int64_expiry_is_ineligible(expiry):
    data,_=entry.metadata(*metadata([row(expiryDate=expiry)]))
    with pytest.raises(ValueError,match='no eligible'):entry.select(data,'BTC',NOW,Decimal(100))
