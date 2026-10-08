import hashlib,json,os,subprocess,tarfile
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'real-data-pilot-diagnostic-entry-increment01-2026-10-08';H=Path(__file__).resolve().parent
checks=[];evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]=sha(b);return json.loads(b)
def check(n,v):
 assert v,n
 checks.append(n)
m=load(D/'FRESH_GIT_RECOVERY02.json');s=load(D/'SELECTION01.json');bare=Path(m['fresh_bare']);env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1')
def git(args,bared=False):
 cmd=['git']+(['--git-dir='+str(bare)] if bared else [])+args
 v=subprocess.run(cmd,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=30)
 assert v.returncode==0,(args,v.returncode,v.stderr.decode(errors='replace'))
 return v.stdout
check('thirteen_successful_operations',len(m['operations'])==13 and all(x['exit_code']==0 for x in m['operations']))
check('source_remote_fetch_identity',m['source']==m['actual_remote_head']==m['actual_fetch_head']=='6977044f689a003c19dfe59f9cf808a6ec852a8c')
check('no_alternates',not (bare/'objects/info/alternates').exists() and not os.environ.get('GIT_ALTERNATE_OBJECT_DIRECTORIES'))
check('bare_confirmed',git(['rev-parse','--is-bare-repository'],True).strip()==b'true')
commit=git(['cat-file','commit',m['source']],True);local=git(['cat-file','commit',m['source']])
check('fetched_commit_equals_local',commit==local and sha(commit)==m['commit_body_sha256'])
check('commit_oid_authenticated',hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==m['source'])
# FETCH_HEAD is retained commit-only retrieval; blob fetch used --no-write-fetch-head.
check('actual_fetch_head',git(['rev-parse','FETCH_HEAD'],True).decode().strip()==m['source'])
archive_path='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-diagnostic-entry-increment01-2026-10-08/public-increment01.tar'
tree=git(['ls-tree',m['source'],'--',archive_path]).decode().strip()
check('local_commit_tree_binding',tree==m['local_commit_tree_join'] and tree.split()[2]==m['archive_git_blob_oid'])
check('remote_config_identity',git(['config','--get','remote.origin.url'],True).decode().strip()==m['actual_external_source'])
returned=R/m['returned_archive']['path'];body=returned.read_bytes();evidence[m['returned_archive']['path']]=sha(body)
check('returned_archive_extent_digest',len(body)==m['returned_archive']['bytes']==2846720 and sha(body)==m['returned_archive']['sha256'])
check('returned_archive_blob_oid',hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==m['archive_git_blob_oid'])
check('fetched_blob_equals_returned',git(['cat-file','blob',m['archive_git_blob_oid']],True)==body)
rows={x['path']:x for x in s['rows']};check('selection_unique_count',len(rows)==len(s['rows'])==171)
check('selected_total_extent',sum(x['bytes'] for x in rows.values())==2694294)
seen=set();directories=[]
with tarfile.open(returned,'r:') as archive:
 for member in archive:
  name=member.name.rstrip('/')
  check('safe_path_'+name,not Path(name).is_absolute() and '..' not in Path(name).parts)
  if member.isdir():directories.append(name);continue
  check('selected_regular_'+name,member.isfile() and name in rows and name not in seen)
  data=archive.extractfile(member).read();row=rows[name]
  check('member_hash_'+name,len(data)==member.size==row['bytes'] and sha(data)==row['sha256'])
  # Original selected controls/source only; scientific/runtime stores excluded.
  check('original_selected_hash_'+name,sha((R/name).read_bytes())==row['sha256'])
  seen.add(name)
check('all_selected_returned',seen==set(rows))
check('directories_only_selected_ancestors',all(any(p.startswith(d+'/') for p in seen) for d in directories))
final='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final20-2026-10-08/'
for name in ('gate02.json','preflight02.py','root_io02.py','BINDING01.json','RELEASE_REVIEW01.json'):
 check('entry_returned_'+name,final+name in seen)
check('changed_main_source_present',any(p.startswith('tradingagents/research/onchain_replication/') for p in seen))
check('private_runtime_excluded',all(not p.startswith(('research_artifacts/','research_runs/')) and not any(x in Path(p).parts for x in ('keys','apis','.env')) for p in seen))
result={'decision':'accepted','status':'EXACT_RETURNED_PUBLIC_INCREMENT_VERIFIED','identity':s['identity'],'source':m['source'],'archive_git_blob_oid':m['archive_git_blob_oid'],'returned_archive':m['returned_archive'],'selection_files':len(rows),'selected_body_bytes':sum(x['bytes'] for x in rows.values()),'evidence':evidence,'checks':checks,'fresh_bare':str(bare),'offline_git_no_lazy_fetch':True,'qualification':'Actual fresh external retrieval receipt plus independent offline fetched commit/blob and every selected returned member verification. Commit-only tree:0 fetch and direct selected archive blob; local cryptographic committed-tree binding verified. No whole-tree, POSIX reconstruction, private transport/runtime/scientific-store, deletion, capacity, admission or native execution proof. Original failed01 timeout and temporary pack remain untouched; no rerun.'}
(H/'RECOVERY_REVIEW02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'decision':'accepted','files':len(rows),'body_bytes':result['selected_body_bytes'],'checks':len(checks),'review_sha256':sha((H/'RECOVERY_REVIEW02.json').read_bytes())}))
