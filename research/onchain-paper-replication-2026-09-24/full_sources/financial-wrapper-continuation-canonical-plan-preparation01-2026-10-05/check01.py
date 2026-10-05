"""Actual metadata and original extracted alias predicate only; no full preflight."""
import ast,copy,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01/preclaim01.py')
sha=lambda b:hashlib.sha256(b).hexdigest()
rel='fixture_inputs/financial_wrapper_continuation01/'
old=json.loads((CAP/(rel+'gates.json')).read_bytes());new=json.loads((H/'gates.json').read_bytes());prior=json.loads((CAP/(rel+'prior.json')).read_bytes());fixed=json.loads((H/'prior.json').read_bytes())
ID='financial-wrapper-classification-eager-continue100-compatibility-20261004-01';PRED='financial-wrapper-classification-eager-predict-compatibility-20261004-01'
policyref=old['experiments'][ID]['inputs']['operational_source_compatibility'];policy=json.loads((CAP/policyref['path']).read_bytes())
tree=ast.parse(P.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_historical');loop=next(n for n in function.body if isinstance(n,ast.For));definitions=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('Unavailable','require')]
module=ast.Module(body=definitions+[loop],type_ignores=[]);code=compile(ast.fix_missing_locations(module),str(P),'exec');rows=[]
def exercise(value):
 env={'prior':value,'hist':policy['historical']}
 exec(code,env)
try:exercise(prior)
except ValueError as e:assert str(e)=='exact historical alias linkage differs';rows.append('actual original RED')
else:raise AssertionError('old metadata unexpectedly accepted')
exercise(fixed);rows.append('corrected metadata GREEN using unchanged actual loop')
for key in ('claim_input','terminal_input','checkpoint_input','parent_job_input','parent_plan_input'):
 bad=copy.deepcopy(fixed);bad[key]='wrong-alias'
 try:exercise(bad)
 except ValueError:rows.append('unchanged refusal '+key)
 else:raise AssertionError(key)
assert {k:v for k,v in fixed.items() if k!='parent_plan_input'}=={k:v for k,v in prior.items() if k!='parent_plan_input'};rows.append('prior only canonical alias changed')
for identity,experiment in old['experiments'].items():
 updated=new['experiments'][identity]
 if identity not in (ID,PRED):assert updated==experiment;rows.append('historical definition exact '+identity);continue
 expected=copy.deepcopy(experiment);expected['source_files'][rel+'prior.json']=sha((H/'prior.json').read_bytes())
 if identity==ID:
  expected['inputs']['historical_plan']=expected['inputs'].pop('historical_wrapper_plan');expected['inputs']['wrapper_prior']['sha256']=sha((H/'prior.json').read_bytes())
 assert updated==expected;rows.append('exact finite new consumer delta '+identity)
assert len(new['experiments'][ID]['inputs'])==29 and len(new['experiments'][PRED]['inputs'])==17;rows.append('actual29/17 role counts retained')
assert new['experiments'][PRED]['inputs']['wrapper_prior']=={'dataset':'synthetic','path':None,'sha256':None};rows.append('prediction future prerequisite remains null')
assert {k:v for k,v in old.items() if k!='experiments'}=={k:v for k,v in new.items() if k!='experiments'};rows.append('dataset/program/family/budget unchanged')
ref=new['experiments'][ID]['inputs']['historical_plan'];raw=(CAP/ref['path']).read_bytes();assert sha(raw)==ref['sha256']=='15fd8a363806a15b68a6ff23b029847727b5ddbeb9e945454a1f9b5d4c4ac729'
claim=json.loads((CAP/new['experiments'][ID]['inputs']['historical_claim']['path']).read_bytes());job=json.loads((CAP/new['experiments'][ID]['inputs']['historical_execution_job']['path']).read_bytes());assert ref==claim['inputs'][job['payload']['plan_input']];rows.append('canonical role exact genuine claim-selected original plan')
inverse=json.loads((H/'INVERSE01.json').read_bytes())
for row in inverse['files']:
 raw=(H/row['candidate_path']).read_bytes()
 for edit in reversed(inverse['literal_replacements'][row['candidate_path']]):assert raw.count(edit['new'].encode())==edit['count'];raw=raw.replace(edit['new'].encode(),edit['old'].encode())
 assert sha(raw)==row['original_sha256'] and raw==Path(row['original_path']).read_bytes();rows.append('full byte inverse '+row['candidate_path'])
print(json.dumps({'passed':len(rows),'checks':rows,'actual_preclaim_source_sha256':sha(P.read_bytes()),'extracted_alias_loop_AST':ast.dump(loop,include_attributes=False),'original_plan_ref':ref,'actual_plan_bytes':len((CAP/ref['path']).read_bytes()),'full_public_preflight':False,'new_admission_or_claim':False},sort_keys=True))
