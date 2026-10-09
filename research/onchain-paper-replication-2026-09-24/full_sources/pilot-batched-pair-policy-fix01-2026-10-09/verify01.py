"""Actual registered metadata and real numeric executor; one-node synthetic graphs only."""
import os,resource,signal,sys,json,hashlib,copy,ast,difflib
from pathlib import Path
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
H=Path(__file__).resolve().parent;ROOT=H.parents[3];S=ROOT/'tradingagents/research/onchain_replication';sys.path.insert(0,str(ROOT))
import numpy as np
from tradingagents.research.onchain_replication import compact_policy,matching_pair,batched_numeric_reuse as reuse
from tradingagents.research.onchain_replication.contracts import AttributedGraph
j=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
gate=H.parent/'real-data-pilot-full25-entry01-2026-10-09/gate01.json';inputs=j(gate)['experiments']['eth-paper-real-data-end-to-end-resource-20261009-25']['inputs'];pins={}
def read(role):
 ref=inputs[role];p=ROOT/ref['path'];assert sha(p)==ref['sha256'];pins[role]=ref;return j(p)
p=read('compact_policy')['stage_policy'];limits=read('pair_policy')['limits'];assert limits==p['pair'];plan=read('producer_plan')['producers']['original32'];config=plan['descriptor']['configs']['matching'];original=copy.deepcopy((config,p))
g=AttributedGraph(('x',),np.zeros((1,2),dtype=np.float64),np.empty((2,0),dtype=np.int64),np.empty((0,2),dtype=np.float64),'1'*64,'x')
def make(c,pol,cb=lambda *args:None):return reuse.NumericReuseExecutor(c,pol,p['schedule'],cb,max_entries=2,max_retained_bytes=1024*1024,max_key_bytes=8192)
x=make(config,p['pair']);x.begin_batch()
try:x(g,g,'2'*64)
except ValueError as e:assert str(e)=='pair policy schema';red=str(e)
else:raise AssertionError('expected original route refusal')
assert x.poisoned and x.executor.checkpoints==0 and x.executor.reserved_bytes==0;x.close()
effective=compact_policy.effective_matching(config,p['pair']);normalized=compact_policy.pair_policy(p['pair']);assert effective['max_pair_entries']==8402640 and config['max_pair_entries']==4000000
assert {k:v for k,v in effective.items() if k!='max_pair_entries'}=={k:v for k,v in config.items() if k!='max_pair_entries'}
assert set(p['pair'])-set(normalized)=={'max_pair_entries_override'} and normalized['checkpoint_layout']==p['pair']['checkpoint_layout']
x=make(effective,normalized);x.begin_batch();one=x(g,g,'3'*64);first=copy.deepcopy(x.last_receipt);two=x(g,g,'4'*64);second=copy.deepcopy(x.last_receipt);x.end_batch();assert one==two and first['mode']=='computed' and second['mode']=='reused';assert x.executor.checkpoints==0 and x.executor.reserved_bytes==0;x.close()
refused={}
for label,change in [('unknown',lambda v:v.update(unknown=1)),('bool_override',lambda v:v.update(max_pair_entries_override=True)),('decreased_override',lambda v:v.update(max_pair_entries_override=1)),('bad_layout',lambda v:v.update(checkpoint_layout={'format':'wrong','chunk_entries':262144}))]:
 v=copy.deepcopy(p['pair']);change(v)
 try:compact_policy.effective_matching(config,v)
 except ValueError as e:refused[label]=str(e)
 else:raise AssertionError(label)
legacy={k:v for k,v in normalized.items() if k!='checkpoint_layout'};assert compact_policy.pair_policy(legacy)==legacy and compact_policy.effective_matching(config,legacy)==config
assert (config,p)==original
# Exact source inverses; numerical executor/cache/checkpoint modules untouched.
new=(H/'compact_mcm_batched.py').read_text();old=(S/'compact_mcm_batched.py').read_text()
new=new.replace('from . import matching_checkpoint as engine, compact_policy','from . import matching_checkpoint as engine').replace("compact_policy.effective_matching(thaw(target.owner.matching),p['pair']),compact_policy.pair_policy(p['pair'])","thaw(target.owner.matching),p['pair']")
assert new==old
caller=(H/'real_pilot_import_caller.py').read_text();lines=caller.splitlines(True);start=next(i for i,l in enumerate(lines) if l=='            from . import compact_policy, matching_pair\n');assert ''.join(lines[:start]+lines[start+6:])==(S/'real_pilot_import_caller.py').read_text()
for name in ('compact_mcm_batched.py','real_pilot_import_caller.py'):
 ast.parse((H/name).read_text());(H/(name+'.inverse.patch')).write_text(''.join(difflib.unified_diff((H/name).read_text().splitlines(True),(S/name).read_text().splitlines(True))))
result=dict(status='PASS_SYNTHETIC_ENGINEERING_ONLY',registered_metadata=pins,original_refusal=red,original_type=type(p['pair']).__name__,extra_capacity_field=8402640,original_capacity=4000000,effective_capacity=effective['max_pair_entries'],score=one,first_receipt=first,second_receipt=second,refusals=refused,literal_inverses=True,real_graphs=False,Run_Owner_Binding=False)
(H/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'original_refusal':red,'score':one,'computed_reused':[first['mode'],second['mode']],'refusals':refused}))
