"""Independent selected-source fragments; no authority, package or native job."""
import ast,hashlib,json,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import proof_raw01 as raw
# Extract the exact phase-prior branch; no earlier release/admission checks are
# claimed by this fragment. They do not inspect prior materialization evidence.
tree=ast.parse((P/'proof_release01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check_release')
start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='prior')
selected=compile(ast.fix_missing_locations(ast.Module(body=fn.body[start:start+2],type_ignores=[])),'<actual-prior-materialization-branch>','exec')
with tempfile.TemporaryDirectory(prefix='cold-prior-review-') as td:
 root=Path(td)
 def put(path,value,kind='metadata'):
  p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw.canonical(value));return raw.ref(root,path,kind=kind)
 population=put('fake/population.json',{'no_actual_population':True},'document')
 material=put('fake/future-inputs.json',{'inputs':{'population':{'path':population['path'],'sha256':population['sha256']}}},'document')
 authentication=put('fake/authentication.json',{'proof':{'kind':'materialized-inputs-only','scientific_completion':False,'future_inputs':material}})
 accepted=put(raw.OUTER+raw.IDENTITIES['materialize']+'/accepted.json',{'status':'accepted','phase':'materialize','source':'b'*40,'release':{'unverified':'not-a-release-reference'},'authentication':authentication})
 wait=put('proof_supervise/'+raw.IDENTITIES['materialize']+'/exit.json',{'status':'accepted','controller_exit_code':0,'controller_pid_absent':True,'accepted_receipt':accepted,'release':{'unverified':'not-a-release-reference'},'source':'c'*40,'controller_pid':2147483646,'supervisor_pid':2147483647})
 env={k:getattr(raw,k) for k in ('require','deref','digest','body','OUTER','IDENTITIES')};env.update(Path=Path,root=root,phase='compare',release={'source':'a'*40,'prior_materialization':{'accepted':accepted,'wait':wait}},job={'payload':{'representation_jobs':{'cold-proof':{}}}},experiment={'inputs':{'population':{'path':population['path'],'sha256':population['sha256']}}})
 exec(selected,env)
 assert not (root/'research_runs').exists()
 print('COUNTEREXAMPLE: exact prior branch accepts no materialization claim/native/lifecycle, a population-only invented future input document and conflicting current/accepted/wait source commits.')
# Actual accepted cleanup class, no package import; raw preserve is used by the
# supervisor, unlike the controller's type-aware select.
owned=P.parent/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py';node=next(n for n in ast.parse(owned.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='CleanupFailure');env={};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-CleanupFailure','exec'),env)
uncertain=env['CleanupFailure']('ordinary close uncertain');fatal=MemoryError('first actual fatal')
assert raw.preserve(uncertain,fatal) is uncertain
print('COUNTEREXAMPLE: supervisor preserve selects actual CleanupFailure over later first MemoryError.')
# Exact parent fsync/finally-close statements from supervisor run().
tree=ast.parse((P/'proof_supervise01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');node=next(n for n in ast.walk(fn) if isinstance(n,ast.Try) and len(n.body)==1 and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Call) and ast.unparse(n.body[0].value)=='os.fsync(fd)')
first=MemoryError('first fsync fatal');later=OSError('ordinary close');calls=[]
def sync(fd):calls.append(('fsync',fd));raise first
def close(fd):calls.append(('close',fd));raise later
env={'os':SimpleNamespace(fsync=sync,close=close),'fd':123}
try:exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-supervisor-parent-close','exec'),env)
except BaseException as selected:
 assert selected is later and selected.__context__ is first
else:raise AssertionError('expected retained failure')
assert calls==[('fsync',123),('close',123)]
print('COUNTEREXAMPLE: supervisor parent-directory close masks fsync MemoryError with OSError; both calls once.')
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print('No numerical imports, actual subprocesses, claims, native units or scientific artifacts.')
