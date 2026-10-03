from pathlib import Path
import hashlib,json,os,stat,subprocess,time
R=Path(__file__).resolve().parent;B=R.parent;MAIN=B.parents[2];A=B/'held-consumer-final-released-scope-root-remote-recovery01-2026-10-03'
H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes())
selection=J(A/'SELECTED_BODIES03.json');receipt=J(A/'REMOTE_RECOVERY03.json');rows=selection['rows'];commit=selection['remote_commit'];repo=A/'fresh-final01.git'
assert commit==receipt['remote_commit']=='a9f18fffbc06b9e3996b67fc2a0139ce98900709'
assert H((A/'SELECTED_BODIES03.json').read_bytes())==receipt['selection_sha256']=='7bde62d8a3a549561b879320c672f77b662bc256f141dd47b96569e918447625'
assert len(rows)==receipt['selected_count']==431 and sum(x['bytes'] for x in rows)==receipt['selected_logical_bytes']==12674060
assert H((A/'recover_final03.py').read_bytes())=='6b4d6671f852ab6893a2219c4185efb7106253b3bf48eb07da500bafe54dbfce'
assert receipt['fresh_git_root']==str(repo) and receipt['genuine_run_or_native_started'] is False
assert receipt['origin']=='git@github.com:malecada/TradingAgents.git' and receipt['branch']=='refs/heads/research/onchain-paper-replication-2026-09-24'
ops=receipt['operations'];assert all(x['exit']==0 and x['cleanup_failures']==[] for x in ops) and len(ops)<1024
remote=[x for x in ops if x['operation']=='ls-remote'];assert len(remote)==2
remote_body=(commit+'\t'+receipt['branch']+'\n').encode()
assert all(x['stdout_bytes']==len(remote_body) and x['stdout_sha256']==H(remote_body) for x in remote)
assert all(not (Path('/proc')/str(x['pid'])).exists() for x in ops)
names=[x['path'] for x in rows];assert names==sorted(set(names)) and all(x['path'].startswith('research/') and '..' not in Path(x['path']).parts and x['bytes']<=4194304 for x in rows)
expected={x['path']:x for x in receipt['selected_blobs']};assert set(expected)==set(names)
env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0','GIT_ALLOW_PROTOCOL':''}
def git(args,request=b''):
 r=subprocess.run(['git','-c','protocol.allow=never',*args],cwd=repo,env=env,input=request,capture_output=True,timeout=30);assert r.returncode==0,(args[0],r.stderr[:200]);assert len(r.stdout)<=64*1024**2 and len(r.stderr)<=65536;return r.stdout
assert git(['rev-parse',commit+'^{commit}']).decode().strip()==commit
raw=git(['ls-tree','-r','-z',commit,'--',*names]);trees={}
for item in raw.split(b'\0')[:-1]:
 head,name=item.split(b'\t',1);mode,kind,oid=head.decode().split();trees[name.decode()]=(mode,kind,oid)
assert set(trees)==set(names)
response=git(['cat-file','--batch'],''.join(commit+':'+n+'\n' for n in names).encode());off=0
for row in rows:
 n=row['path'];end=response.index(b'\n',off);head=response[off:end].split();assert len(head)==3 and head[1]==b'blob';size=int(head[2]);assert size==row['bytes'];start=end+1;body=response[start:start+size];assert response[start+size:start+size+1]==b'\n';off=start+size+1
 mode,kind,oid=trees[n];assert kind=='blob' and mode in ('100644','100755') and head[0].decode()==oid==hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest()
 assert expected[n]==dict(row,git_mode=mode,git_object=oid)
 saved=A/'selected'/n;s=saved.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and saved.resolve()==saved
 assert H(body)==row['sha256'] and saved.read_bytes()==body==(MAIN/n).read_bytes()
assert off==len(response)
actual=[]
for parent,dirs,files in os.walk(A/'selected',followlinks=False):
 for n in dirs:
  p=Path(parent)/n;assert stat.S_ISDIR(p.lstat().st_mode) and p.resolve()==p
 for n in files:actual.append((Path(parent)/n).relative_to(A/'selected').as_posix())
assert sorted(actual)==names
# Both archive scopes and all new final parent body donors must be in the real selection.
for folder in ('held-consumer-final-released-scope-root-capture01-2026-10-03','held-consumer-final-baseline-root-capture01-2026-10-03'):
 for suffix in ('REQUEST01.json','bundle01/capture.json','bundle01/capsule-manifest.json','bundle01/external-manifest.json','bundle01/capsule.tar.gz','bundle01/external.tar.gz'):
  assert str((B/folder/suffix).relative_to(MAIN)) in names
out={'schema_version':1,'decision':'accepted_actual_selected_remote_file_bodies_only_pending_final_flat_union','receipt_sha256':H((A/'REMOTE_RECOVERY03.json').read_bytes()),'selection_sha256':receipt['selection_sha256'],'remote_commit':commit,'actual_git_blobs':431,'selected_logical_bytes':12674060,'git_calls_by_reviewer':3,'root_recorded_operations':len(ops),'root_recorded_elapsed_seconds':receipt['elapsed_seconds'],'all_recorded_operation_pids_absent':True,'actual_selected_membership_exact':True,'final_union_accepted':False,'source_execution_or_network_by_reviewer':False}
(R/'ORIGIN_READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
