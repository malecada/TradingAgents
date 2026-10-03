"""Independent stdlib-only source/body and tiny local-byte counterexamples."""
import ast, hashlib, importlib.util, json, os, shutil, sys, threading
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SRC=HERE.parent/'batch-output-transport-context-preparation01-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
manifest=json.loads((SRC/'MANIFEST01.json').read_bytes())
assert sha((SRC/'MANIFEST01.json').read_bytes())=='8023fc8d06597f22291a25a495e38cac6c5c124f4184e32c705d9516a3705e06'
for row in manifest['files']:
 b=(SRC/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
deps=json.loads((SRC/'DEPENDENCIES01.json').read_bytes())
for row in deps['files']:
 b=(ROOT/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
print('AUTHENTICATED',len(manifest['files']),'author bodies;',len(deps['files']),'dependency bodies')

# Actual load() boundary: actual Path.read_bytes is unbounded and its context
# manager close can replace the exact first fatal. The file object alone is fake.
tree=ast.parse((SRC/'non_tail_context.py').read_bytes())
node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='load')
ns={'D':SRC,'hashlib':hashlib,'PINS':{},'sys':sys,'Path':Path,'require':lambda *a:None}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(SRC/'non_tail_context.py'),'exec'),ns)
first=MemoryError('review first fatal');later=OSError('review close error');reads=[]
class Stream:
 def __enter__(self):return self
 def read(self,*args):reads.append(args);raise first
 def __exit__(self,*args):raise later
with patch.object(Path,'open',return_value=Stream()):
 try:ns['load']('owned_io')
 except BaseException as caught:
  assert caught is later and caught.__context__ is first
  print('NTC1 REPRODUCED: unbounded read arguments',reads,'raised later OSError, not original MemoryError')

m=load('review_context01',SRC/'non_tail_context.py')
f=load('review_formats01',m.D/'test_formats02.py')
def limits(**kw):
 v=dict(max_rounded_bytes=1048576,max_commands=100,max_parts=100,part_bytes=128,deadline_seconds=60);v.update(kw);return v

# Deterministic interleaving inside the actual reserve method, immediately
# after both threads compute their successor and before either publishes it.
budget=m.Reservations(limits(max_commands=1));barrier=threading.Barrier(2);oldrequire=m.require;success=[];errors=[]
def interleave(v,text):
 oldrequire(v,text)
 if text=='cumulative reservation exhausted':barrier.wait(timeout=3)
def reserve():
 try:success.append(dict(budget.reserve(1)))
 except BaseException as e:errors.append(type(e).__name__)
with patch.object(m,'require',side_effect=interleave):
 ts=[threading.Thread(target=reserve) for _ in range(2)]
 for t in ts:t.start()
 for t in ts:t.join(timeout=5);assert not t.is_alive()
assert not errors and len(success)==2 and budget.spent['commands']==1 and not budget.revoked
print('NTC2 REPRODUCED:',len(success),'successful reservations; max_commands=1; stored',dict(budget.spent))

owned=HERE/'owned-bytes01';owned.mkdir()
for kind in ('score-batches','mcm-output','graph-artifact'):
 original=owned/kind;original.mkdir()
 if kind=='score-batches':ref=f.batches(original)
 elif kind=='graph-artifact':ref=f.graph(original)
 else:
  body=b'\0'*128;(original/'matrix.f32').write_bytes(body)
  value=dict(schema_version=1,kind='compact-mcm-output',stage_sha256='12'*32,contract_sha256='13'*32,stage_directory='/synthetic/reviewer-stage',scope={k:'14'*32 for k in m.reader.SCOPES},owner='15'*32,rows=1,motifs=32,dtype='<f4',order='row-major',array_bytes=128,array_sha256=sha(body),execution_admitted=False)
  ref=f.save(original,'manifest.json',value)
 recovered=owned/(kind+'-recovered');shutil.copytree(original,recovered)
 with m.open_context(original,kind=kind,document_sha256=ref,limits=limits()) as c:
  calculated=[0,0]
  for name in c.members:
   actual=(original/name).read_bytes();parts=[]
   for offset,size in c.ranges(name):
    parts.append(c.read_original(name,offset,size));calculated[0]+=((size+32767)//32768)*32768;calculated[1]+=1
   assert b''.join(parts)==actual
  result=c.verify_recovery(recovered)
  assert c.spent['rounded_bytes']==2*calculated[0] and c.spent['commands']==2*calculated[1]
  assert result['remote_verified'] is False and result['recovery_authority'] is False and result['local_bytes_retired']==0
  try:c.activate_transport()
  except NotImplementedError:pass
  else:raise AssertionError('activation accepted')
  print('CONTROL complete original/recovered',kind,'members',len(c.members),'spent',dict(c.spent),'activation refused')

# On a clean-body exit, actual reader root close is attempted exactly once.
# Error is injected AFTER actual fd close, so no descriptor is leaked here.
budget=m.Reservations(limits());root=owned/'score-batches';ref=sha((root/'terminal.json').read_bytes())
cm=m.open_context(root,kind='score-batches',document_sha256=ref,limits=budget);c=cm.__enter__();closed=[];realclose=os.close
def failedclose(fd):closed.append(fd);realclose(fd);raise OSError('review close uncertainty')
# Avoid perturbing the final content checks: inject only when the actual retained
# root descriptor is closed (all temporary read descriptors close normally).
rootfd=c._reader.fd
def selectedclose(fd):
 if fd==rootfd:return failedclose(fd)
 return realclose(fd)
with patch.object(m.reader.os,'close',side_effect=selectedclose):
 try:cm.__exit__(None,None,None)
 except m.io.CleanupFailure:pass
 else:raise AssertionError('missing cleanup uncertainty')
assert closed==[rootfd] and c.revoked and not budget.revoked
budget.reserve(1)
print('NTC3 REPRODUCED: root fd closed once; context revoked but shared budget remains usable',dict(budget.spent))
assert not {'numpy','torch','scipy','pandas','pyarrow'}.intersection(sys.modules)
print('NO numerical imports, network, real authority, remote transport or deletion; all counterexamples retained')
