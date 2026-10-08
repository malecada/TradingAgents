import hashlib,json,os,subprocess,tarfile
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'real-data-pilot-entry21-increment01-2026-10-08';N=F/'real-data-pilot-final21-2026-10-08';H=Path(__file__).resolve().parent;checks=[];evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p,h=None):
 b=p.read_bytes();x=sha(b);assert h is None or x==h;evidence[str(p.relative_to(R))]=x;return json.loads(b)
def check(n,v):
 assert v,n
 checks.append(n)
m=load(D/'FRESH_GIT_RECOVERY01.json');capture=load(R/m['capture']['path'],m['capture']['sha256']);s=load(D/'SELECTION01.json');bare=Path(m['fresh_bare']);env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0')
def git(args,bared=False):
 v=subprocess.run(['git']+(['--git-dir='+str(bare)] if bared else [])+args,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);assert v.returncode==0,(args,v.returncode);return v.stdout
check('13_operations_successful',len(m['operations'])==13 and all(x['exit_code']==0 for x in m['operations']))
check('source_remote_fetch',m['source']==m['actual_remote_head']==m['actual_fetch_head']=='c047a35206e16da00c3a0f261142e26d48ea266d')
check('no_alternates',not (bare/'objects/info/alternates').exists() and not os.environ.get('GIT_ALTERNATE_OBJECT_DIRECTORIES'))
check('bare',git(['rev-parse','--is-bare-repository'],True).strip()==b'true')
commit=git(['cat-file','commit',m['source']],True);check('commit_body',commit==git(['cat-file','commit',m['source']]) and sha(commit)==m['commit_body_sha256'])
check('commit_oid',hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==m['source'])
check('fetch_head',git(['rev-parse','FETCH_HEAD'],True).decode().strip()==m['source'])
check('actual_remote',git(['config','--get','remote.origin.url'],True).decode().strip()==m['actual_external_source'])
tree=git(['ls-tree',m['source'],'--',capture['archive']['path']]).decode().strip();check('local_committed_tree_join',tree==m['local_commit_tree_join'] and tree.split()[2]==m['archive_git_blob_oid'])
body=(R/m['returned_archive']['path']).read_bytes();evidence[m['returned_archive']['path']]=sha(body)
check('returned_extent_digest',len(body)==m['returned_archive']['bytes']==capture['archive']['bytes']==2508800 and sha(body)==m['returned_archive']['sha256']==capture['archive']['sha256'])
check('blob_oid',hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==m['archive_git_blob_oid'])
check('actual_bare_blob_return',git(['cat-file','blob',m['archive_git_blob_oid']],True)==body)
check('original_capture_bytes',(R/capture['archive']['path']).read_bytes()==body)
rows={r['path']:r for r in s['rows']};check('selection_extent',len(rows)==len(s['rows'])==s['files']==capture['files']==142 and sum(r['bytes'] for r in rows.values())==s['regular_bytes']==capture['regular_bytes']==2388151)
seen=set();dirs=[]
with tarfile.open(R/m['returned_archive']['path'],'r:') as t:
 for member in t:
  name=member.name.rstrip('/');check('safe_path_'+name,not Path(name).is_absolute() and '..' not in Path(name).parts)
  if member.isdir():dirs.append(name);continue
  check('regular_unique_'+name,member.isfile() and name in rows and name not in seen);seen.add(name);row=rows[name]
  # Git archive records canonical regular modes; original selected local mode
  #0664 has the same executable-bit meaning as Git100644.
  check('git_mode_'+name,(member.mode & 0o111)==(int(row['mode'],8)&0o111))
  data=t.extractfile(member).read();check('body_'+name,len(data)==member.size==row['bytes'] and sha(data)==row['sha256'] and sha((R/name).read_bytes())==row['sha256'])
check('exact_selected_regular_names',seen==set(rows));check('ancestor_dirs_only',all(any(p.startswith(d+'/') for p in seen) for d in dirs))
release=load(N/'RELEASE_REVIEW01.json','83b3ad9c265f65e59a4e852ec0470875b3081e2e0357a57686186d0ef2ffc298');gate=load(N/'gate01.json');exp=gate['experiments'][release['identity']];binding=load(N/'BINDING01.json');old=load(F/'index-capacity02-review01-2026-10-08/RELEASE_REVIEW02.json')
for name,h in exp['source_files'].items():check('source_returned_or_inherited_'+name,release['evidence'][name]==h and (rows.get(name,{}).get('sha256')==h or old['evidence'].get(name)==h))
for role,v in exp['inputs'].items():
 name=v['path'];h=v['sha256'];check('input_release_'+role,release['evidence'][name]==h)
 if role!='archive_transport':check('input_returned_or_inherited_'+role,rows.get(name,{}).get('sha256')==h or old['evidence'].get(name)==h)
check('source331_input59',len(exp['source_files'])==331 and len(exp['inputs'])==59)
for name in ('gate01.json','preflight01.py','root_io.py','BINDING01.json','RELEASE_REVIEW01.json'):check('active_entry_returned_'+name,str((N/name).relative_to(R)) in rows)
check('no_private_return',binding['transport']['path'] not in rows and not any(p.startswith('research_artifacts/real_pilot_runtime/') for p in rows))
check('prior_archive_exclusions_respected',not set(s['already_recovered_or_duplicate_archive_exclusions'])&seen)
v={'decision':'accepted','status':'EXACT_ENTRY21_PUBLIC_INCREMENT_RECOVERED','identity':release['identity'],'source':m['source'],'evidence':evidence,'checks':checks,'files':142,'regular_bytes':2388151,'returned_archive':m['returned_archive'],'source_count':331,'input_count':59,'offline_git_no_lazy_fetch':True,'qualification':'Actual fresh commit-only/direct blob receipt independently verified offline; exact142 selected public member bodies and Git executable-mode semantics returned. Source331/input59 are returned changed public bodies or unchanged prior accepted release pins; sole private dispatch excluded. Prior failed20 recovered archive reused, not duplicated. No full-tree, private/runtime/scientific-store, POSIX mode/ownership/xattr reconstruction, deletion, capacity, admission or numerical proof. No release or source suite repeated.'}
(H/'RECOVERY_REVIEW01.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted','checks':len(checks),'sha256':sha((H/'RECOVERY_REVIEW01.json').read_bytes())}))
