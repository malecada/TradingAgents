"""Exact original scalar admission ancestry and cumulative-budget components only."""
from pathlib import Path
import json,hashlib,ast,copy,importlib.util
H=Path(__file__).resolve().parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');g=json.loads((H/'GATE4_DRAFT01.json').read_text());checks=[]
source=(CAP/'tradingagents/research/admission.py').read_text();tree=ast.parse(source);ad=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admit');loop=next(n for n in ad.body if isinstance(n,ast.While) and ast.unparse(n.test)=='parent is not None')
code=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'actual-admission-parent-loop','exec')
def parentcheck(experiments,identity):exec(code,{'seen':set(),'parent':identity,'experiments':experiments,'exp':experiments[identity]})
ids=['financial-wrapper-classification-eager-continue100-compatibility-20261004-01','financial-wrapper-classification-eager-predict-compatibility-20261004-01']
for i in ids:parentcheck(g['experiments'],i);checks.append('actual parent loop4-definition pass '+i)
try:parentcheck({i:g['experiments'][i] for i in ids},ids[0])
except ValueError as e:assert str(e)=='invalid parent ancestry';checks.append('exact2-definition gate refused')
else:raise AssertionError('missing ancestors accepted')
budget=CAP/'tradingagents/research/budget_extensions.py';spec=importlib.util.spec_from_file_location('_original_budget_scalar',budget);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);prior=[json.loads((p/'claim.json').read_text()) for p in (CAP/'research_runs').iterdir() if p.is_dir()];assert len(prior)==4
family=g['families']['synthetic-financial-wrapper'];e=g['experiments'][ids[0]]
def read(v):
 raw=(CAP/v['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==v['sha256'];return raw
assert m.effective_budget(CAP,g['program_id'],ids[0],e,family,prior,read)==20;assert len(prior)+family['prior_attempts']==4;checks.append('genuine20 extension reused with4 global actual claims independent of gate path')
for label,change in [('no extension',None),('lower extension',prior[0]['experiment'].get('cumulative_budget_extension'))]:
 bad=copy.deepcopy(e);bad.pop('cumulative_budget_extension',None)
 if change is not None:bad['cumulative_budget_extension']=change
 if change==e['cumulative_budget_extension']:continue
 try:m.effective_budget(CAP,g['program_id'],ids[0],bad,family,prior,read)
 except ValueError:checks.append('global previous20 downgrade refused '+label)
 else:raise AssertionError(label)
p=H/'preclaim_reuse01.py';sp=importlib.util.spec_from_file_location('_pure_refusal',p);n=importlib.util.module_from_spec(sp);sp.loader.exec_module(n);draft=json.loads((H/'PROOF_REUSE_CONTRACT_DRAFT01.json').read_text());oldq=json.loads((CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01/REQUEST_FINAL01.json').read_text());untrusted=copy.deepcopy(oldq);untrusted['expected_phase']='continue100';untrusted['identity']=ids[0]
for value,message in [(draft,'actual current source unavailable'),(dict(draft,consumer='foreign'),'fixed next consumer differs'),(dict(draft,current_source=n.REUSE_SOURCE),'new honest current/design source required')]:
 try:n._reuse_contract(value,untrusted,{},n.Reader())
 except n.Unavailable as e:assert str(e)==message;checks.append('exact invalid document predicate '+message)
 else:raise AssertionError(message)
# Pending recovery is an explicit null and cannot be a valid strict reference.
assert draft['outcome_recovery'] is None;assert 'actual completed100 outcome recovery still unavailable' in p.read_text();checks.append('actual100 recovery remains explicit required null')
(H/'SCALAR_CONTROLS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'actual_admission_or_permission':False,'real_claims_read_metadata_only':4,'actual_original_budget_api_return':20,'source_pins':{'admission':hashlib.sha256(source.encode()).hexdigest(),'budget':hashlib.sha256(budget.read_bytes()).hexdigest()}},sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(checks))
