"""Finite metadata audit; no research imports or authority admission."""
from pathlib import Path
import json,hashlib,ast
P=Path(__file__).resolve().parent;R=P.parents[3]
S=R/'tradingagents/research/onchain_replication/batched_continuation.py'
parent='eth-paper-real-data-end-to-end-resource-20261012-39';D=R/'research_runs'/parent
G=R/'research_artifacts/onchain_representations/ada9fbd6764c8dc113bf837ff9cc71296dd9c09e6af2a9da4d7a841a2e91329f'/parent/'compact/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba'
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();assert len(b)<2*1024*1024
 return json.loads(b),dict(path=str(p.relative_to(R)),bytes=len(b),sha256=digest(b))
failed,fp=read(D/'failed.json');claim,cp=read(D/'claim.json');assert failed['claim_sha256']==cp['sha256'];assert failed['status']=='failed';assert failed['experiment_id']==claim['experiment_id']==parent
costs=('checkpoint_attempts','checkpoint_reserved_bytes','completed_operations','advance_calls','abandoned_call_operation_limit')
def matches(value,path=''):
 result=[]
 if isinstance(value,dict):
  for k,v in value.items():
   if k in costs or k in ('spent_counters','retained_partial_work','parent_experiment'):result.append(dict(path=path+'/'+k,value=v))
   result+=matches(v,path+'/'+k)
 elif isinstance(value,list):
  for i,v in enumerate(value):result+=matches(v,path+'/'+str(i))
 return result
outputs=[];pins=[fp,cp]
for name,sha in failed['output_sha256'].items():
 value,pin=read(D/'outputs'/name);assert sha==pin['sha256'];pins.append(pin);outputs.append(dict(**pin,counter_fields=matches(value)))
commit,kp=read(G/'matching/00000015.prefix.json');summary,sp=read(G/'stream/numeric-batches/000000000015.json');pins.extend((kp,sp));assert commit['summary_sha256']==sp['sha256'];assert commit['stop']==summary['stop']==65536
prefix_costs={k:commit[k] for k in costs[:2]}|commit['operation_counters']
phase,pp=read(D/'outputs/phase-timing.json')
assert phase['authority'] is False
review,rp=read(R/'research/onchain-paper-replication-2026-09-24/full_sources/pilot39-outcome-increment37-review-2026-10-12/RETURN_REVIEW01.json');pins.append(rp)
# Exact existing membership predicate, extracted without executing _authority/Run.
tree=ast.parse(S.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_authority')
statement=next(n for n in fn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(x,ast.Constant) and x.value=='actual parent spent output required' for x in n.value.args))
derived=json.dumps(dict(parent_experiment=parent,spent_counters=prefix_costs,retained_partial_work={}),sort_keys=True,separators=(',',':')).encode()
def require(ok,why):
 if not ok:raise ValueError(why)
try:
 exec(compile(ast.Module(body=[statement],type_ignores=[]),str(S),'exec'),dict(require=require,digest=digest,accounting_raw=derived,failed=failed,review={'parent_accounting_sha256':digest(derived)}))
except ValueError as e:refusal=str(e)
else:raise AssertionError('unsealed derived accounting unexpectedly admitted')
(P/'BASELINE_batched_continuation.py').write_bytes(S.read_bytes())
result=dict(status='WITHHELD_NO_AUTHORITATIVE_TERMINAL_NUMERIC_ACCOUNTING',parent=parent,original_failed_outputs=outputs,required_counter_names=costs,last_completed_prefix=dict(**kp,stop=65536,spent_lower_bound=prefix_costs),last_summary=sp,phase_numeric_counts_match_last_summary=phase['numeric_counts']==summary['phase_totals']['numeric_counts'],phase_authority=phase['authority'],existing_reader_derived_body_refusal=refusal,derived_body_is_not_written_or_registered=True,evidence=pins,source=dict(path=str(S.relative_to(R)),sha256=digest(S.read_bytes())))
(P/'AUDIT01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'outputs_checked':len(outputs),'outputs_containing_required_fields':sum(bool(x['counter_fields']) for x in outputs),'prefix_costs':prefix_costs,'refusal':refusal},indent=2))
