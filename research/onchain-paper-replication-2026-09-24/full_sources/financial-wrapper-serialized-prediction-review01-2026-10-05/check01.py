"""Read-only review of finite metadata bindings; output remains in review ownership."""
import ast,hashlib,importlib.util,io,json,os,subprocess,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
P=BASE/'financial-wrapper-serialized-prediction-preparation01-2026-10-05'
OLD=BASE/'financial-wrapper-prediction-successor-source01-2026-10-05'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PREFIX='tradingagents/research/onchain_replication/'
def sha(x):return hashlib.sha256(x).hexdigest()
def obj(p):return json.loads(p.read_bytes())
def authenticated(r):
 p=Path(r['path']);b=p.read_bytes();assert sha(b)==r['sha256'];return obj(p)
manifest_raw=(P/'MANIFEST01.json').read_bytes()
assert sha(manifest_raw)=='b7e5adfac87e0774f70c3b8181b06fceb77b59a65c0f6ebf937a20a871726017'
manifest=json.loads(manifest_raw)
for member in manifest['members']:
 p=P/member['path'];b=p.read_bytes();assert len(b)==member['bytes'] and sha(b)==member['sha256'] and p.stat().st_mode&0o777==member['mode']
draft=obj(P/'DRAFT_INPUTS02.json');edge=draft['prediction_edge_candidate'];identity=draft['prediction_identity'];cell=edge['consumer']['cell_id']
namespace=[CAP/'research_runs'/identity,CAP/'research_artifacts/financial_wrapper_engineering'/identity,CAP/'research_artifacts/onchain_fit_cells'/sha(cell.encode())/identity]
assert all(not os.path.lexists(p) for p in namespace)
processes=subprocess.run(['ps','-eo','pid,ppid,stat,args'],check=True,text=True,capture_output=True).stdout.splitlines()
active=[r for r in processes if any(s in r for s in ['financial_wrapper_fixture','native_guard.py','continue100-serialized-storage-root-launch','predict-serialized-storage-root-launch']) and not any(s in r for s in ['check01.py','bash -lc','ps -eo'])]
assert not active,active
claim=authenticated(draft['actual_parent_claim']);policy=authenticated(draft['actual_parent_policy']);closure=authenticated(draft['actual_parent_closure'])
obs=draft['observed_parent_completion'];terminal=authenticated(obs['complete_terminal']);complete=authenticated(obs['fit_completion']);checkpoint=authenticated(obs['checkpoint_manifest'])
assert claim['source']==claim['design_source']==draft['actual_parent_source']
assert terminal['status']=='complete' and terminal['experiment_id']==draft['parent'] and terminal['claim_sha256']==draft['actual_parent_claim']['sha256']
assert not os.path.lexists(Path(obs['complete_terminal']['path']).with_name('failed.json'))
assert complete['epochs']==100 and complete['checkpoint']==obs['checkpoint_manifest']['path'] and complete['sha256']==obs['checkpoint_manifest']['sha256']
assert checkpoint['provenance']==obs['original_checkpoint_provenance']
member=obs['checkpoint_members'][0];raw=Path(member['path']).read_bytes();assert len(raw)==member['bytes']==497712 and sha(raw)==member['sha256']=='920fda8e886d21e55cf18a357f6040b877ffdb06a905724cf84d109b5cdbd076'
assert checkpoint['members']=={'state.pt':{'size':len(raw),'sha256':sha(raw)}}
before=policy['installed'];after=edge['installed'];changed={k for k in before if before[k]!=after[k]}
assert before==closure['installed'] and set(before)==set(after) and changed=={PREFIX+n for n in ['operational_source_compatibility.py','financial_wrapper_fixture.py','evaluation.py']}
assert all(claim['experiment']['source_files'].get(k)==v for k,v in before.items())
assert checkpoint['provenance']['source_hashes']==sorted(set(before.values()))
for n in ['financial_wrapper_fixture.py','evaluation.py']:assert (P/n).read_bytes()==(OLD/n).read_bytes()
# Accepted refusal-chain bodies are reused by AST identity, without re-executing tests.
def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a=functions(CAP/PREFIX/'operational_source_compatibility.py');b=functions(P/'operational_source_compatibility.py')
assert all(a[n]==b[n] for n in ['validate_successor','successor_context','validate_terminal_refusal','validate_successor_reference'])
assert all(v is None for v in draft['unresolved'].values())
# Execute only the one changed-binding test; accepted nine-method baseline is not rerun.
spec=importlib.util.spec_from_file_location('reviewed_prediction_test',P/'test_prediction.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([module.Prediction('test_new_actual_binding_and_unresolved_draft')]))
assert result.wasSuccessful(),stream.getvalue()
assert not {'numpy','torch','scipy','pandas'}&set(sys.modules)
# Original terminal records only: no arrays, labels, tensor decode or fitting.
parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-serialized-storage-root-launch-20261005-01')
terminal_parent=obj(parent/'attempt/parent-terminal.json');cleanup=obj(parent/'attempt/owned-tree-cleanup.json')
root_exit=obj(BASE/'heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_NUMERICAL_ROOT_EXIT01.json')
summary=obj(CAP/'research_runs'/draft['parent']/'outputs/wrapper-summary.json')
print(json.dumps({'schema_version':1,'decision':'ACCEPTED_NARROW_SOURCE_AND_PROSPECTIVE_DRAFT_ONLY','manifest_sha256':sha(manifest_raw),'sealed_member_count':len(manifest['members']),'installed_map_count':len(before),'changed_installed_paths':sorted(changed),'namespaces_absent':[str(p) for p in namespace],'matching_numerical_processes':active,'actual_parent_claim_sha256':draft['actual_parent_claim']['sha256'],'actual_terminal_sha256':obs['complete_terminal']['sha256'],'checkpoint_sha256':obs['checkpoint_manifest']['sha256'],'opaque_state_bytes':len(raw),'opaque_state_sha256':sha(raw),'parent_terminal':terminal_parent,'cleanup':cleanup,'root_exit':root_exit,'summary':summary,'focused_test_output':stream.getvalue(),'unresolved':draft['unresolved'],'numerical_imports':False,'numerical_release':False,'new_claim':False},sort_keys=True,indent=2))
