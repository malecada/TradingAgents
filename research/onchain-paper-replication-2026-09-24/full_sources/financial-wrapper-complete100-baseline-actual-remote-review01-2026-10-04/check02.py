from pathlib import Path
import hashlib,json,os,stat,subprocess,shutil,sys
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-complete100-baseline-remote01-2026-10-04';C=F/'financial-wrapper-complete100-baseline-capture01-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';checks=[];calls=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
def read(p):return json.loads(p.read_bytes())
def git(repo,args):
 p=subprocess.run(['git','--no-replace-objects','--git-dir='+str(repo),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'});ok(p.returncode==0,'local Git exit '+args[0]);ok(len(p.stdout)<=8*1024**2,'bounded local Git output');calls.append({'args':args,'stdout_sha256':sha(p.stdout),'bytes':len(p.stdout),'exit':p.returncode});return p.stdout
r=read(T/'REMOTE_RECOVERY01.json');selection=read(T/'SELECTED_BODIES01.json');commit=r['remote_commit'];repo=Path(r['fresh_git_root']);intent=read(H/'ROOT_BASELINE_REMOTE01_INTENT.json');terminal=read(H/'ROOT_BASELINE_REMOTE01_EXIT.json');required=read(C/'REQUIRED_BODIES02.json')
ok(sha((T/'REMOTE_RECOVERY01.json').read_bytes())=='36cc03869ce63c103e2631bc3b602f3ea9e478c5a50ba6f015f55359bff9816b','exact actual receipt')
ok(commit==selection['remote_commit']==intent['actual_remote_commit']=='189855726b372bf4bbfdf63eab0687add74886eb','actual immutable commit')
ok(r['selection_sha256']==sha((T/'SELECTED_BODIES01.json').read_bytes())==intent['exact_selection_sha256'],'actual selection binding')
release=F/'financial-wrapper-complete100-baseline-selection-release-review01-2026-10-04';ok(sha((release/'MANIFEST01.json').read_bytes())==intent['exact_selection_release_manifest_sha256']=='1053ad04354ffb0a87e65607f8e828f247ffd47d87d85c95f91534e5fc7ed881','genuine exact selection release')
for row in read(release/'MANIFEST01.json')['members']:
 p=release/row['path']
 if row['kind']=='file':ok(sha(p.read_bytes())==row['sha256']and p.stat().st_size==row['bytes'],'release member '+row['path'])
for stream in ('stdout','stderr'):
 b=(H/('ROOT_BASELINE_REMOTE01.'+stream)).read_bytes();ok(sha(b)==terminal[stream+'_sha256']and len(b)==terminal[stream+'_bytes'],'actual Root '+stream)
ok(terminal['actual_outer_exit']==0 and terminal['native_or_claim_started']is False,'actual Root ordinary exit')
ok(r['selected_count']==len(r['selected_blobs'])==len(required)==17 and r['selected_logical_bytes']==5320678,'exact17 extent')
rows=r['selected_blobs'];ok([x['path']for x in rows]==sorted(required)and len(set(x['path']for x in rows))==17,'sorted unique complete required rows')
tree=git(repo,['ls-tree','-r','-z',commit,'--',*sorted(required)]);entries={}
for record in tree.split(b'\0'):
 if record:
  a,n=record.split(b'\t');mode,kind,oid=a.decode().split();entries[n.decode()]=(mode,kind,oid)
ok(git(repo,['cat-file','-t',commit])==b'commit\n','actual fetched commit object separately from FETCH_HEAD')
for row,sel in zip(rows,selection['rows']):
 name=row['path'];b=(T/'selected'/name).read_bytes();ok(sel=={'path':name,'bytes':row['bytes'],'sha256':row['sha256']},'original selected row '+name);ok(required[name]=={'bytes':row['bytes'],'sha256':row['sha256']},'required exact row '+name)
 ok(entries[name]==(row['git_mode'],'blob',row['git_object']),'actual fetched tree mode/OID '+name)
 ok(git(repo,['cat-file','blob',row['git_object']])==b==(ROOT/name).read_bytes(),'freshGit saved current bytes '+name)
 ok(sha(b)==row['sha256']and len(b)==row['bytes']and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_object'],'full opaque body extents/hashes/OID '+name)
 ok(stat.S_ISREG((T/'selected'/name).lstat().st_mode),'saved regular '+name)
actualfiles={str(p.relative_to(T/'selected'))for p in (T/'selected').rglob('*')if p.is_file()};ok(actualfiles==set(required),'saved no extra or missing bodies')
ops=r['operations'];ok(len(ops)==45 and all(o['exit']==0 and o['cleanup_failures']==[]for o in ops),'all45 recorded exits/cleanup')
for op in ops:
 pid=op['pid'];ok(type(pid)is int and not Path('/proc',str(pid)).exists(),'current original PID absent '+str(pid))
 try:os.killpg(pid,0)
 except ProcessLookupError:checks.append('current original group absent '+str(pid))
 else:raise AssertionError('group still present '+str(pid))
rev=next(o for o in ops if o['operation']=='rev-parse');ok(rev['stdout_sha256']==sha((commit+'\n').encode())and rev['stdout_bytes']==41,'first fetch actual commit readback stdout hash')
fetches=[o for o in ops if o['operation']=='fetch'];ok(len(fetches)==2 and all(o['stdout_bytes']==0 and o['stdout_sha256']==sha(b'')for o in fetches),'two original fetch stdout records')
fh=(repo/'FETCH_HEAD').read_text().splitlines();ok(len(fh)==17 and {s.split('\t')[0]for s in fh}=={x['git_object']for x in rows},'final FETCH_HEAD is17 blob list not first commit')
flat=T/'restore02.py';ok(sha(flat.read_bytes())=='8b010b28e37978c6ea24eb0e4aaad68d715f4031a102d7396f4627fd501d06e1','exact accepted restore02')
absent=['flat-'+v+'01'for v in ('capsule','parent','support','git1','git2','git3')]+['fresh-original-source339-01.git','FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json']
for n in absent:ok(not os.path.lexists(T/n),'fresh namespace '+n)
active=[]
for proc in Path('/proc').iterdir():
 if proc.name.isdigit():
  try:argv=(proc/'cmdline').read_bytes().split(b'\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if any(v==str(flat).encode()or v==str(T/'recover01.py').encode()for v in argv):active.append(proc.name)
ok(not active,'no current matching helper argv');ok(shutil.disk_usage(T).free>=10*1024**3,'current10GiB floor')
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'local_Git_calls':calls,'remote_receipt_sha256':sha((T/'REMOTE_RECOVERY01.json').read_bytes()),'original_Root_PID_history':None,'original_Git_PID_current_absence':True,'prospective_absent_names':absent,'helper_sha256':sha(flat.read_bytes()),'actual_flat_run':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks)}))
