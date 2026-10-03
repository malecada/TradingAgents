from pathlib import Path
import ast,hashlib,json,os,platform,stat,subprocess,sys
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3]
C=F/'original-import-native-successor-preparation06-2026-10-03/capsule04'
X=F/'original-import-native-successor-preparation06-2026-10-03/outcome-recovery01/recovered-terminal-capsule04'
G=F/'original-import-native-successor-preparation06-2026-10-03/outcome-recovery01/repository.git'
S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source')
I=F/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json'
P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source/cold_prep/runtime.json')
B=F/'neural-cold-feature-handoff-held-consumer-fixture-successor-preparation02-2026-10-03/capsule_builder01.py'
E=F/'held-target-input-reuse-investigation01-2026-10-03/ORIGINAL_EVIDENCE_ROLE01.json'
V=S/'tradingagents/research/onchain_replication/resource_fixture.py'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,cap=4*1024**2):
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=cap
 with p.open('rb') as f:b=f.read(cap+1)
 assert len(b)==st.st_size and p.lstat()==st
 return b
def rec(p,cap=4*1024**2):
 b=read(p,cap);return {'path':str(p),'bytes':len(b),'sha256':sha(b),'mode':stat.S_IMODE(p.lstat().st_mode)}
def git(g,*a):return subprocess.check_output(['git','--git-dir='+str(g),*a],env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0'},timeout=15)
def write(n,x):(H/n).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
orig=json.loads(read(I));runtime=json.loads(read(P));assert git(S/'.git','rev-parse','HEAD').strip().decode()=='903488c49ad25e8026ec849a1c8b30ca5f90bcff'
assert len(orig['original_source_files'])==26
commit=orig['original_source'];objects={}
def obj(oid,kind):
 if oid not in objects:
  assert git(G,'cat-file','-t',oid).strip().decode()==kind
  n=int(git(G,'cat-file','-s',oid));assert 0<n<=2*1024**2
  b=git(G,'cat-file',kind,oid);assert len(b)==n and git(C/'.git','cat-file',kind,oid)==b and git(X/'.git','cat-file',kind,oid)==b
  assert hashlib.sha1((kind+' '+str(n)+'\0').encode()+b).hexdigest()==oid
  objects[oid]={'object':oid,'type':kind,'bytes':n,'sha256':sha(b)}
 return git(G,'cat-file',kind,oid)
cb=obj(commit,'commit');tree=cb.splitlines()[0].split()[1].decode();source=[]
for path,row in sorted(orig['original_source_files'].items()):
 t=tree;parts=path.split('/')
 for j,part in enumerate(parts):
  raw=obj(t,'tree');entries={};i=0
  while i<len(raw):
   z=raw.index(b'\0',i);mode,name=raw[i:z].split(b' ',1);oid=raw[z+1:z+21].hex();entries[name.decode()]=(mode.decode(),oid);i=z+21
  mode,oid=entries[part]
  if j<len(parts)-1:assert mode=='40000';t=oid
  else:
   assert mode in ('100644','100755');body=obj(oid,'blob');assert sha(body)==row['sha256']==row['claim_sha256'];source.append({'path':path,'git_mode':mode,'object':oid,'bytes':len(body),'sha256':sha(body)})
assert sum(x['bytes'] for x in source)==122632
assert git(G,'rev-parse','--is-bare-repository').strip()==b'true'
assert not (G/'objects/info/alternates').exists()
write('ORIGINAL_GIT_COPY_PLAN01.json',{'status':'verified-existing-objects-not-installed','source_git':str(G),'original_capsule_git':str(C/'.git'),'recovered_capsule_git':str(X/'.git'),'source':commit,'objects':list(sorted(objects.values(),key=lambda x:x['object'])),'source_paths':source,'object_payload_bytes':sum(x['bytes'] for x in objects.values()),'complete_for':'commit:path lookups of exactly26 original claimed sources; not full commit ancestry or entire unrelated tree','root_transfer':'Root may export the exact object IDs using git pack-objects --stdout without --revs, validate and install into future Git store; no operation performed here. Never copy old HEAD/config as new authority.','destination_source_head':git(S/'.git','rev-parse','HEAD').decode().strip()})
# Execute only the accepted stdlib helper and its strict file reader dependencies extracted from source.
assert sys.executable==runtime['executable'] and sys.prefix==runtime['prefix'] and platform.python_version()==runtime['python']
exe=Path(sys.executable).resolve();assert str(exe)==runtime['resolved_executable'];assert exe.stat().st_size==runtime['executable_bytes']
h=hashlib.sha256()
with exe.open('rb') as f:
 while b:=f.read(65536):h.update(b)
assert h.hexdigest()==runtime['executable_sha256']
assert sha(read(S/'uv.lock'))==sha(read(R/'uv.lock'))==runtime['lock_sha256']
# Actual helper invokes importlib.metadata.version on each explicit distribution, not numerical imports.
namespace={'Path':Path,'require':lambda v,m: None if v else (_ for _ in ()).throw(ValueError(m))}
def strict_read(root,path,digest,extent):
 p=Path(root)/path;b=read(p,32*1024**2);assert len(b)==extent and sha(b)==digest;return b
namespace['read']=strict_read
tree_ast=ast.parse(read(B));node=next(n for n in tree_ast.body if isinstance(n,ast.FunctionDef) and n.name=='held_runtime_metadata')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(B),'exec'),namespace)
observed=namespace['held_runtime_metadata'](S,runtime)
assert observed['record_count']==251
write('RUNTIME_READBACK01.json',observed)
write('RUNTIME_ROLE_BODY01.json',runtime)
write('PRIMARY_ORIGINS01.json',{'primary_documents':[rec(p) for p in (I,P,B,E,V)],'source_head':git(S/'.git','rev-parse','HEAD').decode().strip(),'runtime_interpreter':{'path':str(exe),'bytes':exe.stat().st_size,'sha256':h.hexdigest()},'source_lock':rec(S/'uv.lock'),'main_lock':rec(R/'uv.lock'),'scope':'251 explicit RECORD files plus interpreter/lock; no package bodies recovered or numerical modules imported'})
print('PASS',len(objects),'original Git objects',sum(x['bytes'] for x in objects.values()),'payload bytes;26 blobs122632B; three existing stores identical')
print('PASS actual accepted held_runtime_metadata:251 RECORDs',observed['record_bytes'],'bytes; interpreter/locks match; numerical imports=0')
