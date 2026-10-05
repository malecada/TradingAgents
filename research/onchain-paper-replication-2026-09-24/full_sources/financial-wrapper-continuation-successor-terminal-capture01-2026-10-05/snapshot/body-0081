"""Independent finite metadata review; no admission creation or numerical import."""
import ast, copy, hashlib, importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / 'financial-wrapper-continuation-successor-source01-2026-10-05'
CAP = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01')
OLD_PARENT = PARENT.parent / 'genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01'
checks = []
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
def good(name, predicate):
    assert predicate, name
    checks.append(name)
def reject(name, operation):
    try: operation()
    except H.Unavailable: checks.append(name)
    else: raise AssertionError(name)

H = load('independent_successor_helper', CANDIDATE/'operational_source_compatibility.py')
oldraw = (CAP/'fixture_inputs/financial_wrapper_compatibility01/policy.json').read_bytes()
old = json.loads(oldraw)
edgepath = Path(sys.argv[1]).resolve()
edgeraw = edgepath.read_bytes()
edge = json.loads(edgeraw)
refusal = (HERE.parent/'financial-wrapper-continuation-outcome-review01-2026-10-05/FULL_REFUSAL_RECOVERY_PROOF01.json').read_bytes()
pin = sha((CANDIDATE/'operational_source_compatibility.py').read_bytes())
effective = H.validate_successor(old, oldraw, edge, pin, refusal)
good('edge has actual candidate bodies', all(edge['installed'][p] == sha((CANDIDATE/Path(p).name).read_bytes()) for p in H.SUCCESSOR_DELTA))
good('full195 source denominator', len(old['target']['installed']) == len(edge['installed']) == 195)
good('exact193 unchanged installed hashes', sum(old['target']['installed'][p] == edge['installed'][p] for p in edge['installed']) == 193)
good('original policy remains byte-exact', sha(oldraw) == H.ORIGINAL_POLICY_SHA)
good('legacy contract still accepts original', H.validate_contract(old,H.ORIGINAL_HELPER_SHA) == old)
reject('legacy map rejects successor', lambda:H.validate_maps(old['historical']['installed'],edge['installed'],pin))
for label, mutate in [('reserved identity',lambda e:e['consumer'].update(experiment=H.RESERVED_ID)), ('different cell',lambda e:e['consumer'].update(cell_id='different')), ('missing path',lambda e:e['installed'].pop(H.PREFIX+'training.py')), ('changed science source',lambda e:e['installed'].update({H.PREFIX+'training.py':'0'*64})), ('extra path',lambda e:e['installed'].update({'arbitrary.py':'0'*64})), ('omitted delta',lambda e:e.update(allowed_delta=[]))]:
    bad=copy.deepcopy(edge);mutate(bad)
    reject(label,lambda:H.validate_successor(old,oldraw,bad,pin,refusal))
claimpath=CAP/'research_runs'/old['consumers']['complete100']['experiment']/'claim.json'
claim=json.loads(claimpath.read_bytes())
cell=old['consumers']['complete100']['cell_id']
fit=CAP/'research_artifacts/onchain_fit_cells'/sha(cell.encode())/claim['experiment_id']
complete=json.loads((fit/'complete.json').read_bytes())
prior=json.loads(Path(complete['checkpoint']).read_bytes())['provenance']
new=copy.deepcopy(prior);new.update(source_hashes=sorted(set(edge['installed'].values())),source_commit='2'*40,cell_id=H.SUCCESSOR_CELL)
H.validate_successor_reference(old,effective,claim,prior,new)
checks.append('actual COMPLETE100 original provenance joins new full source list')
for field in prior:
    if field in ('source_commit','cell_id'): continue
    bad=copy.deepcopy(new);bad[field]=[] if field=='source_hashes' else 'mutated'
    reject('reference rejects changed '+field,lambda:H.validate_successor_reference(old,effective,claim,prior,bad))
bad=copy.deepcopy(prior);bad['source_hashes']=new['source_hashes']
reject('old list cannot be rewritten as successor',lambda:H.validate_successor_reference(old,effective,claim,bad,new))
for name in ('descendants01.py','supervisor01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json'):
    good('unchanged Parent helper '+name,(PARENT/name).read_bytes()==(OLD_PARENT/name).read_bytes())
before=ast.parse((CAP/H.PREFIX/'financial_wrapper_fixture.py').read_text())
after=ast.parse((CANDIDATE/'financial_wrapper_fixture.py').read_text())
functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a,b=functions(before),functions(after)
good('only admitted and reference runtime functions changed',set(b)-set(a)=={'require_compatibility_roles'} and {k for k in a if a[k]!=b[k]} == {'admitted','_reference_state'})
fixture=load('independent_successor_fixture',CANDIDATE/'financial_wrapper_fixture.py')
try: fixture.require_compatibility_roles({H.SUCCESSOR_ROLE:{}})
except fixture.Unavailable: checks.append('successor without original policy refuses')
else: raise AssertionError('successor without original role accepted')
fixture.require_compatibility_roles({H.SUCCESSOR_ROLE:{},H.ROLE:{}})
# Metadata consistency fixtures are deliberately not represented as admission,
# reviewer authority or recovery evidence.
closure={'schema_version':1,'installed':old['target']['installed'],'scientific_model':H.MODEL,'scientific_training':H.TRAINING,'candidate02':fixture.CANDIDATE}
bodies={H.SUCCESSOR_ROLE:edgeraw,edge['refusal_input']:refusal,edge['original_closure_input']:H.canonical(closure)}
for role in H.SUCCESSOR_PROOFS:
    bodies[role]=H.canonical({'schema_version':1,'kind':role,'decision':'accepted','policy_sha256':sha(edgeraw),'original_policy_sha256':H.ORIGINAL_POLICY_SHA,'historical_map_sha256':sha(H.canonical(old['target']['installed'])),'target_map_sha256':sha(H.canonical(edge['installed'])),'checker_sha256':pin,'refusal_sha256':H.REFUSAL_SHA})
inputs={role:{'path':role} for role in bodies}
sources={role:sha(body) for role,body in bodies.items()}
H.successor_context(old,oldraw,bodies.__getitem__,sources,inputs,pin)
for key in ('candidate02','schema_version','scientific_model'):
    bad=copy.deepcopy(closure);bad.pop(key);bodies[edge['original_closure_input']]=H.canonical(bad)
    reject('original closure rejects omitted '+key,lambda:H.successor_context(old,oldraw,bodies.__getitem__,sources,inputs,pin))
bodies[edge['original_closure_input']]=H.canonical(closure)
for role in H.SUCCESSOR_PROOFS:
    keep=bodies.pop(role)
    try:H.successor_context(old,oldraw,bodies.__getitem__,sources,inputs,pin)
    except KeyError:checks.append('missing independent evidence role refuses '+role)
    else:raise AssertionError('missing role accepted')
    bodies[role]=keep
good('no numerical imports',not {'torch','numpy','scipy','pandas'} & set(sys.modules))
print(json.dumps({'decision':'SOURCE_METADATA_CHECKS_PASSED_NOT_RELEASE','checks':checks,'policy_sha256':sha(edgeraw),'candidate_sha256':{p.name:sha(p.read_bytes()) for p in (CANDIDATE/'operational_source_compatibility.py',CANDIDATE/'financial_wrapper_fixture.py',CANDIDATE/'preclaim01.py')},'numerical_imports':False,'limitations':['No ResearchRun.start, Owner launch, checkpoint decode, numerical agreement, capacity, financial return or full recovery test.','Genuine current Admission and complete final Parent remain a later review phase.']},indent=2,sort_keys=True))
