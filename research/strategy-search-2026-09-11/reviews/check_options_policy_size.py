"""Bounded invented episode/storage rehearsal; no market I/O or lifecycle claims."""
import base64
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import options_policy_batch as batch
import options_policy_engine as engine


def main():
    root=Path(__file__).resolve().parents[1]
    symbols={a:{'call':a+'-270115-100-C','put':a+'-270115-100-P'} for a in ('BTC','ETH')}
    receipts=[];slot=1800000000000;slot-=slot%3600000
    for request in batch.requests(symbols):
        kind=request['kind'];event=slot+200
        if kind=='time':value={'serverTime':event}
        elif kind=='index':value={'indexPrice':'100','time':event}
        elif kind=='depth':value={'T':event,'E':event+1,'lastUpdateId':1,'bids':[[str(100-i),'100'] for i in range(10)],'asks':[[str(101+i),'100'] for i in range(10)]}
        elif request['venue']=='options':value=[{'symbol':request['parameters']['symbol'],'markPrice':'100','delta':'.5' if request['side']=='call' else '-.5'}]
        else:value={'symbol':request['parameters']['symbol'],'markPrice':'100','time':event}
        # Whitespace padding is literal retained body content and valid strictJSON.
        encoded=json.dumps(value).encode();raw=encoded+b' '*(batch.LIMIT-len(encoded));assert len(raw)==8192
        receipts.append({'id':request['id'],'request_url':request['endpoint']+('?' + batch.urlencode(request['parameters']) if request['parameters'] else ''),
          'request_ms':slot+100,'retrieval_ms':slot+300,'attempted':True,'body_complete':True,'http_status':200,'error':None,
          'body_base64':base64.b64encode(raw).decode(),'body_bytes':len(raw),'body_sha256':hashlib.sha256(raw).hexdigest()})
    assembled=batch.assemble(decision_ms=slot,symbols=symbols,receipts=receipts,units={'BTC':1,'ETH':1})
    assert all(x['entry_available'] for x in assembled['records'].values())
    raw_size=sum(r['body_bytes'] for r in receipts)
    receipt_size=len(json.dumps(receipts,separators=(',',':')).encode())
    assembly_size=len(json.dumps(assembled,separators=(',',':')).encode())
    profiles=[];all_books=[]
    for asset in ('BTC','ETH'):
        for capital in ('1000','10000'):
            for stress in (False,True):
                records=[]
                for hour in range(1057):
                    price=str(100+hour%7)
                    opt={'unit':1,'bid':'10','ask':'10.01','bid_qty':'100','ask_qty':'100','mark':'10'}
                    records.append({'time_ms':slot+hour*3600000,'action_time_ms':slot+hour*3600000+5000,'decision_available':True,
                        'index':price,'call':dict(opt,delta=('1','.2','.7','.4')[hour%4]),'put':dict(opt,delta='-.5'),
                        'perp':{'bid':price,'ask':price,'bid_qty':'100','ask_qty':'100','mark':price}})
                expected=[slot+h*3600000+3000 for h in range(0,1057,8)]
                events=[{'time_ms':t,'rate':'.0001','mark':'100'} for t in expected[1:]]
                costs={'option_fee_rate':'.00030' if stress else '.00024','perp_fee_rate':'.001' if stress else '.0005',
                       'perp_slippage':'.0004' if stress else '.0002','option_tick_worsening':'.01' if stress else '0'}
                try:
                    result=engine.ledger(records,capital=capital,option_quantity='.01',costs=costs,hedge_lot='.0001',
                       hedge_min_quantity='0',hedge_min_notional='0',expected_funding_times=expected,funding_events=events)
                    assert result['final']['closed'] and len(result['trace'])==1057
                    size=len(json.dumps(result,separators=(',',':')).encode())
                    profiles.append({'asset_label':asset,'capital_label':capital,'stress':stress,'status':result['status'],
                        'nominal_slots':len(result['trace']),'trades':len(result['trades']),'json_bytes':size})
                    all_books.append(result)
                except engine.ArithmeticScopeError as exc:
                    profiles.append({'asset_label':asset,'capital_label':capital,'stress':stress,'status':'arithmetic_unavailable',
                        'nominal_slots':1057,'reason':str(exc)})
    serialized=len(json.dumps(all_books,separators=(',',':')).encode())
    total=1057*(receipt_size+assembly_size)+serialized
    report={'kind':'synthetic_engineering_only','sources':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('options_policy_batch.py','options_policy_engine.py')},
      'max_body_fixture':{'source_slots':16,'bytes_each':8192,'raw_batch_bytes':raw_size,'receipt_json_bytes':receipt_size,'assembly_json_bytes':assembly_size},
      'episode_cases':profiles,'all_books_json_bytes':serialized,'routine_receipts_and_assemblies_and_books_bytes':total,
      'measured_routine_bytes_below_512MiB':total<512*1024**2,
      'all_eight_cases_cash_complete':len(all_books)==8 and all(p['status']=='conditional_cash_complete' for p in profiles),
      'practical_fixture_pass':len(all_books)==8 and all(p['status']=='conditional_cash_complete' for p in profiles) and total<512*1024**2,
      'limits':'1057hourly slots,8case labels, exact4096bit rational rejection. This measures one full-length invented fixture, not all accepted numbers, actual payloads, history-validation cost, transport, durable storage, metadata/funding retention or full lifecycle. No unattended process or observations.'}
    destination=root/'reviews/options-policy-size-proof-v3.json'
    with destination.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report))

if __name__=='__main__':main()
