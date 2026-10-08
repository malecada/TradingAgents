import hashlib,json,os,subprocess,tarfile
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'real-data-pilot-twentieth-failed-increment01-2026-10-08';H=Path(__file__).resolve().parent;checks=[];evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p,h=None):
 b=p.read_bytes();digest=sha(b);assert h is None or digest==h;evidence[str(p.relative_to(R))]=digest;return json.loads(b)
def check(n,v):
 assert v,n
 checks.append(n)
m=load(D/'FRESH_GIT_RECOVERY01.json');capture=load(R/m['capture']['path'],m['capture']['sha256']);s=load(R/capture['selection']['path'],capture['selection']['sha256']);bare=Path(m['fresh_bare']);env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0')
def git(args,bared=False):
 p=subprocess.run(['git']+(['--git-dir='+str(bare)] if bared else [])+args,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);assert p.returncode==0,(args,p.returncode);return p.stdout
check('13_operations_successful',len(m['operations'])==13 and all(o['exit_code']==0 for o in m['operations']))
check('source_remote_fetch',m['source']==m['actual_remote_head']==m['actual_fetch_head']=='7a5af7914eb8ab4f78223b739ff3863c9bdceda0')
check('no_alternates',not (bare/'objects/info/alternates').exists() and not os.environ.get('GIT_ALTERNATE_OBJECT_DIRECTORIES'))
check('bare',git(['rev-parse','--is-bare-repository'],True).strip()==b'true')
commit=git(['cat-file','commit',m['source']],True);check('fetched_commit_body',commit==git(['cat-file','commit',m['source']]) and sha(commit)==m['commit_body_sha256'])
check('commit_oid',hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==m['source'])
check('fetch_head',git(['rev-parse','FETCH_HEAD'],True).decode().strip()==m['source'])
check('remote_url',git(['config','--get','remote.origin.url'],True).decode().strip()==m['actual_external_source'])
tree=git(['ls-tree',m['source'],'--',capture['archive']['path']]).decode().strip();check('committed_tree_join',tree==m['local_commit_tree_join'] and tree.split()[2]==m['archive_git_blob_oid'])
body=(R/m['returned_archive']['path']).read_bytes();evidence[m['returned_archive']['path']]=sha(body)
check('archive_extent_digest',len(body)==m['returned_archive']['bytes']==capture['archive']['bytes']==512000 and sha(body)==m['returned_archive']['sha256']==capture['archive']['sha256'])
check('archive_blob_oid',hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==m['archive_git_blob_oid'])
check('fetched_blob',git(['cat-file','blob',m['archive_git_blob_oid']],True)==body)
check('original_archive_identical',(R/capture['archive']['path']).read_bytes()==body)
rows={r['path']:r for r in s['rows']};dirs={r['path']:r for r in s['directories']};check('selected_totals',len(rows)==s['files']==capture['files']==39 and len(dirs)==capture['directories']==11 and sum(r['bytes'] for r in rows.values())==s['body_bytes']==capture['regular_bytes']==437725)
seen=set()
with tarfile.open(R/m['returned_archive']['path'],'r:') as t:
 for member in t:
  name=member.name.rstrip('/');check('selected_unique_'+name,name not in seen and name in rows.keys()|dirs.keys() and not Path(name).is_absolute() and '..' not in Path(name).parts);seen.add(name)
  row=(rows|dirs)[name];check('mode_'+name,member.mode==int(row['mode'],8))
  if row['type']=='directory':check('directory_'+name,member.isdir())
  else:
   check('regular_'+name,member.isfile() and member.size==row['bytes']);data=t.extractfile(member).read();check('opaque_hash_'+name,sha(data)==row['sha256'] and sha((R/name).read_bytes())==row['sha256'])
check('exact_selected_names',seen==rows.keys()|dirs.keys())
root='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final20-2026-10-08/';check('actual_outer_terminal_included',root+'ROOT_TERMINAL01.json' in rows)
check('private_runtime_excluded',not any(p.startswith('research_artifacts/real_pilot_runtime/') for p in rows))
v={'decision':'accepted','status':'EXACT_FAILED20_PUBLIC_INCREMENT_RECOVERED','identity':s['identity'],'source':m['source'],'evidence':evidence,'checks':checks,'files':39,'directories':11,'body_bytes':437725,'returned_archive':m['returned_archive'],'archive_git_blob_oid':m['archive_git_blob_oid'],'offline_git_no_lazy_fetch':True,'qualification':'Exact declared39-file/11-directory public failed20 increment recovered with original selected names/types/modes and opaque bytes. Commit-only fresh external receipt independently joins offline fetched commit/blob and local committed tree. No whole-tree, private/runtime/scientific-store, POSIX ownership/xattr/hardlink reconstruction, deletion, numerical completion or new admission proof. Earlier recovery evidence reused; no old tree retrieval or job.'}
(H/'RECOVERY_REVIEW01.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted','checks':len(checks),'sha256':sha((H/'RECOVERY_REVIEW01.json').read_bytes())}))
