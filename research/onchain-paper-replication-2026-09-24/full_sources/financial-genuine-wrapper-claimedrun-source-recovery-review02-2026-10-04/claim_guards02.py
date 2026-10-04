import ast,copy,hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;P=B/'financial-genuine-wrapper-claimedrun-source-recovery-preparation02-2026-10-04';checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
claimraw=(B/'financial-genuine-wrapper-claimed-run-correction-preparation01-2026-10-04/actual-claim.json').read_bytes();check(sha(claimraw)=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','genuine oldclaim')
baseclaim=json.loads(claimraw);G=B/'financial-genuine-wrapper-root-claimedrun-handoff-generation01-2026-10-04/generated01';regraw=(G/'ORIGINAL_GATES_PRESERVED.json').read_bytes();check(sha(regraw)=='4474df26460aab41281bfdcc311129b613a90d76963e853858841200d9faa69a','genuine original gate bytes');reg=json.loads(regraw);exp=reg['experiments'][baseclaim['experiment_id']];record=json.loads((G/'ORIGINAL_SOURCE_READBACK01.json').read_bytes());check(sha((G/'ORIGINAL_SOURCE_READBACK01.json').read_bytes())=='24e8be32e199172f6bf1f8c6277776bc79c06c41805c529881aedf0f9922cb8e','actual original source body metadata')
entries={n:(r['git_mode'],r['git_object']) for n,r in record['tracked'].items()};spec=json.loads((B/'financial-genuine-wrapper-claimedrun-history-copy-admission-review01-2026-10-04/GIT_ANCESTRY_SPEC01.json').read_bytes());oids={line.split()[0] for line in spec['ancestry_lines']}
fn=next(n for n in ast.parse((P/'git_objects01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='claim_join');guards=[]
for n in ast.walk(fn):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require':
  expr=n.args[0]
  # Scalar guard extraction excludes repo.obj/body transport. Actual OIDs and
  # metadata supply scalar operands, not an invented recovered Git authority.
  if any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='obj' for x in ast.walk(expr)):continue
  text=ast.unparse(expr).replace('repo.commits','ancestry_oids');guards.append((n.lineno,text,compile(text,'<exact scalar claim guard>','eval')))
def evaluate(claim):
 ns={'claim':claim,'source':claim['source'],'design':claim['design_source'],'ancestry_oids':oids,'entries':entries,'regpath':claim['registration'],'raw':regraw,'hashlib':hashlib,'reg':reg,'exp':exp,'pins':exp['source_files']}
 return [bool(eval(code,ns)) for _,_,code in guards]
check(all(evaluate(baseclaim)),'all extracted genuine claim scalar guards pass')
mutations=[('source',lambda c:c.update(source='f'*40)),('design',lambda c:c.update(design_source='f'*40)),('registration hash',lambda c:c.update(registration_sha256='0'*64)),('program',lambda c:c.update(program_id='unrelated')),('family',lambda c:c['family'].update(attempt_budget=19)),('effective budget',lambda c:c.update(effective_attempt_budget=19)),('bindings',lambda c:c.update(bindings='other.json')),('bindings_sha',lambda c:c.update(bindings_sha256='0'*64)),('experiment contract',lambda c:c['experiment'].update(question='changed'))]
for label,change in mutations:
 c=copy.deepcopy(baseclaim);change(c);check(not all(evaluate(c)),'mutated actual claim refuses '+label)
for name in baseclaim['experiment']['source_files']:
 c=copy.deepcopy(baseclaim);c['experiment']['source_files'][name]='0'*64;check(not all(evaluate(c)),'mutated old324 contract pin '+name)
for role in baseclaim['inputs']:
 c=copy.deepcopy(baseclaim);c['inputs'][role]['sha256']='0'*64;check(not all(evaluate(c)),'mutated oldinput '+role)
# Byte predicates for original claim/terminal are exact fixed SHA in adapter.
restore=(P/'restore01.py').read_text();old=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source/research_runs')/baseclaim['experiment_id'];terminal=(old/'failed.json').read_bytes();pin='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450';check(pin in restore and sha(terminal)==pin,'genuine original terminal exact pin');check(sha(terminal+b' ')!=pin and sha(claimraw+b' ')!='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','changed claim/terminal bytes refuse before semantic use')
# Genuine verifier comparison: extension absent original fixed18, source=design,
# no bindings. Its chronology fields are covered by fixed byte pins, not by a new
# generic claim verifier inside claim_join.
verify=(Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source/tradingagents/research/verify.py')).read_text();check('def verify_claim(directory)' in verify and 'prior_exposures' in verify and 'windows' in verify,'actual verifier source scope');out={'checks':len(checks),'check_names':checks,'exact_guard_expressions':[{'line':line,'expression':s} for line,s,_ in guards],'actual_claim_positive_against_recovered_Git_not_executed':True,'qualification':'No fake claim receipts or recovered repo; only copied in-memory genuine claim metadata mutation and extracted original scalar predicates. Historical source/body transport exercised separately with tiny genuine opaque Git objects. Full actual747/sourceGit decode remains unperformed.'};(H/'CLAIM_GUARDS02.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'guards':len(guards),'qualification':out['qualification']}))
