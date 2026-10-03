"""Independent source/tiny metadata checks, not authority or native execution."""
import ast,hashlib,json,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(P))
import proof_raw01 as raw
import proof_release01 as release
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((P/'MANIFEST02.json').read_text());total=0
for item in manifest['files']:
 path=P/item['path'];assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256'];total+=item['bytes']
print('Frozen authored files:',len(manifest['files']),'bytes:',total,'manifest:',sha(P/'MANIFEST02.json'))
inv=json.loads((P/'source_inventory02.json').read_text())
for row in inv['source_inventory']:
 path=ROOT/row['origin'];assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256']
for row in inv['dependencies']:
 path=ROOT/row['path'];assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256']
print('Six mapped outer sources and four frozen dependencies match.')
old=P.parent/'neural-cold-feature-handoff-proof-outer-preparation01-2026-10-03'
for name in ('proof_outer01.py','runtime_gate01.py','build_release_draft01.py'):assert (P/name).read_bytes()==(old/name).read_bytes()
owned=P.parent/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py';cls=next(n for n in ast.parse(owned.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='CleanupFailure');env={};exec(compile(ast.Module(body=[cls],type_ignores=[]),'actual-CleanupFailure','exec'),env);Cleanup=env['CleanupFailure']
for first,second,expected in [(Cleanup(),MemoryError(),1),(MemoryError(),Cleanup(),0),(SystemExit(),MemoryError(),0),(ValueError(),Cleanup(),1),(OSError(),MemoryError(),1)]:
 assert raw.preserve_owned(first,second,Cleanup) is (first,second)[expected]
for first,second,expected in [(MemoryError(),OSError(),0),(OSError(),MemoryError(),1),(SystemExit(),MemoryError(),0),(None,OSError(),1)]:
 calls=[]
 def op(*args):calls.append('open');return 7
 def sync(fd):
  calls.append('sync')
  if first is not None:raise first
 def close(fd):calls.append('close');raise second
 original=raw.os;raw.os=SimpleNamespace(open=op,fsync=sync,close=close,O_RDONLY=0,O_DIRECTORY=0,O_NOFOLLOW=0)
 try:
  try:raw.sync_owned_directory(Path('/qualified'),Cleanup)
  except BaseException as actual:assert actual is (first,second)[expected]
  else:raise AssertionError('unexpected success')
 finally:raw.os=original
 assert calls==['open','sync','close']
print('CO2 actual helper mixed first-fatal identity and one-close cases pass.')
# Improved forgery carries identity/phase keys, so conflicting source specifically refuses.
with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 def put(path,value):
  p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw.canonical(value));return raw.ref(root,path,kind='metadata')
 identity=raw.IDENTITIES['materialize'];a=put(raw.OUTER+identity+'/accepted.json',dict(status='accepted',phase='materialize',identity=identity,source='b'*40));w=put('proof_supervise/'+identity+'/exit.json',dict(status='accepted',phase='materialize',identity=identity,source='c'*40));current={'prior_materialization':{'accepted':a,'wait':w},'source':'a'*40}
 try:release.authenticate_prior(root,current,{}, {'payload':{'representation_jobs':{'cold-proof':{}}}})
 except ValueError as error:assert str(error)=='prior/current source commits conflict'
 else:raise AssertionError('conflicting source accepted')
 assert not (root/'research_runs').exists()
print('CO1 improved conflicting-source forgery refused before historical context.')
# Independently derive exact emitted input names from actual materializer source.
material=P.parent/'neural-cold-feature-handoff-proof-preparation01-2026-10-03/compact_cold_proof_inputs.py';tree=ast.parse(material.read_text())
keys={n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='put' and n.args and isinstance(n.args[0],ast.Constant)}
policy=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='policies' for t in n.targets));keys|={k.value for k in policy.keys};keys|={'graph-'+str(i).zfill(2) for i in range(19)}
assert keys==raw.MATERIAL_INPUTS and len(keys)==43
print('Actual materializer literal policy/put keys plus fixed19 graph population equal43 required inputs.')
assert not any(n.split('.')[0] in ('numpy','torch','scipy','tradingagents') for n in sys.modules)
print('No numerical imports, actual claims, native jobs, authority creation or network.')
