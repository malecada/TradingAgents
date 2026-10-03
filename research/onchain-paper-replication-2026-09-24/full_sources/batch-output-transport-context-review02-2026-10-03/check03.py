"""Independent selected-source review with synthetic owned-byte fixtures only."""
import ast,hashlib,importlib.util,json,os,shutil,sys,threading
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent;ROOT=H.parents[3];P=H.parent/'batch-output-transport-context-preparation02-2026-10-03'
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
manifest=json.loads((P/'MANIFEST02.json').read_bytes());assert sha((P/'MANIFEST02.json').read_bytes())=='49dc408e23e327116d6c040631369c54f0ef0c82430b224993e4d5b8f1effa3a'
for r in manifest['files']:
 b=(P/r['path']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
deps=json.loads((P/'DEPENDENCIES02.json').read_bytes())['dependencies']
for r in deps:
 b=(ROOT/r['path']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
m=load('independent_context02',P/'non_tail_context.py');f=load('synthetic_formats02',m.D/'test_formats02.py')
assert sha((P/'non_tail_context.py').read_bytes())=='52858e18ce1bf01715380dc149da0e6bf95728879c5d5798c5d3b24a587360d2'
def limits(**kw):
 d=dict(max_rounded_bytes=16*1024**2,max_commands=1000,max_parts=1000,part_bytes=32768,deadline_seconds=60);d.update(kw);return d
owned=H/'owned-bytes03';owned.mkdir()
# NTC1 firstfatal + growth controls against the actual new bootstrap.
p=owned/'source.py';p.write_bytes(b'source');assert m.bootstrap_read(p)==b'source'
first=MemoryError('original first fatal');realclose=os.close;closes=[]
def close(fd):closes.append(fd);realclose(fd);raise OSError('later close')
with patch.object(m.os,'read',side_effect=first),patch.object(m.os,'close',side_effect=close):
 try:m.bootstrap_read(p)
 except MemoryError as e:assert e is first
 else:raise AssertionError('first fatal lost')
assert len(closes)==1
realread=os.read;sizes=[]
def grow(fd,count):
 sizes.append(count)
 if len(sizes)==1:
  with p.open('ab') as stream:stream.write(b'more')
 return realread(fd,count)
with patch.object(m.os,'read',side_effect=grow):
 try:m.bootstrap_read(p)
 except ValueError as e:assert str(e)=='dependency grew'
 else:raise AssertionError('growth accepted')
assert sizes==[7]
print('NTC1 fixed controls: bounded growth refusal and identical first MemoryError after one real close')
# NTC2 same old two-thread schedule now refuses before the shared update.
b=m.Reservations(limits(max_commands=1));success=[];errors=[]
def reserve():
 try:success.append(dict(b.reserve(1)))
 except BaseException as e:errors.append(type(e).__name__)
threads=[threading.Thread(target=reserve) for _ in range(2)]
for t in threads:t.start()
for t in threads:t.join(timeout=3);assert not t.is_alive()
assert not success and len(errors)==2 and b.revoked and b.spent['commands']==0
b=m.Reservations(limits());a=b.reserve(32768);assert a['rounded_bytes']==65536
oldrequire=m.require;entered=[]
def reenter(v,text):
 oldrequire(v,text)
 if text=='cumulative reservation exhausted' and not entered:
  entered.append(True)
  try:b.reserve(1)
  except ValueError:pass
with patch.object(m,'require',side_effect=reenter):
 try:b.reserve(1)
 except ValueError:pass
 else:raise AssertionError('swallowed nested refusal allowed outer commit')
assert b.revoked and b.spent['rounded_bytes']==65536 and b.spent['commands']==1
print('NTC2 fixed controls: foreign threads refused/revoked; swallowed reentrant refusal cannot commit or refund; exact32768 charges65536')
# Complete unchanged content controls including raw f32 and NPY companion headers.
for kind in ('score-batches','mcm-output','graph-artifact'):
 original=owned/kind;original.mkdir()
 if kind=='score-batches':reference=f.batches(original)
 elif kind=='graph-artifact':reference=f.graph(original)
 else:
  body=b'\0'*128;(original/'matrix.f32').write_bytes(body)
  value=dict(schema_version=1,kind='compact-mcm-output',stage_sha256='12'*32,contract_sha256='13'*32,stage_directory='/synthetic/reviewer-stage',scope={k:'14'*32 for k in m.reader.SCOPES},owner='15'*32,rows=1,motifs=32,dtype='<f4',order='row-major',array_bytes=128,array_sha256=sha(body),execution_admitted=False)
  reference=f.save(original,'manifest.json',value)
 recovered=owned/(kind+'-recovered');shutil.copytree(original,recovered)
 with m.open_context(original,kind=kind,document_sha256=reference,limits=limits()) as c:
  rounded=commands=0
  for name in c.members:
   pieces=[]
   for offset,size in c.ranges(name):pieces.append(c.read_original(name,offset,size));rounded+=(size//32768+1)*32768;commands+=1
   assert b''.join(pieces)==(original/name).read_bytes()
  obs=c.verify_recovery(recovered);assert c.spent['rounded_bytes']==2*rounded and c.spent['commands']==2*commands
  assert obs['remote_verified'] is False and obs['recovery_authority'] is False and obs['local_bytes_retired']==0
  try:c.activate_transport()
  except NotImplementedError:pass
  else:raise AssertionError('transport activated')
 print('COMPLETE local original/recovery',kind,'members',len(c.members),'charges',dict(c.spent))
# NTC3 and birth/body/fatal all revoke shared aliases; previous spend persists.
root=owned/'score-batches';reference=sha((root/'terminal.json').read_bytes())
for mode in ('close','birth','body','fatal'):
 budget=m.Reservations(limits());alias=budget;budget.reserve(1);spent=dict(budget.spent)
 if mode=='birth':
  try:
   with m.open_context(root/'absent',kind='score-batches',document_sha256=reference,limits=budget):pass
  except BaseException:pass
 else:
  cm=m.open_context(root,kind='score-batches',document_sha256=reference,limits=budget);c=cm.__enter__();rootfd=c._reader.fd;closed=[]
  def selectedclose(fd):
   realclose(fd)
   if fd==rootfd:closed.append(fd);raise OSError('reader root close uncertain')
  primary=MemoryError('body fatal') if mode=='fatal' else ValueError('body failed') if mode=='body' else None
  with patch.object(m.reader.os,'close',side_effect=selectedclose):
   try:returned=cm.__exit__(type(primary) if primary else None,primary,None)
   except BaseException as e:
    if mode=='fatal':assert e is primary
   else:assert primary is not None and returned is False, 'failure unexpectedly suppressed'
  assert closed==[rootfd] and c.revoked
 assert alias.revoked and dict(alias.spent)==spent
 try:alias.reserve(1)
 except ValueError:pass
 else:raise AssertionError('shared alias reusable after failed context')
print('NTC3 fixed controls: birth/body/close/fatal revoke shared alias with original spend intact')
# Newly observed canonical-path rejoin gap, same exact file inode/body throughout.
parent=owned/'bootstrap-parent';parent.mkdir();source=parent/'dependency.py';source.write_bytes(b'original safe source');moved=owned/'bootstrap-parent-moved';changed=[]
def redirect(fd,count):
 if not changed:parent.rename(moved);parent.symlink_to(moved,target_is_directory=True);changed.append(True)
 return realread(fd,count)
with patch.object(m.os,'read',side_effect=redirect):result=m.bootstrap_read(source)
assert result==b'original safe source' and source.resolve()!=source and parent.is_symlink()
print('NTC4 CONFIRMED: actual bootstrap accepts parent redirect during read; final canonical origin differs despite unchanged file inode/body')
assert not {'numpy','torch','scipy','pandas','pyarrow'}.intersection(sys.modules)
print(json.dumps({'status':'WITHHELD','corrected':['NTC1-fatal/growth','NTC2','NTC3'],'remaining':['NTC4-canonical-parent-rejoin'],'author_bodies':len(manifest['files']),'dependency_bodies':len(deps),'authority_or_network':False}))
