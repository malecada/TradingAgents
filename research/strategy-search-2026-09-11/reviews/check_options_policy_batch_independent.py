"""Synthetic clock/dependency attacks using the author's invented receipt builder."""
import importlib.util
import json
from pathlib import Path

root=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('synthetic_fixture',root/'tests/research/test_options_policy_batch.py')
test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test)
cases=[]
def verify(name,mutation,expected):
    rows=test.fixture();mutation(rows);out=test.run(rows)
    assert len(out['sources'])==16
    expected(out);cases.append(name)

def no_hedge(out):
    assert out['records']['BTC']['hedge_available'] is False
    assert out['records']['ETH']['hedge_available'] is True

# These timestamps would have passed the original action-clock future check.
verify('T after its own receipt',lambda r:test.body(r,'btc-perp-depth',lambda b:b.update(T=test.SLOT+4000,E=test.SLOT+4001)),no_hedge)
# Futures offset interval is [-200,0]: local T interval becomes [1250,1450],
# while retrieval+1000 is1300. Earliest alone is insufficient for admission.
verify('upper interval future bound',lambda r:test.body(r,'btc-perp-depth',lambda b:b.update(T=test.SLOT+1250,E=test.SLOT+1251)),no_hedge)
verify('E precedes T',lambda r:test.body(r,'btc-perp-depth',lambda b:b.update(E=b['T']-1)),no_hedge)
verify('E future despite current T',lambda r:test.body(r,'btc-perp-depth',lambda b:b.update(E=test.SLOT+2000)),no_hedge)

def absent_delta(out):
    r=out['records']['BTC']
    assert r['hedge_available'] is False and r['exit_available'] is True
    assert r['valuation_available'] is True
    assert r['call']['mark']=='9.5'
verify('missing delta retains valuation',lambda r:test.body(r,'btc-call-mark',lambda b:b[0].pop('delta')),absent_delta)
def absent_mark(out):
    r=out['records']['BTC']
    assert r['hedge_available'] is True and r['exit_available'] is True
    assert r['valuation_available'] is False
    assert r['call']['delta']=='.5' or r['call']['delta']=='0.5'
verify('missing mark retains hedge delta',lambda r:test.body(r,'btc-call-mark',lambda b:b[0].pop('markPrice')),absent_mark)
def hashbad(out):
    assert out['sources']['btc-call-depth']['status']=='unavailable'
    assert out['records']['BTC']['exit_available'] is False
    assert out['records']['ETH']['exit_available'] is True
verify('bad hash isolated to dependent asset',lambda r:next(x for x in r if x['id']=='btc-call-depth').update(body_sha256='0'*64),hashbad)
report={'passed':True,'cases':cases,'scope':'Invented receipts only; independent expected timing/dependency assertions. No transport or empirical inputs.'}
Path(__file__).with_name('options-policy-batch-independent-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
