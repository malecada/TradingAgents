"""Independent invented stream chronology and exact currency arithmetic; no network."""
import base64
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

DIRECTORY=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(DIRECTORY))
import triangle_stream as candidate


def message(symbol,values,update=1):
    return json.dumps({'stream':symbol.lower()+'@bookTicker','data':{'s':symbol,'u':update,**values}},separators=(',',':')).encode()


def replay(quotes, extra=(), end=540_000_000_000, reason='deadline'):
    records=[]
    events=[(0,message(symbol,row),1,True) for symbol,row in quotes.items()]+list(extra)
    for sequence,(stamp,raw,opcode,fin) in enumerate(events):
        records.append({'sequence':sequence,'kind':'inbound-frame','elapsed_ns':stamp,'body_bytes':len(raw),'body_sha256':hashlib.sha256(raw).hexdigest(),'body_base64':base64.b64encode(raw).decode(),'opcode':opcode,'fin':fin})
    return candidate.replay(candidate.default_spec(),iter(records),{'end_elapsed_ns':end,'end_reason':reason},{'status':'complete'})


def quote(price,size='1000000000'):
    return {'b':price,'a':price,'B':size,'A':size}


def oracle(quotes,direction,capital,fee):
    # Explicit independent paths, no helper outputs or helper path constants.
    path=([('BTCUSDT',True),('ETHBTC',True),('ETHUSDT',False)] if direction=='btc-eth' else [('ETHUSDT',True),('ETHBTC',False),('BTCUSDT',False)])
    amount=Fraction(capital);gross=Fraction(capital);sizes=[]
    fee=Fraction(0) if fee==0 else Fraction(1,1000)
    for symbol,buy in path:
        row=quotes[symbol];price=Fraction(Decimal(row['a' if buy else 'b']))
        size=Fraction(Decimal(row['A' if buy else 'B']))
        required=amount/price if buy else amount
        sizes.append(required<=size)
        amount=(amount/price if buy else amount*price)*(1-fee)
        gross=gross/price if buy else gross*price
    return {'positive':amount>capital,'sizes':sizes,'cash':float(amount-capital),'gross':float(gross/capital),'factor':float(amount/capital),'fees':float(gross-amount)}


def main():
    checks=[]
    fixtures={
        'exact_parity_float_false_positive':{'BTCUSDT':quote('1'),'ETHBTC':quote('13'),'ETHUSDT':quote('13')},
        'planted_positive':{'BTCUSDT':quote('100'),'ETHBTC':quote('0.1'),'ETHUSDT':quote('10.1')},
        'planted_negative':{'BTCUSDT':quote('100'),'ETHBTC':quote('0.1'),'ETHUSDT':quote('9.9')},
        'zero_visible_size':{'BTCUSDT':quote('1','0'),'ETHBTC':quote('1'),'ETHUSDT':quote('2')},
        'rounded_insufficient_size':{'BTCUSDT':quote('1','999.9999999999999999999'),'ETHBTC':quote('1'),'ETHUSDT':quote('2')},
    }
    failures=[]
    for name,quotes in fixtures.items():
        bins,summary=replay(quotes)
        for direction in ('btc-eth','eth-btc'):
            for capital in (1000,10000):
                for fee in (0,.001):
                    identifier=f"{direction}-{capital}-{'zero-fee' if fee==0 else '10bp'}"
                    expected=oracle(quotes,direction,capital,fee)
                    row=dict(zip(bins['columns'],bins['series'][identifier][0]))
                    actual=row['status']==2;wanted=expected['positive'] and all(expected['sizes'])
                    passed=(actual==wanted and abs(row['simple_cash_proxy_usdt']-expected['cash'])<1e-8
                            and abs(row['three_fees_usdt_equivalent']-expected['fees'])<1e-8
                            and [row[f'size_sufficient_leg{i}'] for i in (1,2,3)]==expected['sizes'])
                    checks.append({'fixture':name,'case':identifier,'passed':passed,'exact_qualified':wanted,'observed_qualified':actual})
                    if not passed:failures.append(checks[-1])
        assert sum(map(len,bins['series'].values()))==43200
        # A quote exactly one second old is admitted; next right boundary is stale.
        assert all(rows[9][0]!=0 and rows[10][0]==0 for rows in bins['series'].values())
    quotes=fixtures['planted_positive']
    bins,_=replay(quotes,end=200_000_000,reason='synthetic_disconnect')
    assert all(rows[0][0]!=0 and all(row[0]==0 for row in rows[1:]) for rows in bins['series'].values())
    for delta,first_available in ((100_000_000,0),(100_000_001,1)):
        late=message('ETHBTC',quotes['ETHBTC'])
        bins,_=replay({s:q for s,q in quotes.items() if s!='ETHBTC'},[(delta,late,1,True)])
        assert all(rows[first_available][0]!=0 and (first_available==0 or rows[0][0]==0) for rows in bins['series'].values())
    result={'scope':'Invented quotes only; independent Fraction wallets and source chronology; no actual capture or registration executed.', 'source_sha256':hashlib.sha256((DIRECTORY/'triangle_stream.py').read_bytes()).hexdigest(),'case_checks':len(checks),'checks':checks,'failures':failures,'passed':not failures,'chronology':'Right boundary, future update exclusion, exact-age admission, disconnect boundary/tail, all43200 subslots.'}
    (Path(__file__).parent/'triangle-stream-synthetic-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'failures':failures}))
    return bool(failures)

if __name__=='__main__':raise SystemExit(main())
