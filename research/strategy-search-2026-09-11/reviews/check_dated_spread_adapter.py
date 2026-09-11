"""Independent invented source-loss and direct HAC sandwich reconstruction."""
from pathlib import Path
import copy,hashlib,importlib.util,json,math,sys
import numpy as np
from scipy.stats import t
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'research/strategy-search-2026-09-11';sys.path.insert(0,str(P))
s=importlib.util.spec_from_file_location('spread_fixture_review',ROOT/'tests/research/test_dated_spread.py');fixture=importlib.util.module_from_spec(s);s.loader.exec_module(fixture)
import dated_spread_sources as sources
import dated_spread_run as runner
import dated_spread_statistics as statistics
cases=[];assertions=0
def numeric(a,b):
 global assertions
 assertions+=np.asarray(a).size
 assert np.allclose(a,b,atol=1e-10,rtol=1e-9),(a,b)
def bars(returns):
 result=[];previous=100.
 for i,r in enumerate(returns):
  current=previous*(1+r);result.append([1777593600000+i*86400000,str(previous),str(max(previous,current)+1),str(min(previous,current)-1),str(current),'1',1777593600000+(i+1)*86400000-1,'1',1,'1','1','0']);previous=current
 return result
i=np.arange(56);btc=.009*np.sin(i*.31)+.002*np.cos(i*.7);eth=.012*np.cos(i*.47)-.001*np.sin(i*.9)
y=.0003+.03*btc-.04*eth+.00007*np.sin(i*.61)
nav=1000*np.cumprod(1+y);br,er=bars(btc),bars(eth)
# Use independently reconstructed returns after source-literal conversion.
def returns(rows):return np.array([float(row[4])/(float(rows[k-1][4])if k else float(row[1]))-1 for k,row in enumerate(rows)])
X=np.column_stack([np.ones(56),returns(br),returns(er)]);Y=nav/np.r_[1000,nav[:-1]]-1
inv=np.linalg.inv(X.T@X);beta=inv@X.T@Y;u=Y-X@beta;xu=X*u[:,None];S=xu.T@xu
for lag in range(1,8):
 term=xu[lag:].T@xu[:-lag];S+=(1-lag/8)*(term+term.T)
cov=inv@S@inv;se=np.sqrt(np.diag(cov));critical=t.ppf(.9875,53)
actual=statistics.exposure(nav,1000,br,er);assert actual['status']=='complete'
numeric([actual['intercept'],actual['btc_beta'],actual['eth_beta']],beta);numeric(actual['covariance'],cov)
numeric([actual['btc_standard_error'],actual['eth_standard_error']],se[1:])
numeric(actual['btc_interval'],[beta[1]-critical*se[1],beta[1]+critical*se[1]]);numeric(actual['eth_interval'],[beta[2]-critical*se[2],beta[2]+critical*se[2]])
assert actual['observations']==56 and actual['hac_lags']==7 and actual['individual_confidence']==.975
cases.append({'name':'direct-Bartlett-HAC7-sandwich-and-t53-interval','passed':True})
for label,v,b,e in [('singular',nav,br,br),('zero-nav',np.r_[0.,nav[1:]],br,er),('missing-day',nav,br[:-1],er)]:
 assert statistics.exposure(v,1000,b,e)['status']=='unavailable';cases.append({'name':label,'passed':True})
inputs=fixture.synthetic_inputs();books,summary,audit,cells=runner.evaluate(inputs)
assert len(cells)==8 and len(audit['source_states'])==20 and summary['complete_primary']==8 and summary['complete_scalars']==16 and summary['complete_stresses']==72
cases.append({'name':'all-source-and-case-denominators','passed':True})
for label in ['carry_capture','archive_capture','mark_capture']:
 bad=dict(inputs);bad[label]=b'{}';b,s,a,c=runner.evaluate(bad)
 assert len(c)==8 and len(a['source_states'])==20 and s['unavailable_primary']==8 and s['unavailable_scalars']==16 and s['unavailable_stresses']==72
 cases.append({'name':'lost-'+label,'passed':True})
 ok=all(x['conditional_screens']['positive_cash_and_3pct_annual_base_and_stress']is None for x in s['cases'])
 cases.append({'name':'unknown-relevance-'+label,'passed':ok})
# One nonbenchmark source failure must not erase separately admitted spot data.
bad=dict(inputs);cc=json.loads(bad['carry_capture']);next(x for x in cc['requests']if x['id']=='btc-funding')['body_sha256']='0'*64;bad['carry_capture']=runner.encoded(cc)
b,s,a,c=runner.evaluate(bad);assert s['complete_primary']==4 and s['unavailable_primary']==4
cases.append({'name':'BTC-funding-failure-preserves-ETH-exposure','passed':all(x['statistics']['market_exposure']['status']=='complete'for x in s['cases']if x['asset']=='ETH')})
# Every source and denominator remains explicit when only a benchmark source fails.
bad=dict(inputs);cc=json.loads(bad['carry_capture']);next(x for x in cc['requests']if x['id']=='btc-spot')['body_sha256']='0'*64;bad['carry_capture']=runner.encoded(cc)
b,s,a,c=runner.evaluate(bad);assert all(x['statistics']['market_exposure']['status']=='unavailable'for x in s['cases']);assert len(a['source_states'])==20
cases.append({'name':'missing-spot-blocks-joint-exposure','passed':True})
# Canonical endpoint filtering retains before/after counts, excluding early June26.
bad=dict(inputs);cc=json.loads(bad['carry_capture']);ca=json.loads(bad['carry_admission'])
import base64
for rec in cc['requests']:
 if rec['kind']!='funding':continue
 rows=json.loads(base64.b64decode(rec['body_base64']));rows[90]['fundingTime']-=5000;rows[258]['fundingTime']-=5000;rows[258]['fundingRate']='100'
 raw=runner.encoded(rows);rec.update(body_base64=base64.b64encode(raw).decode(),body_sha256=hashlib.sha256(raw).hexdigest(),body_bytes=len(raw))
 req=next(x for x in sources.carry.frozen_request_spec()['requests']if x['id']==rec['id'])
 normal={'id':rec['id'],**sources.carry.admit_response(req,raw),'coverage':sources.carry.funding_coverage(rows)}
 ca['cells']=[normal if c['id']==rec['id']else c for c in ca['cells']]
bad['carry_capture']=runner.encoded(cc);bad['carry_admission']=runner.encoded(ca)
data,a=sources.readmit(bad)
for asset in ['BTC','ETH']:
 assert len(data[asset]['funding'])==168 and data[asset]['funding'][0]['fundingTime']==1777593595000 and all(row['fundingRate']!='100'for row in data[asset]['funding'])
 assert a['clipping'][asset]['funding']['canonical_before']==90 and a['clipping'][asset]['funding']['canonical_after']==15
cases.append({'name':'canonical90-258-boundary-independent-of-raw-window','passed':True})
report={'passed':all(x['passed']for x in cases),'cases':cases,'direct_statistic_assertions':int(assertions),'sources':{name:hashlib.sha256((P/name).read_bytes()).hexdigest()for name in ['dated_spread_sources.py','dated_spread_statistics.py','dated_spread_run.py']},'scope':'Invented raw source envelopes and planted NAV/benchmarks only. No actual inputs, financial experiment, network or ledger mutations. Direct OLS/Bartlett-HAC covariance and Student-t interval reconstruction does not use statsmodels expected values.'}
(Path(__file__).parent/'dated-spread-adapter-synthetic-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed']else 1)
