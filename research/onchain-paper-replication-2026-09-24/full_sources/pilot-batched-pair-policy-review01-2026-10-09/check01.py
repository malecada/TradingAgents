import os,resource,signal,sys,json,hashlib,ast,copy
from pathlib import Path
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent;C=F/'pilot-batched-pair-policy-fix01-2026-10-09';S=R/'tradingagents/research/onchain_replication';sys.path.insert(0,str(R))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'MANIFEST01.json').read_bytes());assert sha(C/'MANIFEST01.json')=='84aefbd27855282214a2f097af2a706b02cd6dfd388bf9865beaa2f607457b80'
for n,v in m['selected'].items():assert sha(C/n)==v['sha256'] and sha(S/n)==v['baseline_sha256']
for n,h in m['unchanged_modules'].items():assert sha(S/n)==h
for n,h in m['evidence'].items():assert sha(C/n)==h
b=(C/'compact_mcm_batched.py').read_text();inverse=b.replace('from . import matching_checkpoint as engine, compact_policy','from . import matching_checkpoint as engine').replace("compact_policy.effective_matching(thaw(target.owner.matching),p['pair']),compact_policy.pair_policy(p['pair'])","thaw(target.owner.matching),p['pair']")
assert inverse==(S/'compact_mcm_batched.py').read_text()
t=(C/'real_pilot_import_caller.py').read_text();lines=t.splitlines(True);i=lines.index('            from . import compact_policy, matching_pair\n');assert ''.join(lines[:i]+lines[i+6:])==(S/'real_pilot_import_caller.py').read_text()
from tradingagents.research.onchain_replication import compact_policy,matching_pair,batched_numeric_reuse
from tradingagents.research.onchain_replication.batched_pair_executor import PairExecutor,CheckpointStop
from tradingagents.research.onchain_replication.contracts import AttributedGraph
import numpy as np
refs=json.loads((F/'real-data-pilot-full25-entry01-2026-10-09/gate01.json').read_bytes())['experiments']['eth-paper-real-data-end-to-end-resource-20261009-25']['inputs'];used={}
def read(role):
 r=refs[role];p=R/r['path'];assert sha(p)==r['sha256'];used[r['path']]=r['sha256'];return json.loads(p.read_bytes())
stage=read('compact_policy')['stage_policy'];pair=read('pair_policy')['limits'];plan=read('producer_plan')['producers']['original32'];config=plan['descriptor']['configs']['matching'];assert pair==stage['pair']
# Execute the exact five non-import statements of the new early branch.
ft=next(x for x in ast.parse(t).body if isinstance(x,ast.FunctionDef) and x.name=='admitted');branch=next(x for x in ast.walk(ft) if isinstance(x,ast.If) and isinstance(x.test,ast.Name) and x.test.id=='batched');code=compile(ast.Module(branch.body[1:6],[]),'<candidate early metadata>','exec')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def early(a,b,c=config):
 s={'compact_policy_input':'compact','pair_checkpoint_input':'pair','descriptor':{'configs':{'matching':c}}};values={'compact':{'stage_policy':{'pair':a}},'pair':{'limits':b}}
 ns=dict(compact_policy=compact_policy,matching_pair=matching_pair,s=s,ad=None,_read=lambda ad,k:values[k],require=require);exec(code,ns);return ns['effective'],ns['normalized']
eff,pol=early(pair,pair);assert eff['max_pair_entries']==8402640 and config['max_pair_entries']==4000000
assert {k:v for k,v in eff.items() if k!='max_pair_entries'}=={k:v for k,v in config.items() if k!='max_pair_entries'}
assert pol=={k:v for k,v in pair.items() if k!='max_pair_entries_override'}
failures={}
for label,mut in [('mismatch',lambda p:p.update(chunk_edges=p['chunk_edges']+1)),('unknown',lambda p:p.update(extra=1)),('boolean',lambda p:p.update(max_pair_entries_override=True)),('decrease',lambda p:p.update(max_pair_entries_override=3999999)),('layout',lambda p:p.update(checkpoint_layout={'format':'bad','chunk_entries':262144}))]:
 q=copy.deepcopy(pair);mut(q)
 try:early(q,pair if label=='mismatch' else q)
 except ValueError as e:failures[label]=str(e)
 else:raise AssertionError(label)
legacy={k:v for k,v in pair.items() if k not in ('checkpoint_layout','max_pair_entries_override')};assert early(legacy,legacy)==(config,legacy)
g=AttributedGraph(('synthetic',),np.zeros((1,2),dtype=np.float64),np.empty((2,0),dtype=np.int64),np.empty((0,2),dtype=np.float64),'1'*64,'synthetic')
def executor(c,p):return batched_numeric_reuse.NumericReuseExecutor(c,p,stage['schedule'],lambda *a:None,max_entries=2,max_retained_bytes=1048576,max_key_bytes=8192)
x=executor(config,pair);x.begin_batch()
try:x(g,g,'2'*64)
except ValueError as e:assert str(e)=='pair policy schema';red=str(e)
else:raise AssertionError('raw policy unexpectedly accepted')
assert x.poisoned and x.executor.reserved_bytes==0;x.close()
x=executor(eff,pol);x.begin_batch();a=x(g,g,'3'*64);ra=copy.deepcopy(x.last_receipt);b=x(g,g,'4'*64);rb=copy.deepcopy(x.last_receipt);x.end_batch();assert a==b and a[0]==0.5 and a[1]==48 and ra['mode']=='computed' and rb['mode']=='reused';assert x.executor.checkpoints==0 and x.executor.reserved_bytes==0;x.close()
schedule=copy.deepcopy(stage['schedule']);schedule.update(calls_per_checkpoint=1,operations_per_call=1);calls=[]
x=PairExecutor(eff,pol,schedule,lambda *args:calls.append(args))
try:x(g,g,'5'*64)
except CheckpointStop:pass
else:raise AssertionError('checkpoint stop missing')
assert x.poisoned and x.checkpoints==1 and len(calls)==1 and x.reserved_bytes==269229056
assert calls[0][5]==eff and calls[0][6]==pol
result={'decision':'accepted_source_only','selected':m['selected'],'manifest_sha256':sha(C/'MANIFEST01.json'),'unchanged_modules':m['unchanged_modules'],'metadata_evidence':used,'checks':{'full_literal_inverses':True,'original_refusal':red,'early_refusals':failures,'legacy_projection_unchanged':True,'score_iterations_convergence':a,'computed_reused':[ra['mode'],rb['mode']],'checkpoint_calls':len(calls),'checkpoint_reserved_bytes':x.reserved_bytes,'effective_capacity':eff['max_pair_entries']},'qualification':'Tiny immutable synthetic graph only; original arithmetic and Owner/persistence/schedule bodies unchanged. Explicitly honors already declared resource override; no empirical capacity, performance, complete pilot, actual Owner/Admission, external recovery or launch authorization. Early predicates are metadata compatibility checks; unchanged downstream validators remain authoritative.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['checks']))
