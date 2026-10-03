"""Finite actual object reconstruction and named stdlib runtime metadata only."""
from pathlib import Path
import ast,hashlib,importlib.metadata,json,os,platform,stat,subprocess,sys
D=Path(__file__).resolve().parent;P=D.parent/'held-consumer-original-git-runtime-role-investigation01-2026-10-03'
H=lambda b:hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(p.read_bytes())
m=doc(P/'MANIFEST01.json');assert H((P/'MANIFEST01.json').read_bytes())=='b2876adef4ef24ca5a07a77370336a45c65fd769e97569379cade8d24e35aa5d'
for r in m['files']:
 b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
plan=doc(P/'ORIGINAL_GIT_COPY_PLAN01.json');origins=doc(P/'PRIMARY_ORIGINS01.json');runtime=doc(P/'RUNTIME_ROLE_BODY01.json')
assert H((P/'ORIGINAL_GIT_COPY_PLAN01.json').read_bytes())=='fab637a0a6e4232d4d54c708a1da411fa72b2cd8822beb5eb35bbb39b529143f'
assert H((P/'RUNTIME_ROLE_BODY01.json').read_bytes())=='2fb523f58c562933a56762fcdbf1a1806bc5af3fe0a68020d4f5c70037ecc59a'
assert len(origins['primary_documents'])==5
for row in origins['primary_documents']:
 p=Path(row['path']);b=p.read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256'] and stat.S_IMODE(p.lstat().st_mode)==row['mode']
original=doc(Path(origins['primary_documents'][0]['path']));assert len(original['original_source_files'])==26
assert doc(Path(origins['primary_documents'][1]['path']))==runtime
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
def git(g,*args):return subprocess.check_output(['git','--git-dir='+str(g),*args],env=env,stderr=subprocess.PIPE,timeout=10)
donors=[Path(plan[k]) for k in ('original_capsule_git','recovered_capsule_git')]
for g in donors:assert git(g,'rev-parse','--is-bare-repository').strip()==b'false'
objects={}
for row in plan['objects']:
 oid=row['object'];typ=row['type'];a=git(donors[0],'cat-file',typ,oid);b=git(donors[1],'cat-file',typ,oid)
 assert a==b and H(a)==row['sha256'] and len(a)==row['bytes']
 assert hashlib.sha1((typ+' '+str(len(a))+'\0').encode()+a).hexdigest()==oid
 assert git(donors[0],'cat-file','-t',oid).decode().strip()==typ
 objects[oid]=(typ,a)
assert len(objects)==34 and sum(len(b) for _,b in objects.values())==129529
assert {k:sum(typ==k for typ,_ in objects.values()) for k in ('commit','tree','blob')}==dict(commit=1,tree=7,blob=26)
commit=plan['source'];assert commit==original['original_source'];raw=objects[commit][1];root=raw.splitlines()[0].split()[1].decode();used={commit}
paths={x['path']:x for x in plan['source_paths']};assert set(paths)==set(original['original_source_files'])
for path,row in paths.items():
 oid=root
 for index,component in enumerate(path.split('/')):
  typ,body=objects[oid];assert typ=='tree';used.add(oid);entries={};i=0
  while i<len(body):
   z=body.index(b'\0',i);mode,name=body[i:z].split(b' ',1);child=body[z+1:z+21].hex();entries[name.decode()]=(mode.decode(),child);i=z+21
  mode,oid=entries[component]
  if index<len(path.split('/'))-1:assert mode=='40000'
  else:
   typ,body=objects[oid];assert typ=='blob';used.add(oid);assert mode==row['git_mode'] and oid==row['object'] and len(body)==row['bytes'] and H(body)==row['sha256']==original['original_source_files'][path]['sha256']==original['original_source_files'][path]['claim_sha256']
   for g in donors:assert git(g,'show',commit+':'+path)==body
assert used==set(objects) and sum(row['bytes'] for row in paths.values())==122632
missing='9df0ab43741659b390eec3d64070b0386e98c871';partial=Path(plan['partial_bare_repository_not_complete_donor'])
failed=subprocess.run(['git','--git-dir='+str(partial),'cat-file','-t',missing],env=env,capture_output=True,timeout=10)
assert failed.returncode==128 and b'could not get object info' in failed.stderr
(D/'incomplete-bare-witness01.log').write_bytes(failed.stdout+failed.stderr)
print('PASS finite34 objects: one authentic commit, seven path trees,26 exact source blobs; incomplete bare witness still refuses offline.')
# Genuine version/hash/251 exact RECORD reads; no package modules imported.
assert sys.executable==runtime['executable'] and sys.prefix==runtime['prefix'] and platform.python_version()==runtime['python']=='3.13.13'
exe=Path(sys.executable).resolve();assert str(exe)==runtime['resolved_executable'] and exe.stat().st_size==runtime['executable_bytes']==31510904
hasher=hashlib.sha256()
with exe.open('rb') as f:
 while b:=f.read(65536):hasher.update(b)
assert hasher.hexdigest()==runtime['executable_sha256']=='1b6373b55566df2953fe1e1345aec5df0d2e76c5e385871e68aa46c48020803d'
for key in ('main_lock','source_lock'):
 row=origins[key];p=Path(row['path']);b=p.read_bytes();assert H(b)==row['sha256']==runtime['lock_sha256'] and len(b)==row['bytes']
readback=doc(P/'RUNTIME_READBACK01.json');modes=doc(P/'RUNTIME_RECORD_MODES01.json');lookup={x['path']:x for x in modes};seen=set();total=0
assert len(runtime['distribution_records'])==len(lookup)==251
for row in runtime['distribution_records']:
 p=Path(row['record']);assert str(p) not in seen;seen.add(str(p));s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 b=p.read_bytes();z=lookup[str(p)];assert H(b)==row['record_sha256']==z['sha256'] and len(b)==z['bytes'] and stat.S_IMODE(s.st_mode)==z['mode']
 assert importlib.metadata.version(row['name'])==row['version']==z['version'];total+=len(b)
assert total==readback['record_bytes']==5033917
assert {x['path']:x for x in readback['distribution_records']}=={k:{a:b for a,b in v.items() if a!='mode'} for k,v in lookup.items()}
assert not {'numpy','torch','scipy','pandas','pyarrow'}.intersection(sys.modules)
# Reproduce the checker-only atime assumption on a new reviewer-owned file,
# never altering timestamps/content of original locks or source files.
tiny=D/'atime-only-control01.txt';tiny.write_bytes(b'unchanged synthetic metadata\n');os.utime(tiny,ns=(1,1));before=tiny.lstat();contents=tiny.read_bytes();after=tiny.lstat()
assert before!=after and before.st_atime_ns!=after.st_atime_ns
stable=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
assert tuple(getattr(before,k) for k in stable)==tuple(getattr(after,k) for k in stable)
assert contents==b'unchanged synthetic metadata\n'
print('PASS real atime-only read counterexample: full stat equality fails, stable signature/content do not change.')
source=Path(origins['source_lock']['path']).parent
assert git(source/'.git','rev-parse','HEAD').decode().strip()==origins['source_head']==plan['destination_source_head']=='903488c49ad25e8026ec849a1c8b30ca5f90bcff'
result=dict(schema_version=1,decision='accepted_finite_object_copy_plan_and_named_runtime_metadata_only',object_count=34,object_types={'commit':1,'tree':7,'blob':26},object_payload_bytes=129529,source_blob_bytes=122632,original_commit=commit,selected_paths=26,selected_tree_dependency_closure_verified=True,full_history_or_checkout=False,incomplete_bare_missing_object=missing,incomplete_bare_exit=failed.returncode,primary_documents=5,runtime_records=251,runtime_record_bytes=total,interpreter_bytes=31510904,python=platform.python_version(),source03_head=origins['source_head'],network=False,numerical_imports=False,objects_installed=False,qualification='No whole history traversal, package-body recovery, runtime/native authority, scientific result or claim.')
(D/'READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
