"""Recover the one declared fresh21 changed public entry from the actual remote."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path.cwd();D=Path(__file__).resolve().parent
B=R.parent/'onchain-pilot-recovery/real-pilot-entry-20261008-21-01.git'
assert not B.exists() and not (D/'FRESH_GIT_RECOVERY01.json').exists()
ops=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def run(name,args,cwd=R):
 p=subprocess.run(args,cwd=cwd,capture_output=True,timeout=60,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
 for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
  with (D/(name+'.'+k)).open('xb') as f:f.write(b)
 ops.append({'operation':name,'exit_code':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':sha(p.stdout),'stderr_bytes':len(p.stderr),'stderr_sha256':sha(p.stderr)})
 (D/'GIT_OPERATIONS01.json').write_text(json.dumps(ops,indent=2,sort_keys=True)+'\n')
 assert p.returncode==0,(name,p.returncode)
 return p.stdout
cap=json.loads((D/'CAPTURE01.json').read_bytes());a=cap['archive'];source=run('local_head',['git','rev-parse','HEAD']).decode().strip();remote=run('remote_get_url',['git','remote','get-url','origin']).decode().strip();branch='refs/heads/research/onchain-paper-replication-2026-09-24'
remotehead=run('remote_actual_branch_readback',['git','ls-remote','origin',branch]).decode().split()[0];assert remotehead==source
join=run('local_archive_git_tree_join',['git','ls-tree',source,'--',a['path']]).decode().strip();parts=join.split();assert parts[:2]==['100644','blob'] and parts[3]==a['path'];blob=parts[2]
run('fresh_bare_init',['git','init','--bare','--quiet',str(B)]);run('fresh_remote_add',['git','remote','add','origin',remote],B);run('set_promisor',['git','config','remote.origin.promisor','true'],B);run('set_tree_zero_filter',['git','config','remote.origin.partialclonefilter','tree:0'],B)
run('actual_external_commit_only_fetch',['git','fetch','--depth=1','--filter=tree:0','origin',source],B);head=run('fetched_head_readback',['git','rev-parse','FETCH_HEAD'],B).decode().strip();assert head==source
body=run('actual_external_commit_body',['git','cat-file','commit',source],B);assert body==subprocess.check_output(['git','cat-file','commit',source],cwd=R)
run('actual_external_selected_blob_fetch',['git','fetch','--no-tags','--no-write-fetch-head','--filter=tree:0','origin',blob],B);returned=run('actual_external_archive_blob_return',['git','cat-file','blob',blob],B);assert len(returned)==a['bytes'] and sha(returned)==a['sha256'];assert not (B/'objects/info/alternates').exists()
out=D/'fresh-git-recovered-increment01.tar';out.write_bytes(returned)
v={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'actual_external_source':remote,'actual_remote_head':remotehead,'actual_fetch_head':head,'fresh_bare':str(B),'archive_git_blob_oid':blob,'local_commit_tree_join':join,'commit_body_sha256':sha(body),'operations':ops,'no_alternates':True,'capture':{'path':str((D/'CAPTURE01.json').relative_to(R)),'sha256':sha((D/'CAPTURE01.json').read_bytes())},'returned_archive':{'path':str(out.relative_to(R)),'bytes':len(returned),'sha256':sha(returned)},'qualification':'Actual fresh remote commit-only/direct selected blob recovery. Complete declared fresh21 changed public entry only; private runtime/scientific stores/whole tree/POSIX reconstruction/deletion excluded.'}
(D/'FRESH_GIT_RECOVERY01.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'ACTUAL_SELECTED_EXTERNAL_RETURN','source':source,'bytes':len(returned),'sha256':sha(returned)}))
