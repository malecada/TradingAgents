import hashlib,json,os,pathlib,stat,subprocess
P=pathlib.Path; HERE=P(__file__).resolve().parent; MAIN=HERE.parents[3]; F=HERE.parent
R=F/'neural-cold-feature-handoff-held-consumer-root-source-composition02-2026-10-03'
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and 0<=s.st_size<=4194304
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns);return b
def sha(b):return hashlib.sha256(b).hexdigest()
def git(root,*args,inp=None):
 env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'}
 return subprocess.run(['git','-c','protocol.allow=never','-C',str(root),*args],input=inp,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=15,env=env).stdout
v=json.loads(read(R/'SOURCE_COMPOSITION02.json'));src=P(v['source_root']);A=v['authentic_parent_anchor'];S=v['actual_148_package_anchor'];T=v['actual_199_source_execution_commit']
for x in (A,S,T):assert len(x)==40 and all(c in '0123456789abcdef' for c in x)
assert git(src,'rev-parse','HEAD').decode().strip()==T
assert git(src,'rev-list','--parents','-n','1',S).decode().split()==[S,A]
assert git(src,'rev-list','--parents','-n','1',T).decode().split()==[T,S]
assert not (src/'.git/objects/info/alternates').exists()
def tree(root,c):
 out={}
 for r in git(root,'ls-tree','-r','-z',c).split(b'\0'):
  if not r:continue
  head,name=r.split(b'\t');mode,typ,oid=head.decode().split();assert typ=='blob' and mode=='100644';out[name.decode()]=oid
 return out
def bodies(root,c,names):
 raw=git(root,'cat-file','--batch',inp=b''.join((c+':'+n+'\n').encode() for n in names));pos=0;out={}
 for n in names:
  end=raw.index(b'\n',pos);oid,typ,size=raw[pos:end].split();assert typ==b'blob';size=int(size);assert size<=4194304;pos=end+1;out[n]=raw[pos:pos+size];pos+=size;assert raw[pos:pos+1]==b'\n';pos+=1
 assert pos==len(raw);return out
tr={c:tree(src,c) for c in (A,S,T)};assert [len(tr[c]) for c in (A,S,T)]==[200,201,204]
bs={c:bodies(src,c,sorted(tr[c])) for c in (A,S,T)}
rows=v['source_entries'];assert len(rows)==len({r['target'] for r in rows})==199
package={r['target'] for r in rows if r['package_source']};assert len(package)==148
actualpkg={p.as_posix() for p in (P(n) for n in tr[T]) if (p.parent.as_posix() in ('tradingagents/research','tradingagents/research/onchain_replication') and p.suffix=='.py') or p.as_posix()=='tradingagents/__init__.py'};assert package==actualpkg
for r in rows:
 n=r['target'];b=bs[T][n];assert len(b)==r['bytes'] and sha(b)==r['sha256'];assert b==read(MAIN/r['origin'])==read(src/n)
 assert r['actual_git_commit']==(S if n in package else T)
 if n in package:assert bs[S][n]==b
aux=v['retained_auxiliary_tracked_bodies'];assert len(aux)==5;assert set(tr[T])-set(r['target'] for r in rows)==set(a['path'] for a in aux)
for a in aux:
 n=a['path'];assert bs[A][n]==bs[S][n]==bs[T][n]==read(src/n);assert sha(bs[T][n])==a['sha256'] and len(bs[T][n])==a['bytes']
assert set(tr[A])<=set(tr[S])<=set(tr[T])
assert set(tr[S])-set(tr[A])=={'tradingagents/research/onchain_replication/held_score_consumer.py'}
assert set(tr[T])-set(tr[S])==set(r['target'] for r in rows if r['change']=='add' and not r['package_source'])
assert {n for n in tr[A] if bs[A][n]!=bs[S][n]}=={'tradingagents/research/verify.py','tradingagents/research/onchain_replication/compact_mcm.py','tradingagents/research/onchain_replication/mcm_score_stream.py'}
assert all(bs[S][n]==bs[T][n] for n in tr[S])
old=P('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');B='361339125a3f1cd57e7ba8611f5a994ae649fa0b';assert git(old,'rev-parse','HEAD').decode().strip()==B
inv=json.loads(read(F/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03/source_inventory04.json'))
ob=bodies(old,B,[r['target'] for r in inv['source_inventory']])
for r in inv['source_inventory']:assert sha(ob[r['target']])==r['sha256'] and ob[r['target']]==read(old/r['target'])
fail=json.loads(read(F/'neural-cold-feature-handoff-held-consumer-root-source-composition01-2026-10-03/SOURCE_COMPOSITION_FAILURE01.json'));clone=P(fail['partial_source_root']);assert clone.exists();assert len(fail['malformed_requested_anchor'])==41
clonehead=git(clone,'rev-parse','HEAD').decode().strip();assert clonehead==B
cb=bodies(clone,B,[r['target'] for r in inv['source_inventory']])
for r in inv['source_inventory']:assert cb[r['target']]==ob[r['target']]
assert {x.name for x in clone.iterdir()}=={'.git'}
for root in (src,clone):
 for n in ('research_runs','research_artifacts/proof_supervise','research_artifacts/proof_outer'):assert not os.path.lexists(root/n)
manifest=json.loads(read(R/'MANIFEST02.json'))
for r in manifest['files']:b=read(R/r['path']);assert len(b)==r['bytes'] and sha(b)==r['sha256']
# Main source held stable against its own committed state, not the capsule baseline.
mainheads={}
for n in ('tradingagents/research/verify.py','tradingagents/research/onchain_replication/compact_mcm.py','tradingagents/research/onchain_replication/mcm_score_stream.py'):
 b=read(MAIN/n);assert b==git(MAIN,'show','HEAD:'+n);mainheads[n]=sha(b)
result={'status':'PASS exact source composition only','source_receipt_sha256':sha(read(R/'SOURCE_COMPOSITION02.json')),'anchor_parent':A,'anchor':S,'execution':T,'tree_counts':[200,201,204],'sources':199,'package':148,'auxiliary':5,'source_bytes':sum(r['bytes'] for r in rows),'old_B2_sources_unchanged':195,'failed_clone01_HEAD':clonehead,'failed_clone01_Git_source_objects_unchanged':195,'failed_clone01_worktree':'only .git; no checkout occurred','main_current_source_hashes':mainheads,'network':0,'numerical_imports':0,'claims':0,'qualification':'No release/runtime/registration/whole old capsule non-source tree assertion.'}
(HERE/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
