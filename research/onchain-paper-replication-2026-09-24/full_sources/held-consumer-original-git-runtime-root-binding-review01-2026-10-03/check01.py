from pathlib import Path
import hashlib,json,os,stat,subprocess,sys,platform,importlib.metadata
H=Path(__file__).resolve().parent;F=H.parent;O=F/'held-consumer-original-git-runtime-root-binding01-2026-10-03';I=F/'held-consumer-original-git-runtime-role-investigation01-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,cap=4*1024**2):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=cap
 b=p.read_bytes();assert len(b)==s.st_size;return b
def doc(p):return json.loads(read(p))
def git(g,*args,body=None):return subprocess.check_output(['git','--git-dir='+str(g),*args],input=body,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0'},timeout=20)
bind=doc(O/'ORIGINAL_GIT_RUNTIME_BINDING01.json');assert sha(read(O/'ORIGINAL_GIT_RUNTIME_BINDING01.json'))=='876e1799f7ca8f42cf9e0da68a2e9611cee8d8359e99f884a7439131332ef7e1'
plan=doc(I/'ORIGINAL_GIT_COPY_PLAN01.json');S=Path(bind['source_root']);G=S/'.git';head=git(G,'rev-parse','HEAD').strip().decode();assert head==bind['unchanged_source_head']=='903488c49ad25e8026ec849a1c8b30ca5f90bcff'
assert bind['objects']==plan['objects'] and bind['source_paths']==plan['source_paths']
pack=read(O/bind['pack']['path']);assert len(pack)==49047 and sha(pack)==bind['pack']['sha256']=='c8bd7083693b5b40e0d473d7b86cded8da6ba2c367bae89d7ac2bf281e556378'
# Owned offline bare verification only; no fetch/config on any original repository.
B=H/'pack-check.git';subprocess.check_output(['git','init','--bare',str(B)],stderr=subprocess.STDOUT,timeout=10)
index_result=git(B,'index-pack','--stdin',body=pack).strip().decode();assert index_result==bind['pack']['actual_index_pack_stdout']
all_objects=git(B,'cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype) %(objectsize)').decode().splitlines();assert len(all_objects)==34
assert {l.split()[0] for l in all_objects}=={x['object'] for x in bind['objects']}
for row in bind['objects']:
 for g in [G,B,Path(plan['source_git']),Path(plan['recovered_capsule_git'])]:
  assert git(g,'cat-file','-t',row['object']).strip().decode()==row['type'];raw=git(g,'cat-file',row['type'],row['object']);assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
for row in bind['source_paths']:
 raw=git(G,'cat-file','blob',bind['actual_original_source']+':'+row['path']);assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
composition=doc(F/'held-consumer-root-source-composition03-2026-10-03/SOURCE_COMPOSITION03.json')
rawtree=git(G,'ls-tree','-rz','HEAD');tracked={}
for item in rawtree.split(b'\0'):
 if not item:continue
 meta,name=item.split(b'\t');mode,kind,oid=meta.decode().split();name=name.decode();assert kind=='blob';raw=read(S/name);assert raw==git(G,'cat-file','blob',oid);tracked[name]={'bytes':len(raw),'sha256':sha(raw),'git_mode':mode}
assert len(tracked)==204
entries=composition['source_entries'];print('source entry representation',type(entries).__name__)
if isinstance(entries,dict):it=entries.items()
else:it=((r.get('target',r.get('path')),r) for r in entries)
for name,row in it:
 assert tracked[name]['sha256']==row['sha256'] and tracked[name]['bytes']==row['bytes']
assert len(entries)==199
packages={n:v for n,v in tracked.items() if n.startswith('tradingagents/') and n.endswith('.py')};assert len(packages)==148
for n in packages:assert read(S/n)==git(G,'cat-file','blob',composition['unchanged_148_package_anchor']+':'+n)
prior=doc(F/'held-target-input-reuse-review01-2026-10-03/READBACK01.json');inputs=prior['selected_bodies'];assert len(inputs)==22
for row in inputs:assert sha(read(S/row['path']))==row['sha256'] and len(read(S/row['path']))==row['bytes']
runtime=doc(S/bind['runtime_role']['relative_path']);assert read(S/bind['runtime_role']['relative_path'])==read(I/'RUNTIME_ROLE_BODY01.json')
assert sys.executable==runtime['executable'] and sys.prefix==runtime['prefix'] and platform.python_version()==runtime['python'];exe=Path(sys.executable).resolve();assert str(exe)==runtime['resolved_executable']
h=hashlib.sha256()
with exe.open('rb') as f:
 while b:=f.read(65536):h.update(b)
assert h.hexdigest()==runtime['executable_sha256'] and exe.stat().st_size==runtime['executable_bytes'];assert sha(read(S/'uv.lock'))==runtime['lock_sha256']
total=0
for row in runtime['distribution_records']:
 p=Path(row['record']);assert p.resolve()==p and p.is_relative_to(Path(sys.prefix));assert importlib.metadata.version(row['name'])==row['version'];raw=read(p,32*1024**2);assert sha(raw)==row['record_sha256'];total+=len(raw)
assert len(runtime['distribution_records'])==251 and total==5033917
actual=[]
for directory,dirs,files in os.walk(S,followlinks=False):
 if Path(directory)==S:dirs.remove('.git')
 for name in dirs+files:assert not (Path(directory)/name).is_symlink()
 for name in files:actual.append((Path(directory)/name).relative_to(S).as_posix())
expected=set(tracked)|{r['path'] for r in inputs}|{bind['runtime_role']['relative_path']};assert len(expected)==227 and set(actual)==expected
assert not (S/'.venv').exists() and not (G/'objects/info/alternates').exists();assert git(G,'rev-parse','HEAD').strip().decode()==head
report={'status':'accepted-actual-local-binding-only','head':head,'pack_sha256':sha(pack),'pack_bytes':len(pack),'exact_objects':34,'object_payload_bytes':sum(r['bytes'] for r in bind['objects']),'original_source_paths':26,'original_blob_bytes':122632,'tracked_bodies':204,'selected_sources':199,'package_anchor_bodies':148,'retained_opaque_inputs':22,'non_git_files':227,'runtime_records':251,'runtime_record_bytes':total,'array_decoding':False,'package_body_recovery':False,'native_or_registration_authority':False,'source_rows':tracked}
(H/'READBACK01.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('PASS actual installed34 objects+owned pack exactmembership;26 lookups;199/148/204source unchanged;227nonGitfiles;251runtime RECORDs; localonly')
