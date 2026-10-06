"""Synthetic interval times; no empirical workload or authority construction."""
from pathlib import Path
import json,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
old=ROOT/'tradingagents/research/onchain_replication/imported_authority_interval.py'
new=HERE/'candidate/imported_authority_interval.py'
def load(p):
    m=types.ModuleType('fixture_interval');exec(compile(p.read_bytes(),str(p),'exec'),vars(m));return m
modules=[load(old),load(new)]
def run(m,age,duration,first=False,callback_fatal=False):
    clock=[0.];reads=[0]
    def now():reads[0]+=1;return clock[0]
    selected={'schema_version':1,'kind':m.KIND,'live_interval_ms':1000,'fingerprint_interval_ms':2000,'full_interval_ms':10000,'max_stale_ms':30000,'max_calls_between_full':100,'assumption':m.ASSUMPTION}
    x=m.Interval(selected,clock=now)
    if not first:x.validate(lambda:None,lambda:None,lambda:None,boundary=True)
    clock[0]=age
    primary=ValueError('original callback fatal')
    def full():
        clock[0]+=duration
        if callback_fatal:raise primary
    try:x.validate(full,lambda:None,lambda:None,boundary=True);return {'pass':True,'clock_reads':reads[0],'closed':x.closed,'full':x.full}
    except ValueError as error:return {'pass':False,'clock_reads':reads[0],'closed':x.closed,'full':x.full,'reason':str(error),'notes':getattr(error,'__notes__',[]),'same_fatal':error is primary}
cases=[]
for args in [(22.,9.,False,False),(22.,7.,False,False),(0.,31.,True,False),(22.,1.,False,True),(31.,0.,False,False)]:
    a,b=[run(m,*args) for m in modules];aa={k:v for k,v in a.items() if k!='notes'};bb={k:v for k,v in b.items() if k!='notes'};assert aa==bb
    if args in [(22.,9.,False,False),(0.,31.,True,False)]:
        assert not a['notes'] and len(b['notes'])==1
        assert f'full_callback_seconds={args[1]!r}' in b['notes'][0]
        assert f'pre_callback_age_seconds={args[0]!r}' in b['notes'][0]
    else:assert a.get('notes',[])==b.get('notes',[])
    cases.append({'args':args,'original':a,'candidate':b})
oldline='                full_check();full_done=self.now();freshness(full_done)\n'
newlines='''                full_check();full_done=self.now()
                try:freshness(full_done)
                except ValueError as error:
                    # Diagnostic only: reuse actual already sampled times. No
                    # extra clock read, refresh, threshold or exception change.
                    origin=start if old_full is None else old_full
                    error.add_note('import lease full boundary timing: '
                        f'full_callback_seconds={full_done-now!r}; '
                        f'pre_callback_age_seconds={now-origin!r}; '
                        f'total_age_seconds={full_done-origin!r}')
                    raise
'''
assert new.read_text().replace(newlines,oldline)==old.read_text()
result={'status':'PASS','cases':cases,'exact_inverse':True,'qualification':'Synthetic scheduler clock only. Original exception reason, poison state, full timestamp and clock-read count unchanged; only stale full_done exception receives diagnostic note. Actual next-run timings remain unknown.'}
(HERE/'DIAGNOSTIC_RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS five diagnostic cases and exact inverse')
