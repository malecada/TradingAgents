"""Invented16sourcebatch; no transport, market values or empirical lifecycle."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'))
import options_policy_batch as batch

SLOT=1800000000000
SLOT-=SLOT%3600000
SYMBOLS={a:{'call':a+'-270115-100-C','put':a+'-270115-100-P'} for a in ('BTC','ETH')}
UNITS={'BTC':1,'ETH':1}


def fixture():
    out=[]
    for r in batch.requests(SYMBOLS):
        # Server offsets +100ms(options),−100ms(futures), each200msRTT.
        off=100 if r['venue']=='options' else -100
        event=SLOT+200+off
        if r['kind']=='time':value={'serverTime':event}
        elif r['kind']=='index':value={'indexPrice':'100','time':event}
        elif r['kind']=='depth':value={'T':event,'E':event+1,'lastUpdateId':1,'bids':[['9','10']],'asks':[['10','10']]}
        elif r['venue']=='options':value=[{'symbol':r['parameters']['symbol'],'markPrice':'9.5','delta':'.5' if r['side']=='call' else '-.5'}]
        else:value={'symbol':r['parameters']['symbol'],'markPrice':'100','time':event,'lastFundingRate':'.99','nextFundingTime':event+1}
        raw=json.dumps(value).encode()
        out.append({'id':r['id'],'request_url':r['endpoint']+('?' + batch.urlencode(r['parameters']) if r['parameters'] else ''),
                    'attempted':True,'body_complete':True,'http_status':200,'error':None,'body_base64':base64.b64encode(raw).decode(),
                    'body_bytes':len(raw),'body_sha256':hashlib.sha256(raw).hexdigest(),'request_ms':SLOT+100,'retrieval_ms':SLOT+300})
    return out


def run(rows=None):return batch.assemble(decision_ms=SLOT,symbols=SYMBOLS,receipts=fixture() if rows is None else rows,units=UNITS)

def body(rows,key,change):
    rec=next(r for r in rows if r['id']==key);value=json.loads(base64.b64decode(rec['body_base64']));change(value)
    raw=json.dumps(value).encode();rec.update(body_bytes=len(raw),body_sha256=hashlib.sha256(raw).hexdigest(),body_base64=base64.b64encode(raw).decode())


def test_complete16_and_fixed_action_clock():
    result=run();assert len(result['sources'])==16
    for r in result['records'].values():
        assert all(r[key] for key in ('entry_available','hedge_available','exit_available','valuation_available'))
        assert r['action_time_ms']==SLOT+5000
        assert r['clock_offsets_ms']=={'options':[0,200],'futures':[-200,0]}
        assert r['call']['unit']==r['put']['unit']==1
        assert r['model_freshness'].startswith('unavailable')
        assert 'fundingRate' not in r['perp'] and 'lastFundingRate' not in r['perp']


def test_unavailable_delta_does_not_erase_terminal_close():
    rows=fixture();body(rows,'btc-call-mark',lambda x:x[0].pop('delta'))
    r=run(rows)['records']['BTC']
    assert not r['entry_available'] and not r['hedge_available'] and r['exit_available']
    assert r['valuation_available'] and r['call']['mark']=='9.5'
    assert run(rows)['sources']['btc-call-mark']['status']=='partial'
    assert run(rows)['records']['ETH']['entry_available']


def test_perp_valuation_failure_does_not_erase_hedge_or_close():
    rows=fixture();body(rows,'btc-perp-mark',lambda x:x.update(markPrice='0'))
    r=run(rows)['records']['BTC']
    assert not r['entry_available'] and not r['valuation_available']
    assert r['hedge_available'] and r['exit_available'] and r['perp']['mark'] is None
    assert r['option_valuation_available'] and not r['perp_valuation_available']


@pytest.mark.parametrize('mutation',['old','future','wrongvenue'])
def test_transaction_age_and_venue_specific_calibration(mutation):
    rows=fixture()
    def change(x):x['T']=SLOT-1 if mutation=='old' else SLOT+7000 if mutation=='future' else SLOT+1
    body(rows,'btc-perp-depth',change)
    if mutation=='wrongvenue':
        # Futures calibration cannot be replaced by options clock; shift its
        # current server offset to+1000ms while the old source T is unchanged.
        body(rows,'futures-time',lambda x:x.update(serverTime=SLOT+1200))
    r=run(rows)['records']['BTC'];assert not r['hedge_available'] and not r['exit_available']


@pytest.mark.parametrize('mutation',['hash','bool','overflow','duplicatekey','url','backward','late','seconds'])
def test_invalid_receipts_retained_without_network(mutation):
    rows=fixture();r=next(x for x in rows if x['id']=='options-time')
    if mutation=='hash':r['body_sha256']='0'*64
    if mutation=='bool':r['http_status']=True
    if mutation=='overflow':
        raw=b' '*8193;r.update(body_base64=base64.b64encode(raw).decode(),body_bytes=len(raw),body_sha256=hashlib.sha256(raw).hexdigest())
    if mutation=='duplicatekey':
        raw=b'{"serverTime":1,"serverTime":2}';r.update(body_base64=base64.b64encode(raw).decode(),body_bytes=len(raw),body_sha256=hashlib.sha256(raw).hexdigest())
    if mutation=='url':r['request_url']='https://unbound.invalid'
    if mutation=='backward':r['retrieval_ms']=SLOT
    if mutation=='late':r['retrieval_ms']=SLOT+5001
    if mutation=='seconds':body(rows,'options-time',lambda x:x.update(serverTime=SLOT//1000))
    result=run(rows);assert len(result['sources'])==16 and result['sources']['options-time']['status']=='unavailable'
    assert all(not x['entry_available'] and not x['exit_available'] for x in result['records'].values())


def test_missing_receipt_keeps_exactdenominator():
    result=run(fixture()[:-1]);assert result['status']=='unavailable' and len(result['sources'])==16
    assert all(not r['decision_available'] for r in result['records'].values())


def test_unit_assumption_must_be_explicit_not_inferred_from_symbols():
    with pytest.raises(ValueError):batch.assemble(decision_ms=SLOT,symbols=SYMBOLS,receipts=fixture(),units={'BTC':True,'ETH':1})


def test_array_symbol_and_crossed_depth_rejected():
    rows=fixture();body(rows,'btc-perp-mark',lambda x:x.update(symbol='OTHERUSDT'))
    assert run(rows)['sources']['btc-perp-mark']['status']=='unavailable'
    rows=fixture();body(rows,'btc-call-depth',lambda x:x.update(bids=[['11','10']]))
    assert not run(rows)['records']['BTC']['exit_available']


def test_missing_model_mark_preserves_delta_for_hedging():
    rows=fixture();body(rows,'btc-call-mark',lambda x:x[0].pop('markPrice'))
    r=run(rows)['records']['BTC']
    assert not r['entry_available'] and not r['valuation_available']
    assert r['hedge_available'] and r['exit_available']
    assert r['call']['delta']=='.5' or r['call']['delta']=='0.5'
    assert r['call']['mark'] is None
    assert not r['option_valuation_available'] and r['perp_valuation_available']


def test_invented_batches_to_cash_ledger_latency_funding_and_partial_model():
    from fractions import Fraction as F
    import options_policy_engine as engine
    assembled=[]
    for hour in range(3):
        rows=fixture()
        for rec in rows:
            rec['request_ms']+=hour*3600000;rec['retrieval_ms']+=hour*3600000
            def shift(value):
                if isinstance(value,dict):
                    for key in ('T','E','time','serverTime'):
                        if key in value:value[key]+=hour*3600000
            body(rows,rec['id'],shift)
        body(rows,'btc-perp-depth',lambda x:x.update(bids=[['100','10']],asks=[['100','10']]))
        body(rows,'btc-call-mark',lambda x:x[0].update(delta='1' if hour==0 else '0'))
        body(rows,'btc-put-mark',lambda x:x[0].update(delta='0' if hour==0 else '-1'))
        if hour==2:body(rows,'btc-call-mark',lambda x:x[0].pop('delta'))
        assembled.append(batch.assemble(decision_ms=SLOT+hour*3600000,symbols=SYMBOLS,receipts=rows,units=UNITS)['records']['BTC'])
    out=engine.ledger(assembled,capital='1000',option_quantity='1',
        costs={'option_fee_rate':'0','perp_fee_rate':'0','perp_slippage':'0','option_tick_worsening':'0'},
        hedge_lot='1',hedge_min_quantity='0',hedge_min_notional='0',
        expected_funding_times=[SLOT+3000,SLOT+3603000,SLOT+7203000],
        funding_events=[{'time_ms':SLOT+3603000,'rate':'.01','mark':'100'},
                        {'time_ms':SLOT+7203000,'rate':'.02','mark':'100'}])
    assert out['initial_zero_inventory_funding_times']==[SLOT+3000]
    assert [x['inventory'] for x in out['funding_events']]==['1','-1']
    assert [x['cash'] for x in out['funding_events']]==['-1','2']
    assert out['final']['closed'] is True
    # Two options sold at9 then bought at10, unchanged hedge price, netfunding+1.
    assert F(out['final']['profit'])==-1
    assert not assembled[-1]['hedge_available'] and assembled[-1]['exit_available']
    assert assembled[-1]['valuation_available']


@pytest.mark.parametrize('mode',['receipt_future','interval_future','reversed_output','output_future'])
def test_event_cannot_follow_its_receipt_beyond_conservative_tolerance(mode):
    rows=fixture()
    def change(value):
        if mode=='receipt_future':value.update(T=SLOT+4000,E=SLOT+4001)
        if mode=='interval_future':value.update(T=SLOT+1200,E=SLOT+1201)
        if mode=='reversed_output':value['E']=value['T']-1
        if mode=='output_future':value['E']=SLOT+4000
    body(rows,'btc-perp-depth',change)
    result=run(rows)
    assert not result['records']['BTC']['hedge_available']
    assert result['records']['ETH']['hedge_available']


def test_unhashable_receipt_identity_remains_unavailable():
    rows=fixture();rows[0]['id']=[]
    assert run(rows)['status']=='unavailable'


def test_encoded_body_is_bounded_before_decoding_and_symbols_bounded():
    rows=fixture();rows[0]['body_base64']='A'*(4*((batch.LIMIT+2)//3)+1)
    assert 'encoded body exceeds bound' in run(rows)['sources']['options-time']['reason']
    names={a:dict(v) for a,v in SYMBOLS.items()}
    names['BTC']['call']='BTC-270115-'+('1'*70)+'-C'
    with pytest.raises(ValueError):batch.requests(names)
