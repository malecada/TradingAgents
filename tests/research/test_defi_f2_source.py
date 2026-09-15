"""Invented source only; no historical files, external HTTP or financial inputs."""
import importlib.util
import json
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import pytest
path=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/f2_source.py'
s=importlib.util.spec_from_file_location('test_f2_source',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    days=[];headers={};context={}
    for i in range(366):
        d=date(2025,9,1)+timedelta(days=i);ts=int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp());number=10**7+i*43200
        day={'date':str(d),'timestamp':ts,'candidate_block':number};days.append(day)
        pair=[]
        for off in (0,1):
            n=number+off;raw={'number':hex(n),'timestamp':hex(ts-1+2*off),'baseFeePerGas':'0x1','hash':'0x'+format(n,'064x'),'parentHash':'0x'+format(n-1,'064x')}
            headers[n]=raw;pair.append(m.p.old.parse_header(raw,n,2e9))
        if str(d) in m.RETAINED:context[str(d)]={'headers':pair,'block':m.p.old.bracket(*pair,ts),'wst_price':2400*10**8}
    design={'days':days,'acquisition_order':['2025-09-01','2025-09-02','2026-09-01']+[d['date'] for d in days if d['date'] not in ('2025-09-01','2025-09-02','2026-09-01')],
      'prior_base_request_keys':[], 'chains':{'base':{'url':'https://mainnet.base.org'}},'pacing':{'minimum_seconds_after_previous_response_same_endpoint':5},
      'recognized_rpc_throttling':{'codes':[-32016],'message_fragments_casefold':['rate limit']},'denials_stop_endpoint':[403,418,429,451],
      'max_rpc_subcalls':1094,'max_http_requests':1094,'max_response_bytes':262144,'worst_case_raw_bytes':1094*262144}
    calls=[];clock=[0];outputs={}
    def publish(name,obj):
        assert name not in outputs;outputs[name]=obj
    def fetch(url,payload):
        calls.append(payload)
        if payload['method']=='eth_getBlockByNumber':value=headers[int(payload['params'][0],16)]
        else:
            data=payload['params'][0]['data'];n=int(data[74:138],16)
            values=[2400*10**8,2000*10**8,10**8] if n==3 else [2000*10**8,10**8]
            value='0x'+''.join(format(v,'064x') for v in [32,n]+values)
        body=json.dumps({'jsonrpc':'2.0','id':payload['id'],'result':value}).encode()
        return {'body':body,'http_status':200,'headers':{},'error':None,'body_complete':True}
    return design,context,outputs,calls,fetch,publish,{'monotonic':lambda:clock[0],'sleep':lambda delay:clock.__setitem__(0,clock[0]+delay),'utc':lambda:datetime(2026,9,16,tzinfo=timezone.utc)}

def test_complete_source_and_financial_denominator(capsys):
    d,c,o,calls,f,p,clocks=fixture();summary,cells=m.capture(d,c,p,f,**clocks)
    assert summary['status']=='complete' and len(calls)==1094
    assert len(summary['price_rows'])==366 and summary['price_rows'][0]['date']=='2025-09-01'
    baseline={'B'+str(i):{k:m.unavailable('invented missing benchmark') for k in m.book.SCENARIOS} for i in range(10)}
    financial=m.financial(summary,baseline,p)
    p('history.json',{})
    expected_cells,expected_outputs=m.manifests(d)
    assert set(o)==set(expected_outputs)
    assert {r['id'] for r in cells+financial}|{'retained-history'}==set(expected_cells)
    assert len(cells+financial)+1==1532
    assert all(o['2026-'+policy.lower()+'-primary.json']['status']=='complete' for policy in m.book.POLICIES)

def test_throttle_stops_and_preserves_every_skipped_cell(capsys):
    d,c,o,calls,f,p,clocks=fixture()
    def denied(url,payload):
        calls.append(payload)
        body=json.dumps({'jsonrpc':'2.0','id':payload['id'],'error':{'code':-32016,'message':'over rate limit'}}).encode()
        return {'body':body,'http_status':200,'headers':{},'error':None,'body_complete':True}
    summary,cells=m.capture(d,c,p,denied,**clocks)
    assert len(calls)==1 and summary['status']=='unavailable'
    assert sum(obj.get('attempted') is True for name,obj in o.items() if name.endswith('-attempt.json'))==1
    assert len(cells)==1465
    assert sum(name.endswith('-receipt.json') for name in o)==1094

def test_array_abi_exact_and_fails_closed():
    assert m.encode_prices(['ETH','USDC']).startswith('0x9d23d9f2')
    for words in ([0,1,5],[32,2,5],[32,1,0],[32,1,5,0]):
        value='0x'+''.join(format(w,'064x') for w in words)
        with pytest.raises(ValueError):m.parse_prices(value,['ETH'])

def test_excludes_old_underlying_call_key_before_transport(capsys):
    d,c,o,calls,f,p,clocks=fixture();block=c['2025-09-01']['block']
    params=[{'to':m.ORACLE,'data':m.encode_prices(['ETH','USDC'])},{'blockHash':block['hash'],'requireCanonical':True}]
    d['prior_base_request_keys']=[m.p.request_key('eth_call',params)]
    with pytest.raises(ValueError,match='retried'):m.capture(d,c,p,f,**clocks)
    assert calls==[]

def test_missing_left_header_suppresses_right_without_retry(capsys):
    d,c,o,calls,f,p,clocks=fixture()
    def missing(url,payload):
        if payload['id']=='2025-09-02-header-left':
            calls.append(payload)
            body=json.dumps({'jsonrpc':'2.0','id':payload['id'],'error':{'code':-32000,'message':'historical state missing'}}).encode()
            return {'body':body,'http_status':200,'headers':{},'error':None,'body_complete':True}
        return f(url,payload)
    summary,cells=m.capture(d,c,p,missing,**clocks)
    assert len(calls)==2 and summary['status']=='unavailable'
    assert o['2025-09-02-header-right-attempt.json']['attempted'] is False

def test_one_infeasible_cell_does_not_suppress_other_books(monkeypatch):
    marks=[{'date':(date(2025,9,1)+timedelta(days=i)).isoformat(),'prices_atoms_1e8':{'USDC':10**8,'ETH':2000*10**8,'WST':2400*10**8}} for i in range(366)]
    source={'status':'complete','price_rows':marks};outputs={};called=[]
    def calculate(panel,policy,scenario,progress=None):
        called.append((policy,scenario))
        if (policy,scenario)==('F2','primary'):raise m.book.FinancialUnavailable('invented cell constraint')
        return {'net_cash_profit_usd':'0','absolute_floor_pass_conditional':False,'numerical_risk_pass_conditional':True}
    monkeypatch.setattr(m.book,'run_book',calculate)
    baseline={'B'+str(i):{k:m.unavailable('invented missing baseline') for k in m.book.SCENARIOS} for i in range(10)}
    m.financial(source,baseline,lambda name,obj:outputs.__setitem__(name,obj))
    assert len(called)==9 and outputs['2026-f2-primary.json']['status']=='unavailable'
    assert outputs['2026-f2-doubled.json']['status']=='complete'
    assert outputs['2026-wallet-cash-primary-attempt.json']['attempted'] is True
    assert outputs['2024-f2-primary-attempt.json']['attempted'] is False

def test_incremental_gate_uses_exact_new_book_fraction(monkeypatch):
    marks=[{'date':(date(2025,9,1)+timedelta(days=i)).isoformat(),'prices_atoms_1e8':{'USDC':10**8,'ETH':2000*10**8,'WST':2400*10**8}} for i in range(366)]
    source={'status':'complete','price_rows':marks};outputs={}
    from fractions import Fraction as F
    def calculate(panel,policy,scenario,progress=None):
        profit=F(1200)-F(1,10**80) if policy=='F2' else F(1000)
        return {'net_cash_profit_usd':m.book.render(profit),'exact_net_cash_profit':m.book.fraction_record(profit),'absolute_floor_pass_conditional':True,'numerical_risk_pass_conditional':True}
    monkeypatch.setattr(m.book,'run_book',calculate)
    baseline={'B'+str(i):{k:{'status':'complete','net_cash_profit_usd':'1000','conditional_numeric_risk_pass':True} for k in m.book.SCENARIOS} for i in range(10)}
    m.financial(source,baseline,lambda name,obj:outputs.__setitem__(name,obj))
    contrast=outputs['financial-summary.json']['comparisons']['primary']['wallet-cash']
    assert contrast['incremental_floor_pass_conditional'] is False
    exact=contrast['difference_exact'];assert F(exact['numerator'],exact['denominator'])<200
