"""One concrete same-family successor registration; requires actual reviewed recovery."""
import ast,copy,hashlib,json,os,subprocess
from pathlib import Path
root=Path.cwd();f=root/'research/onchain-paper-replication-2026-09-24/full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04';r=f/'financial-wrapper-continuation-successor-review01-2026-10-05';cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01');directory=cap/'fixture_inputs/financial_wrapper_continuation_successor01';registration=directory/'gates.json';identity='financial-wrapper-classification-eager-continue100-resource-successor-20261005-01';oldid='financial-wrapper-classification-eager-continue100-compatibility-20261004-01';oldreg='fixture_inputs/financial_wrapper_continuation01/gates.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):
 with p.open('xb') as w:w.write(b)
def git(args):return subprocess.run(['git',*args],cwd=cap,capture_output=True,check=True).stdout
assert not registration.exists() and not (cap/'research_runs'/identity).exists() and not (parent/'attempt').exists()
assert git(['rev-parse','HEAD']).decode().strip()=='d4c81c0961342bfe4c5771aabbef1d46a14cffb8'
oldraw=(cap/oldreg).read_bytes();assert sha(oldraw)=='1f96b8efd7fdd468cb9ef87059c5bba026c4aa238f21580ed3ae6e961146e18d';gate=json.loads(oldraw);original=copy.deepcopy(gate['experiments']);experiment=copy.deepcopy(original[oldid]);inputs=experiment['inputs'];inputs['successor_original_closure']=copy.deepcopy(inputs['source_closure'])
recovery=(r/'SOURCE_RECOVERY_PROOF01.json').read_bytes();proof=json.loads(recovery);expected=json.loads((f/'financial-wrapper-continuation-successor-preparation02-2026-10-05/PROOF_FIELDS_DRAFT01.json').read_bytes())['required_future_fields']['continuation_source_successor_recovery'];assert proof==expected
put(directory/'successor-recovery.json',recovery)
for role,name in {'wrapper_plan':'continue-plan.json','source_closure':'source_closure.json','continuation_source_successor':'successor.json','continuation_source_successor_review':'successor-review.json','continuation_source_successor_recovery':'successor-recovery.json','successor_refusal':'refusal.json'}.items():
 p=directory/name;inputs[role]={'dataset':'synthetic','path':p.relative_to(cap).as_posix(),'sha256':sha(p.read_bytes())}
assert len(inputs)==34
edge=json.loads((directory/'successor.json').read_bytes());prefix='tradingagents/research/onchain_replication/'
for name in ('operational_source_compatibility.py','financial_wrapper_fixture.py'):assert sha((cap/(prefix+name)).read_bytes())==edge['installed'][prefix+name]
names=git(['ls-tree','-r','--name-only','HEAD']).decode().splitlines();assert len(names)==360
names=sorted(set(names)|{x.relative_to(cap).as_posix() for x in directory.iterdir() if x.is_file()});assert len(names)==366
experiment['source_files']={name:sha((cap/name).read_bytes()) for name in names};experiment['question']+=' Same-family continuation source successor after independently recovered terminal no-claim resource refusal; no numerical or cap change.'
gate['experiments'][identity]=experiment;assert len(gate['experiments'])==5 and all(gate['experiments'][k]==v for k,v in original.items());put(registration,enc(gate))
assert experiment['parent']=='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01' and gate['families']==json.loads(oldraw)['families']
paths=[prefix+'operational_source_compatibility.py',prefix+'financial_wrapper_fixture.py']+[x.relative_to(cap).as_posix() for x in sorted(directory.iterdir()) if x.is_file()]
git(['add','--',*paths]);git(['diff','--cached','--check']);git(['commit','-m','engineering: register same-family continuation resource successor'])
source=git(['rev-parse','HEAD']).decode().strip();tracked=git(['ls-tree','-r','--name-only','HEAD']).decode().splitlines();assert len(tracked)==367 and set(tracked)==set(experiment['source_files'])|{registration.relative_to(cap).as_posix()}
binding={'source':source,'registration_sha256':sha(registration.read_bytes()),'source_map_sha256':sha(enc(experiment['source_files'])),'source_count':366,'tracked_count':367}
caller=(parent/'parent01.py').read_bytes();put(c/'SUCCESSOR_PARENT_PRE_SOURCE_BINDING01.py',caller);text=caller.decode();assert text.count('SOURCE_BINDING=None')==1;text=text.replace('SOURCE_BINDING=None','SOURCE_BINDING='+repr(binding));ast.parse(text);(parent/'parent01.py').write_text(text)
contract_path=parent/'proof_reuse_contract01.json';oldcontract=contract_path.read_bytes();put(c/'SUCCESSOR_PROOF_REUSE_UNBOUND01.json',oldcontract);contract=json.loads(oldcontract);assert contract['current_source'] is None;contract['current_source']=source;contract_path.write_bytes(enc(contract))
q=json.loads((parent/'REQUEST_DRAFT01.json').read_bytes());q.update(source=source,design_source=source,registration_sha256=binding['registration_sha256'],source_files=experiment['source_files'],input_hashes={k:v['sha256'] for k,v in inputs.items()},caller_sha256=sha((parent/'parent01.py').read_bytes()),helper_hashes={name:sha((parent/name).read_bytes()) for name in ('supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json','preclaim01.py','proof_reuse_contract01.json')});put(parent/'REQUEST_SOURCE_BOUND_DRAFT01.json',enc(q))
record={'schema_version':1,'source':source,'design_source':source,'registration':registration.relative_to(cap).as_posix(),'registration_sha256':binding['registration_sha256'],'source_count':366,'tracked_count':367,'source_map_sha256':binding['source_map_sha256'],'input_count':34,'unchanged_old_definitions':4,'added_definitions':1,'family_budget':gate['families'][experiment['family']],'recovery_proof_sha256':sha(recovery),'caller_sha256':q['caller_sha256'],'claim':False,'pending':'genuine read-only admission, current full recovery, final exact release and preflight'}
put(c/'SUCCESSOR_GATE_ADOPTION01.json',enc(record));print(json.dumps(record,sort_keys=True))
