"""One-use actual remote return of exactly three final39 public metadata bodies."""
import datetime,hashlib,json,os,re,stat,subprocess,sys
from pathlib import Path
F='research/onchain-paper-replication-2026-09-24/full_sources/'
ENTRY=F+'real-data-pilot-full39-entry-preparation01-2026-10-12/'
PATHS=(ENTRY+'BINDING01.json',ENTRY+'RELEASE_REVIEW01.json',F+'pilot39-final-entry-review-2026-10-12/BINDING_REVIEW02.json')
PRIOR=F+'real-data-pilot-full24-preparation-increment01-2026-10-09/full39entry36/FRESH_GIT_RECOVERY36.json'
LIMIT=4*1024**2
sha=lambda b:hashlib.sha256(b).hexdigest()
def read_pin(root,ref):
 assert set(ref)=={'path','sha256','bytes','mode'}
 assert isinstance(ref['bytes'],int) and not isinstance(ref['bytes'],bool) and 0<=ref['bytes']<=LIMIT
 assert re.fullmatch('[0-9a-f]{64}',ref['sha256']) and re.fullmatch('0[0-7]{3}',ref['mode'])
 p=root/ref['path'];assert p.resolve(strict=True)==p and p.is_relative_to(root)
 before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==ref['bytes']
 assert format(stat.S_IMODE(before.st_mode),'04o')==ref['mode']
 with p.open('rb') as f:body=f.read(LIMIT+1)
 after=p.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
 assert len(body)==ref['bytes'] and sha(body)==ref['sha256']
 return body
def main():
 R=Path.cwd().resolve();input_path=Path(sys.argv[1]);assert input_path.stat().st_size<=LIMIT
 with input_path.open('rb') as f:raw=f.read(LIMIT+1)
 assert len(raw)<=LIMIT;spec=json.loads(raw)
 assert set(spec)=={'source','prior_recovery','files'} and re.fullmatch('[0-9a-f]{40}',spec['source'])
 assert len(spec['files'])==3 and tuple(x['path'] for x in spec['files'])==PATHS
 assert spec['prior_recovery']['path']==PRIOR
 prior=json.loads(read_pin(R,spec['prior_recovery']))
 B=R.parent/'onchain-pilot-recovery/real-pilot-entry39-20261012-36.git'
 assert prior['fresh_bare']==str(B) and prior['no_alternates'] is True
 assert B.resolve(strict=True)==B and B.is_dir() and not (B/'objects/info/alternates').exists()
 bodies=[read_pin(R,x) for x in spec['files']]
 D=R/ENTRY/'final-metadata-return01';D.mkdir() # exclusive reservation before Git operations
 (D/'INPUT01.json').write_text(json.dumps(spec,indent=2)+'\n');ops=[]
 def run(name,args,cwd=R):
  p=subprocess.run(args,cwd=cwd,capture_output=True,timeout=60,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GIT_NO_LAZY_FETCH':'1'})
  for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
   with (D/(name+'.'+k)).open('xb') as f:f.write(b)
  ops.append({'operation':name,'exit_code':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':sha(p.stdout),'stderr_bytes':len(p.stderr),'stderr_sha256':sha(p.stderr)})
  (D/'GIT_OPERATIONS01.json').write_text(json.dumps(ops,indent=2,sort_keys=True)+'\n')
  assert p.returncode==0,(name,p.returncode)
  return p.stdout
 source=run('local_head',['git','rev-parse','HEAD']).decode().strip();assert source==spec['source']
 remote=run('remote_get_url',['git','remote','get-url','origin']).decode().strip()
 assert run('bare_remote_get_url',['git','remote','get-url','origin'],B).decode().strip()==remote
 branch='refs/heads/research/onchain-paper-replication-2026-09-24'
 remotehead=run('remote_actual_branch_readback',['git','ls-remote','origin',branch]).decode().split();assert remotehead==[source,branch]
 oids=[]
 for i,(ref,body) in enumerate(zip(spec['files'],bodies)):
  line=run(f'local_tree_join{i}',['git','ls-tree',source,'--',ref['path']]).decode().strip()
  left,path=line.split('\t');mode,kind,oid=left.split();assert path==ref['path'] and kind=='blob' and mode==('100755' if int(ref['mode'],8)&0o111 else '100644') and re.fullmatch('[0-9a-f]{40}',oid)
  assert run(f'local_blob{i}',['git','-c','remote.origin.promisor=false','cat-file','blob',oid])==body
  oids.append(oid)
 run('actual_external_commit_only_fetch',['git','fetch','--depth=1','--filter=tree:0','origin',source],B)
 head=run('fetched_head_readback',['git','rev-parse','FETCH_HEAD'],B).decode().strip();assert head==source
 local=run('local_commit_body',['git','-c','remote.origin.promisor=false','cat-file','commit',source])
 commit=run('actual_external_commit_body',['git','-c','remote.origin.promisor=false','cat-file','commit',source],B);assert local==commit
 returned=[]
 for i,(ref,oid) in enumerate(zip(spec['files'],oids)):
  run(f'actual_external_selected_blob_fetch{i}',['git','fetch','--no-tags','--no-write-fetch-head','--filter=tree:0','origin',oid],B)
  body=run(f'actual_external_blob_return{i}',['git','-c','remote.origin.promisor=false','cat-file','blob',oid],B)
  assert len(body)==ref['bytes'] and sha(body)==ref['sha256'] and body==read_pin(R,ref)
  returned.append({'original':ref,'git_blob_oid':oid,'returned_path':str((D/f'actual_external_blob_return{i}.stdout').relative_to(R))})
 assert run('final_local_head',['git','rev-parse','HEAD']).decode().strip()==source
 assert not (B/'objects/info/alternates').exists()
 receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'actual_external_source':remote,'actual_remote_head':remotehead[0],'actual_fetch_head':head,'existing_fresh_bare':str(B),'prior_recovery':spec['prior_recovery'],'commit_body_sha256':sha(commit),'returned':returned,'operations':ops,'no_alternates':True,'qualification':'Actual return of exactly three final public metadata bodies; no archive, historical traversal, POSIX reconstruction, runtime body or whole-tree recovery claim.'}
 with (D/'FINAL_METADATA_RETURN01.json').open('x') as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps({'status':'ACTUAL_THREE_FINAL_METADATA_RETURN','source':source,'files':3}))
if __name__=='__main__':main()
