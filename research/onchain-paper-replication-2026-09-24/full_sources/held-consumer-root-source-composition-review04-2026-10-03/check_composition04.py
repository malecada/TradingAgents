"""Offline byte/Git/metadata review; no source or numeric execution."""
import hashlib,json,os,stat,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;MAIN=F.parents[2]
R=F/'held-consumer-root-source-composition04-2026-10-03'
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(R/'SOURCE_COMPOSITION04.json').read_bytes();assert sha(raw)=='322eeb896ee3e3b40285723d56fa5fd65de3f7360267fa146bc83468231c69b2';doc=json.loads(raw)
S=Path(doc['source_root']);OLD=S.parent.parent/'held-score-consumer-native-20261003-03/source'
HEAD='fa9712c36daf2896ef3f6a8a8a5d99ec696cfdf4';ANCHOR='0cfc2c03200880534b7c91c2f16ac659a265a35b';PARENT='903488c49ad25e8026ec849a1c8b30ca5f90bcff'
ENV=os.environ|{'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0'}
def git(root,*args,data=None):
 r=subprocess.run(['git','-c','protocol.allow=never','-C',str(root),*args],input=data,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);assert r.returncode==0,(args,r.stderr);return r.stdout
assert git(S,'rev-parse','HEAD').decode().strip()==HEAD
assert git(OLD,'rev-parse','HEAD').decode().strip()==PARENT
assert not (S/'.git/objects/info/alternates').exists()
for child,parent in [(HEAD,ANCHOR),(ANCHOR,PARENT)]:
 assert git(S,'rev-list','--parents','-n','1',child).decode().split()==[child,parent]
assert git(S,'rev-parse',HEAD+'^{tree}')==git(S,'rev-parse',ANCHOR+'^{tree}')
def tree(root,ref):
 out={}
 for row in git(root,'ls-tree','-rz',ref).split(b'\0'):
  if row:
   a,b=row.split(b'\t',1);mode,kind,oid=a.decode().split();assert kind=='blob';out[b.decode()]=(mode,oid)
 return out
trees=tree(S,HEAD);anchors=tree(S,ANCHOR);previous=tree(S,PARENT)
assert trees==anchors and previous==tree(OLD,PARENT) and len(trees)==204
changed=[n for n in trees if trees[n]!=previous[n]];assert changed==['tradingagents/research/onchain_replication/resource_fixture.py']
def batches(root,requests):
 stream=git(root,'cat-file','--batch',data=('\n'.join(requests)+'\n').encode());offset=0;result=[]
 for request in requests:
  end=stream.index(b'\n',offset);oid,kind,size=stream[offset:end].split();size=int(size);offset=end+1
  body=stream[offset:offset+size];offset+=size;assert len(body)==size and stream[offset:offset+1]==b'\n';offset+=1
  assert hashlib.sha1(kind+b' '+str(size).encode()+b'\0'+body).hexdigest()==oid.decode()
  result.append((oid.decode(),kind.decode(),body))
 assert offset==len(stream);return result
committed=dict(zip(trees,batches(S,[v[1] for v in trees.values()])))
def body(path,pin=None,size=None,mode=None):
 st=path.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and path.resolve()==path
 raw=path.read_bytes();after=path.lstat();fields=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 assert fields(st)==fields(after)
 if pin is not None:assert sha(raw)==pin
 if size is not None:assert len(raw)==size
 if mode is not None:assert stat.S_IMODE(st.st_mode)==mode
 return raw
assert len(doc['source_entries'])==199 and sum(x['package_source'] for x in doc['source_entries'])==148
for row in doc['source_entries']:
 rel=row['target'];b=body(S/rel,row['sha256'],row['bytes']);assert b==committed[rel][2]==body(MAIN/row['origin'])
 assert stat.S_IMODE((S/rel).lstat().st_mode)==stat.S_IMODE((OLD/rel).lstat().st_mode)
 if rel not in changed:assert b==body(OLD/rel)
 else:
  assert sha(b)=='3ea9902ec4067edc59bc897081c5ad5f6738350ccd3a339b0b423c863212a97e'
  assert body(OLD/rel)==git(OLD,'show',PARENT+':'+rel)
 assert row['actual_git_commit']==HEAD
assert sum(r['bytes'] for r in doc['source_entries'])==3353171
for row in doc['retained_auxiliary_tracked_bodies']:
 rel=row['path'];b=body(S/rel,row['sha256'],row['bytes']);assert b==committed[rel][2]==body(OLD/rel)
 assert (S/rel).lstat().st_mode==(OLD/rel).lstat().st_mode
assert set(trees)=={r['target'] for r in doc['source_entries']}|{r['path'] for r in doc['retained_auxiliary_tracked_bodies']}
for row in doc['opaque_prior_inputs']:
 # Opaque byte/hash equality only; never parse NPY/data values.
 b=body(S/row['path'],row['sha256'],row['bytes'],row['mode']);assert b==body(Path(row['authenticated_source03']),mode=row['mode'])==body(Path(row['authenticated_original']),mode=row['mode'])
assert len(doc['opaque_prior_inputs'])==22 and sum(r['bytes'] for r in doc['opaque_prior_inputs'])==961506
rr=doc['runtime_role'];rbody=body(S/rr['path'],rr['sha256'],rr['bytes'],rr['mode']);assert rbody==body(OLD/rr['path'],mode=rr['mode']);runtime=json.loads(rbody)
records=runtime['distribution_records'];assert len(records)==251 and len({r['record'] for r in records})==251
record_bytes=sum(len(body(Path(r['record']),r['record_sha256'])) for r in records);assert record_bytes==5033917
assert sys.version.split()[0]==runtime['python'];assert str(Path(sys.executable).resolve())==runtime['resolved_executable']
body(Path(runtime['resolved_executable']),runtime['executable_sha256'],runtime['executable_bytes'])
assert sha(body(S/'uv.lock'))==sha(body(MAIN/'uv.lock'))==runtime['lock_sha256']
binding=json.loads((F/'held-consumer-original-git-runtime-root-binding01-2026-10-03/ORIGINAL_GIT_RUNTIME_BINDING01.json').read_bytes())
objects=batches(S,[r['object'] for r in binding['objects']]);assert len(objects)==34
for row,(oid,kind,b) in zip(binding['objects'],objects):assert oid==row['object'] and kind==row['type'] and len(b)==row['bytes'] and sha(b)==row['sha256']
paths=batches(S,[binding['actual_original_source']+':'+r['path'] for r in binding['source_paths']]);assert len(paths)==26
for row,(oid,kind,b) in zip(binding['source_paths'],paths):assert kind=='blob' and len(b)==row['bytes'] and sha(b)==row['sha256']
expected=set(trees)|{r['path'] for r in doc['opaque_prior_inputs']}|{rr['path']};actual=set();directories=[]
def scan(root):
 for entry in os.scandir(root):
  p=Path(entry.path);rel=p.relative_to(S).as_posix()
  if rel=='.git':continue
  info=entry.stat(follow_symlinks=False)
  if stat.S_ISDIR(info.st_mode):directories.append({'path':rel,'mode':stat.S_IMODE(info.st_mode)});scan(p)
  else:assert stat.S_ISREG(info.st_mode) and info.st_nlink==1;actual.add(rel)
scan(S);assert actual==expected and len(actual)==227
for d in directories:assert any(n.startswith(d['path']+'/') for n in expected),'extra empty directory'
assert not git(S,'diff','--name-only') and not git(S,'diff','--cached','--name-only')
assert set(git(S,'ls-files','--others','--exclude-standard').decode().splitlines())==expected-set(trees)
assert git(OLD,'rev-parse','HEAD').decode().strip()==PARENT
result={'scope':'actual local source/Git/opaque input/runtime metadata only','head':HEAD,'anchor':ANCHOR,'parent':PARENT,'changed':changed,'source_count':199,'package_count':148,'tracked':204,'source_bytes':3353171,'opaque_inputs':22,'opaque_input_bytes':961506,'non_git_files':227,'non_git_directories':directories,'C6_objects':34,'C6_selected_paths':26,'runtime_RECORDs':251,'runtime_RECORD_bytes':record_bytes,'untracked':sorted(expected-set(trees)),'no_claim_or_numeric_execution':True,'external_recovery_verified':False}
(H/'READBACK04.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS actual sole-parent empty snapshot/anchor lineage; one accepted changed package body; all199 origin/Git/current,148 anchor,204 tracked+5aux')
print('PASS227-file nonGit membership/modes,22opaque inputs961506B,251runtime RECORDs5033917B,34original C6objects and26lookups; no numerical imports/jobs/network')
