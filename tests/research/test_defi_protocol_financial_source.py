import importlib.util
from datetime import date,timedelta,datetime,timezone
import json
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15'
spec=importlib.util.spec_from_file_location('tested_protocol_collector',HERE/'protocol_financial_source.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    reference=json.loads((HERE/'q1-spec.json').read_text())
    base=next(c for c in reference['chains'] if c['name']=='base')
    actions={a['key']:{'method':'eth_call',**a} for a in base['actions']}
    daily=[actions[k] for k in m.DAILY['F1']]
    boundary=[actions[k] for k in ('usdc-decimals','aave-pool-identity','aave-underlying')]
    for key,to in [('usdc-code',base['usdc']),('aave-pool-code',base['aave_pool']),('atoken-code',base['atoken'])]:
        boundary.append({'key':key,'to':to,'method':'eth_getCode'})
    days=[];context={};ownership={}
    for i in range(366):
        d=(date(2025,9,1)+timedelta(days=i)).isoformat();stamp=int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp())
        days.append({'date':d,'timestamp':stamp,'candidate_block':1000+i})
        h={'number':1000+i,'timestamp':stamp,'hash':'0x'+format(1000+i,'064x'),'parentHash':'0x'+format(999+i,'064x'),'baseFeePerGas':1}
        context[d]={'header':h,'prices':{'block_hash':h['hash'],'prices_atoms_1e8':{'ETH':2000*10**8,'USDC':10**8}}}
        ownership[d]={'header':'retained','prices':'retained','fields':{a['key']:'new' for a in daily+(boundary if d in m.BOUNDARIES else [])}}
    order=[days[i]['date'] for i in (0,1,365)]+[d['date'] for d in days[2:-1]]
    design={'recipe':'F1','days':days,'acquisition_order':order,'ownership':ownership,'daily_actions':daily,'boundary_actions':boundary,
            'url':'https://mainnet.base.org','attempt_delays_seconds':[0,15,60],'minimum_response_pause_seconds':5,
            'inherited_endpoint_stop':None,'prior_request_keys':[],'price_field_history':{'prior_oracle_fields':[],'unresolved_prior_price_tags':[]},'denials_stop_endpoint':sorted(m.P.DENIALS),
            'recognized_rpc_throttling':{'codes':sorted(m.P.THROTTLE_CODES),'message_fragments_casefold':sorted(m.P.THROTTLE_FRAGMENTS)}}
    design.update({k:v for k,v in m.request_inventory(design).items() if k in ('max_physical_requests','worst_case_raw_bytes')})
    return design,context


class Fake:
    def __init__(self,design):
        self.saved={};self.now=0;self.calls=[];self.design=design;self.bad_date=None;self.deny=False
        self.values={'aave-income':10**27,'aave-config':(6<<48)|(1<<56),'aave-contract-cash':10**12,
                     'aave-scaled-supply':10**9,'aave-total-supply':10**9}
        self.actions={a['key']:a for a in design['daily_actions']+design['boundary_actions']}
    def publish(self,name,value):assert name not in self.saved;self.saved[name]=value
    def sleep(self,seconds):self.now+=seconds
    def fetch(self,url,payload,*,max_bytes):
        self.calls.append(payload);rid=payload['id'];date=rid[:10];key=rid[11:].rsplit('-try',1)[0]
        assert self.saved[rid+'-attempt.json']['attempted']
        if self.deny:
            body=json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32016,'message':'rate limit'}}).encode()
            return {'body':body,'http_status':200,'headers':{},'error':None,'body_complete':True}
        if key=='aave-contract-cash' and date==self.bad_date:
            result={'error':{'code':-32000,'message':'invented missing historical cash'}}
        else:
            a=self.actions[key]
            if a['method']=='eth_getCode':value='0x6000'
            else:
                v=self.values.get(key,a.get('expected',[None])[0])
                v=int(v,16) if isinstance(v,str) else v
                value='0x'+format(v,'064x')
            result={'result':value}
        body=json.dumps({'jsonrpc':'2.0','id':rid,**result}).encode()
        return {'body':body,'http_status':200,'headers':{},'error':None,'body_complete':True}
    def run(self,design,context):
        return m.capture(design,context,self.publish,self.fetch,monotonic=lambda:self.now,sleep=self.sleep,
                         utc=lambda:datetime(2026,9,15,tzinfo=timezone.utc))


def test_complete_synthetic_source_retains_every_logical_physical_cell(capsys):
    d,c=fixture();f=Fake(d);summary,cells=f.run(d,c)
    inventory=m.request_inventory(d)
    assert summary['status']=='complete' and len(summary['rows'])==366
    assert set(f.saved)==set(inventory['outputs'])
    assert set(r['id'] for r in cells)==set(inventory['cells'])
    assert len(f.calls)==366*5+12 and summary['physical_requests']==len(f.calls)
    assert sum(v['attempted'] for k,v in f.saved.items() if k.endswith('attempt.json'))==len(f.calls)
    assert all(r['supply_identity']['value']['residual_atoms']==0 for r in summary['rows'])


def test_missing_cash_retained_with_available_endpoints_and_no_model_fill(capsys):
    d,c=fixture();f=Fake(d);f.bad_date='2025-10-01';summary,cells=f.run(d,c)
    assert summary['status']=='unavailable'
    bad=next(r for r in summary['rows'] if r['date']==f.bad_date)
    assert not bad['daily_source_complete'] and bad['fields']['aave-contract-cash']['status']=='unavailable'
    assert bad['fields']['aave-income']['status']=='complete'
    assert all(r['daily_source_complete'] for r in (summary['rows'][0],summary['rows'][1],summary['rows'][-1]))
    assert len([p for p in f.calls if p['id'].startswith(f.bad_date+'-aave-contract-cash')])==1


def test_denial_stops_actual_sends_preserves_complete_unavailable_denominator(capsys):
    d,c=fixture();f=Fake(d);f.deny=True;summary,cells=f.run(d,c)
    assert summary['status']=='unavailable' and summary['physical_requests']==1
    assert set(f.saved)==set(m.request_inventory(d)['outputs']) and summary['endpoint_stop']


def test_ownership_and_budget_gaps_rejected_before_transport():
    d,c=fixture();d['boundary_actions']=[]
    with pytest.raises(ValueError,match='boundary identity'):m.validate_design(d,c)
    d,c=fixture();d['ownership']['2025-09-01']['header']='new'
    with pytest.raises(ValueError,match='repeat retained'):m.validate_design(d,c)
    d,c=fixture();d['max_physical_requests']-=1
    with pytest.raises(ValueError,match='reservation'):m.validate_design(d,c)


def test_calendar_timestamp_and_height_cannot_be_relabelled():
    d,c=fixture();d['days'][5]['timestamp']+=86400
    with pytest.raises(ValueError,match='midnight UTC'):m.validate_design(d,c)
    for value in (-1,True,1.5):
        d,c=fixture();d['days'][5]['candidate_block']=value
        with pytest.raises(ValueError,match='exact nonnegative integer'):m.validate_design(d,c)


def test_retained_scalar_never_requested_and_failure_not_backfilled(capsys):
    d,c=fixture();day='2025-09-02';action=d['boundary_actions'][0]
    d['ownership'][day]['fields']['usdc-decimals']='retained'
    c[day]['fields']={'usdc-decimals':{'block_hash':c[day]['header']['hash'],'action':action,'value':{'words':[6]}}}
    d['ownership']['2025-10-01']['fields']['aave-contract-cash']='unavailable'
    inv=m.request_inventory(d)
    d.update({k:inv[k] for k in ('max_physical_requests','worst_case_raw_bytes')})
    f=Fake(d);summary,cells=f.run(d,c)
    assert not any(p['id'].startswith(day+'-usdc-decimals') for p in f.calls)
    assert not any(p['id'].startswith('2025-10-01-aave-contract-cash') for p in f.calls)
    assert summary['status']=='unavailable' and set(f.saved)==set(inv['outputs'])


def test_truthy_string_does_not_prove_new_ownership():
    d,c=fixture();day='2025-10-01';del c[day]
    d['ownership'][day].update(header='new',prices='new',first_header_acquisition_proved='false',first_overlapping_price_fields_proved=True)
    with pytest.raises(ValueError,match='ownership not proved'):m.validate_design(d,c)


def test_full_lp_inventory_and_boundary_decoding_with_invented_values(capsys):
    d,c=fixture();base=next(x for x in json.loads((HERE/'q1-spec.json').read_text())['chains'] if x['name']=='base')
    actions={a['key']:{'method':'eth_call',**a} for a in base['actions']}
    actions['lp-max-liquidity']={'key':'lp-max-liquidity','method':'eth_call','to':base['pool'],
                               'data':'0x70cf754a','types':['uint128'],'expected':[m.LP.MAX_TICK_LIQUIDITY]}
    for key,address in [('lp-code',base['pool']),('weth-code',base['weth']),('usdc-code',base['usdc'])]:
        actions[key]={'key':key,'method':'eth_getCode','to':address}
    d.update(recipe='F3',daily_actions=[actions[k] for k in m.DAILY['F3']],
             boundary_actions=[actions[k] for k in m.BOUNDARY_KEYS['F3']])
    for day in d['days']:
        dt=day['date'];d['ownership'][dt]['fields']={a['key']:'new' for a in d['daily_actions']+(d['boundary_actions'] if dt in m.BOUNDARIES else [])}
    inv=m.request_inventory(d);d.update({k:inv[k] for k in ('max_physical_requests','worst_case_raw_bytes')})
    f=Fake(d)
    def fetch(url,payload,*,max_bytes):
        f.calls.append(payload);rid=payload['id'];key=rid[11:].rsplit('-try',1)[0];a=actions[key]
        assert f.saved[rid+'-attempt.json']['attempted']
        if a['method']=='eth_getCode':value='0x6000'
        else:
            vals={'lp-slot0':[m.LP.T.sqrt_at_tick(-200000),-200000,0,1,1,0,1],
                  'lp-liquidity':[10**20],'lp-fee0':[123],'lp-fee1':[456],
                  'lp-lower':[0,0,0,0,0,0,0,0],'lp-upper':[0,0,0,0,0,0,0,0]}.get(key,a.get('expected'))
            value='0x'+''.join(format((int(v,16) if isinstance(v,str) else v)%(1<<256),'064x') for v in vals)
        body=json.dumps({'jsonrpc':'2.0','id':rid,'result':value}).encode()
        return {'body':body,'http_status':200,'headers':{},'error':None,'body_complete':True}
    f.fetch=fetch;summary,cells=f.run(d,c)
    assert summary['status']=='complete' and len(f.calls)==366*4+2*13
    assert set(f.saved)==set(inv['outputs']) and {x['id'] for x in cells}==set(inv['cells'])
    assert summary['rows'][1]['fields']['lp-slot0']['value']['words'][1]==-200000
    assert summary['rows'][1]['fields']['lp-max-liquidity']['value']['words']==[m.LP.MAX_TICK_LIQUIDITY]
