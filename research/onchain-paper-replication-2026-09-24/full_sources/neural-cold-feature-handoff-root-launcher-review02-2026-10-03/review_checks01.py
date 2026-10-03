"""Independent frozen launcher02 checks; synthetic metadata only, no authority."""
import ast,copy,hashlib,importlib.util,json,pathlib,stat,sys,types
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent;B=P.parent;A=B/'neural-cold-feature-handoff-root-launcher-preparation02-2026-10-03';OLD=B/'neural-cold-feature-handoff-root-launcher-preparation01-2026-10-03';ROOT=P.parents[3]
def sha(x):return hashlib.sha256(x).hexdigest()
assert sha((A/'MANIFEST02.json').read_bytes())=='ca5238d0f42a71e66d11c5c4d0e232010fa55a916e2720654580e8ef339797ed'
manifest=json.loads((A/'MANIFEST02.json').read_bytes())
for r in manifest['files']:
 b=(A/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'],r['path']
assert (A/'baseline01.py').read_bytes()==(OLD/'launcher01.py').read_bytes()
for n in ('SOURCE_ORIGINS01.json','REQUEST_TEMPLATE01.json'):assert (A/n).read_bytes()==(OLD/n).read_bytes()
for r in json.loads((A/'SOURCE_ORIGINS01.json').read_bytes()).values():assert sha((ROOT/r['path']).read_bytes())==r['sha256']
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load(A/'launcher02.py','review_launcher02');old=load(OLD/'launcher01.py','review_launcher01')
before=ast.parse((A/'baseline01.py').read_bytes());after=ast.parse((A/'launcher02.py').read_bytes());bf={n.name:n for n in before.body if isinstance(n,ast.FunctionDef)};af={n.name:n for n in after.body if isinstance(n,ast.FunctionDef)}
changed={n for n in bf if ast.dump(bf[n])!=ast.dump(af[n])};assert changed=={'fatal','select','actions','root_watch','cleanup_descendants','execute'}
assert set(af)-set(bf)=={'tail_write','finish_tail'}
normalized=copy.deepcopy(after);normalized.body=[copy.deepcopy(bf[n.name]) if isinstance(n,ast.FunctionDef) and n.name in changed else n for n in normalized.body if not(isinstance(n,ast.FunctionDef) and n.name in {'tail_write','finish_tail'})]
assert ast.dump(normalized)==ast.dump(before)
# Full source inverse: execute only the author's normalization statements/assert,
# excluding its patch-output mutation and print, after independently checking the
# changed-function set and reading the complete declared patch.
pt=ast.parse((A/'check_parity02.py').read_bytes());pt.body=[n for n in pt.body if not(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ((isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='write_text') or (isinstance(n.value.func,ast.Name) and n.value.func.id=='print')))]
exec(compile(pt,'read-only-inverse-normalization','exec'),{'__file__':str(A/'check_parity02.py')})
result={'manifest_bodies':len(manifest['files']),'source_origin_pins':7,'changed_functions':sorted(changed),'full_inverse_AST':True,'numeric_or_authority_execution':False,'cases':[]}
# Exact old terminal reproduces RL1. Preserve the old original observation in a
# NEW independent tiny directory, never rerun an original owned identity.
dir=P/'old-red';dir.mkdir();root=P/'synthetic-empty-root';root.mkdir();calls=[]
def watch_old(*args,**kw):
 calls.append(kw)
 if len(calls)==2:raise ValueError('synthetic final watch failure')
 return {'files':0,'allocated_bytes':0}
tail=next(n for n in bf['execute'].body if isinstance(n,ast.Try)).finalbody
start=next(i for i,n in enumerate(tail) if isinstance(n,ast.Try) and any(isinstance(c,ast.Name) and c.id=='disposition' for c in ast.walk(n)))
ns=dict(old.__dict__);ns.update(directory=dir,root=root,identity='review-synthetic',q={'phase':'materialize','source':'ab'*20},request_reference={},process=None,observed={},primary=None,result={'synthetic':True},root_watch=watch_old)
ns['retain']=lambda e:ns.update(primary=old.select(ns['primary'],e))
exec(compile(ast.Module(body=copy.deepcopy(tail[start:]),type_ignores=[]),'old-exact-tail','exec'),ns)
assert isinstance(ns['primary'],ValueError) and json.loads((dir/'observation.json').read_bytes())['result'] and not (dir/'failure.json').exists()
result['old_RL1_reproduced']=True
# Actual new helper cases with exclusively owned output files and explicit
# synthetic watch/I/O failure injection. Each injected error object is retained.
original_write=m.write
cases=[('normal',None,None,None),('ordinary-final',ValueError('final'),None,None),('fatal-final',MemoryError('final'),None,None),('early-fatal-late-fatal',MemoryError('later'),SystemExit(7),None),('partial-seal',None,None,'partial-seal'),('first-marker-fatal',ValueError('final'),None,'first-marker-fatal'),('all-markers',MemoryError('final'),None,'all-markers'),('observation-fatal',None,None,'observation-fatal')]
for name,late,primary,fail in cases:
 d=P/name;d.mkdir();watches=[];writes=[];markerfatal=KeyboardInterrupt('marker');obsfatal=MemoryError('observation');sealfatal=MemoryError('seal')
 def watch(directory,**kw):
  watches.append(kw)
  if len(watches)==2 and late is not None:raise late
  return {'files':0,'allocated_bytes':0}
 def write(directory,name,data):
  writes.append(name)
  if fail=='first-marker-fatal' and name=='failure.json':raise markerfatal
  if fail=='all-markers' and name in ('failure.json','late-failure.json','tail-write-failure.json'):raise OSError('synthetic full marker failure')
  if fail=='observation-fatal' and name=='observation.json':raise obsfatal
  original_write(directory,name,data)
  if fail=='partial-seal' and name=='tail-complete.json':raise sealfatal
 with patch.object(m,'root_watch',side_effect=watch),patch.object(m,'write',side_effect=write):
  selected=m.finish_tail(d,root,'review-synthetic',{'phase':'materialize','source':'ab'*20},{},None,{},primary,{'synthetic':True},())
 files={p.name for p in d.iterdir()}
 if name=='normal':assert selected is None and 'tail-complete.json' in files and 'failure.json' not in files
 else:
  expected=primary if primary is not None else markerfatal if fail=='first-marker-fatal' else sealfatal if fail=='partial-seal' else obsfatal if fail=='observation-fatal' else late
  assert selected is expected,(name,selected,expected)
  if fail=='all-markers':assert not files&{'failure.json','late-failure.json','tail-write-failure.json'} and 'tail-complete.json' not in files
  else:
   marker=next(n for n in ('failure.json','late-failure.json','tail-write-failure.json') if n in files);v=json.loads((d/marker).read_bytes());assert v['revokes_observation'] and v['revokes_any_tail_complete'] and v['child_terminal_synthesized'] is False
  if fail=='partial-seal':assert 'tail-complete.json' in files
 assert len(writes)==len(set(writes)),(name,writes)
 assert len(watches)==(2 if name=='normal' else 3)
 result['cases'].append({'case':name,'selected_error':None if selected is None else type(selected).__name__,'writes':writes,'watch_arguments':watches})
# Exact canonical owned class: identity-based exemption, same-spelling stranger
# still actual fatal. All classes used here are AST-only, not a package import.
owned=B/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03/source-bodies/tradingagents/research/onchain_replication/owned_io.py'
ns={};exec(compile(ast.Module(body=[n for n in ast.parse(owned.read_bytes()).body if isinstance(n,ast.ClassDef) and n.name=='CleanupFailure'],type_ignores=[]),'exact-canonical-class','exec'),ns)
cls=ns['CleanupFailure'];u=cls('uncertain')
for fatal in (MemoryError(),KeyboardInterrupt(),SystemExit(4)):
 assert m.select(u,fatal,(cls,)) is fatal and m.select(fatal,u,(cls,)) is fatal
other=type('CleanupFailure',(BaseException,),{});foreign=other();assert m.select(foreign,MemoryError(),(cls,)) is foreign
# Actual checked byte/entry arithmetic at boundaries using synthetic stat rows.
class Entry:
 def __init__(self,allocated):self.allocated=allocated
 def lstat(self):return types.SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_nlink=1,st_size=1,st_blocks=self.allocated//512)
with patch.object(m.shutil,'disk_usage',return_value=types.SimpleNamespace(free=20*m.GIB)):
 for allocated,count,ok in ((23*1024**2,24,True),(23*1024**2+512,24,False),(0,25,False)):
  entries=[Entry(allocated)]+[Entry(0) for _ in range(count-1)];directory=types.SimpleNamespace(iterdir=lambda:iter(entries))
  try:v=m.root_watch(directory)
  except ValueError:assert not ok
  else:assert ok
# 9MiB/8 entries > observation4MiB + error4MiB + intent/seal/3markers64KiB each.
assert 9*1024**2 >= 2*m.MAX+5*65536 and 8>=7
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
result['canonical_type_identity_and_firstfatal']=True;result['active_23MiB_24_entries_bounds']=True;result['initial_headroom_arithmetic']=True
print(json.dumps(result,indent=2))
