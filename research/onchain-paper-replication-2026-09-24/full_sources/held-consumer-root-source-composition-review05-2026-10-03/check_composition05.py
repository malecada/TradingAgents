"""Read-only actual source/history/opaque-byte review; no source imports."""
import hashlib,json,os,stat,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;MAIN=F.parents[2];R=F/'held-consumer-root-source-composition05-2026-10-03'
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(R/'SOURCE_COMPOSITION05.json').read_bytes();assert sha(raw)=='0b95109d971966225ef4e163d2f12cace7a930ac8d50afd25e5f449e230bad9f';doc=json.loads(raw)
S=Path(doc['source_root']);OLD=S.parent.parent/'held-score-consumer-native-20261003-04/source';HEAD='6c36d073598c9949c463cf56619bb9d3b7b59329';PARENT='fa9712c36daf2896ef3f6a8a8a5d99ec696cfdf4';ANCHOR='0cfc2c03200880534b7c91c2f16ac659a265a35b'
ENV=os.environ|{'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0'}
def git(root,*args,data=None):
 r=subprocess.run(['git','-c','protocol.allow=never','-C',str(root),*args],input=data,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);assert r.returncode==0,(args,r.stderr);return r.stdout
def batch(root,refs):
 raw=git(root,'cat-file','--batch',data=('\n'.join(refs)+'\n').encode());off=0;result=[]
 for ref in refs:
  end=raw.index(b'\n',off);oid,kind,size=raw[off:end].split();size=int(size);off=end+1;b=raw[off:off+size];off+=size;assert len(b)==size and raw[off:off+1]==b'\n';off+=1
  assert hashlib.sha1(kind+b' '+str(size).encode()+b'\0'+b).hexdigest()==oid.decode();result.append((oid.decode(),kind.decode(),b))
 assert off==len(raw);return result
def tree(root,ref):
 out={}
 for row in git(root,'ls-tree','-rz',ref).split(b'\0'):
  if row:
   left,name=row.split(b'\t',1);mode,kind,oid=left.decode().split();assert kind=='blob';out[name.decode()]=(mode,oid)
 return out
assert git(S,'rev-list','--parents','-n','1','HEAD').decode().split()==[HEAD,PARENT]
assert git(OLD,'rev-parse','HEAD').decode().strip()==PARENT
for root in (S,OLD):assert not (root/'.git/objects/info/alternates').exists()
newtree=tree(S,HEAD);oldtree=tree(S,PARENT);anchor=tree(S,ANCHOR);assert oldtree==tree(OLD,PARENT) and len(newtree)==len(oldtree)==204
changed=sorted(n for n in newtree if newtree[n]!=oldtree[n]);assert changed==['fixture_tools/capsule_builder01.py','fixture_tools/generate_inputs01.py','proof_tools/build_release_draft01.py']
newblobs=dict(zip(newtree,batch(S,[v[1] for v in newtree.values()])));oldblobs=dict(zip(oldtree,batch(OLD,[v[1] for v in oldtree.values()])))
def body(p,pin=None,size=None,mode=None):
 s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1
 b=p.read_bytes();t=p.lstat();sig=lambda q:(q.st_dev,q.st_ino,q.st_mode,q.st_nlink,q.st_size,q.st_mtime_ns,q.st_ctime_ns)
 assert sig(s)==sig(t)
 if pin is not None:assert sha(b)==pin
 if size is not None:assert len(b)==size
 if mode is not None:assert stat.S_IMODE(s.st_mode)==mode
 return b
entries=doc['source_entries'];assert len(entries)==199 and sum(r['package_source'] for r in entries)==148
for r in entries:
 n=r['target'];b=body(S/n,r['sha256'],r['bytes']);assert b==newblobs[n][2]==body(MAIN/r['origin']);assert r['actual_git_commit']==HEAD
 assert stat.S_IMODE((S/n).lstat().st_mode)==stat.S_IMODE((OLD/n).lstat().st_mode)
 assert body(OLD/n)==oldblobs[n][2]
 if r['package_source']:assert newtree[n]==anchor[n]==oldtree[n]
 elif n not in changed:assert b==oldblobs[n][2]
assert sum(r['bytes'] for r in entries)==3365188
for r in doc['retained_auxiliary_tracked_bodies']:
 n=r['path'];assert body(S/n,r['sha256'],r['bytes'])==newblobs[n][2]==body(OLD/n)==oldblobs[n][2];assert (S/n).lstat().st_mode==(OLD/n).lstat().st_mode
assert set(newtree)=={r['target'] for r in entries}|{r['path'] for r in doc['retained_auxiliary_tracked_bodies']}
extra=doc['copied_opaque_and_closed_history_files'];assert len(extra)==42 and len({r['path'] for r in extra})==42
for r in extra:assert body(S/r['path'],r['sha256'],r['bytes'],r['mode'])==body(Path(r['original_path']),mode=r['mode'])
binding=json.loads((F/'held-consumer-historical-admission-root-binding01-2026-10-03/HISTORY_BINDING01.json').read_bytes());plan=json.loads((MAIN/binding['copy_plan']['path']).read_bytes());C6=json.loads((F/'held-consumer-original-git-runtime-root-binding01-2026-10-03/ORIGINAL_GIT_RUNTIME_BINDING01.json').read_bytes())
for rows in (plan['objects'],C6['objects']):
 values=batch(S,[r['object'] for r in rows]);prior=batch(OLD,[r['object'] for r in rows]);assert values==prior
 for r,(oid,kind,b) in zip(rows,values):assert oid==r['object'] and kind==r['type'] and len(b)==r['bytes'] and sha(b)==r['sha256']
lookups=plan['logical_committed_lookups'];assert len(lookups)==638
values=batch(S,[r['commit']+':'+r['path'] for r in lookups]);assert values==batch(OLD,[r['commit']+':'+r['path'] for r in lookups])
for r,(oid,kind,b) in zip(lookups,values):assert oid==r['object'] and kind=='blob' and len(b)==r['bytes'] and sha(b)==r['sha256']
closures=[]
for row in binding['actual_old_claims']:
 d=S/'research_runs'/row['identity'];craw=(d/'claim.json').read_bytes();traw=(d/'failed.json').read_bytes();c=json.loads(craw);t=json.loads(traw)
 assert sha(craw)==row['claim_sha256'] and sha(traw)==row['terminal_sha256'] and t['claim_sha256']==sha(craw) and t['status']=='failed' and not (d/'complete.json').exists()
 actual={p.name for p in (d/'outputs').iterdir()};assert actual==set(t['output_sha256'])
 for n,pin in t['output_sha256'].items():assert sha((d/'outputs'/n).read_bytes())==pin
 closures.append({'identity':row['identity'],'terminal':'failed','outputs':sorted(actual),'missing':sorted(set(c['experiment']['outputs'])-actual)})
assert [len(r['outputs']) for r in closures]==[4,4,2,1]
expected=set(newtree)|{r['path'] for r in extra};actual=set()
def scan(root):
 for e in os.scandir(root):
  p=Path(e.path);n=p.relative_to(S).as_posix()
  if n=='.git':continue
  st=e.stat(follow_symlinks=False)
  if stat.S_ISDIR(st.st_mode):assert any(k.startswith(n+'/') for k in expected);scan(p)
  else:assert stat.S_ISREG(st.st_mode) and st.st_nlink==1;actual.add(n)
scan(S);assert actual==expected and len(actual)==246
assert set(git(S,'ls-files','--others','--exclude-standard').decode().splitlines())==expected-set(newtree)
assert not git(S,'diff','--name-only') and not git(S,'diff','--cached','--name-only')
assert git(S,'rev-parse','HEAD').decode().strip()==HEAD and git(OLD,'rev-parse','HEAD').decode().strip()==PARENT
out={'scope':'local byte/Git composition only; no imported source or authority execution','head':HEAD,'parent':PARENT,'unchanged_package_anchor':ANCHOR,'changed':changed,'selected_sources':199,'package_sources':148,'tracked':204,'non_git_files':246,'copied_extra_files':42,'copied_extra_bytes':sum(r['bytes'] for r in extra),'source_bytes':3365188,'history_objects':222,'original_C6_objects':34,'historical_lookups':638,'old_claims':closures,'new_claims_jobs':0,'external_recovery_verified':False}
(H/'READBACK05.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS actual6c36 solechildfa9712; exact3helpers/199origins/148anchor/204tracked;42retainedextras/modes+246exactnonGit;222history+34C6objects/638lookups;Source04 unchanged;failedcounts4/4/2/1')
