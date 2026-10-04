from pathlib import Path
import hashlib,json,os,stat,subprocess,shutil,importlib.util,io
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';C=F/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';checks=[];calls=[];sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_bytes())
def ok(v,n):assert v,n;checks.append(n)
def git(repo,args):
 p=subprocess.run(['git','--no-replace-objects','--git-dir='+str(repo),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'});ok(p.returncode==0 and len(p.stdout)<=4*1024**2,'bounded readonly Git '+args[0]);calls.append({'args':args,'stdout_sha256':sha(p.stdout),'bytes':len(p.stdout),'exit':p.returncode});return p.stdout
r=read(T/'REMOTE_RECOVERY01.json');selection=read(T/'SELECTED_BODIES01.json');commit=r['remote_commit'];repo=Path(r['fresh_git_root']);intent=read(H/'ROOT_FINAL_SUPPLEMENT_REMOTE01_INTENT.json');terminal=read(H/'ROOT_FINAL_SUPPLEMENT_REMOTE01_EXIT.json')
ok(sha((T/'REMOTE_RECOVERY01.json').read_bytes())=='f58f20f14ea67c76f6d7571bd2f90e6c0d9374ca12d3e08f137188e8b5eae9bc','actual receipt exact')
ok(commit==selection['remote_commit']=='3a17d3630d5c06380c5d4ede5f9f72c1b9b429b2','actual immutable Main/remote commit')
ok(r['selection_sha256']==sha((T/'SELECTED_BODIES01.json').read_bytes())==intent['command'][-1]=='ef3aa53b788576c233d0bf712c04daf1ebaf4bb6cb2947352f3bea58b55f1c4d','original exact selection')
ok(sha((T/'recover01.py').read_bytes())==intent['source_helper_sha256']=='25080e2eeceb234fe63e69ab093c3d1c6af84d6584f476cc872ed43666056c1b','actual source helper unchanged')
review=F/'financial-wrapper-complete100-final-supplement-selection-review01-2026-10-04';ok(sha((review/'MANIFEST01.json').read_bytes())==intent['selection_review_manifest']=='9c946399d79f0e33aa85e50f263252748688a9635015c0c019adbc72c157bf11','genuine selection release')
for row in read(review/'MANIFEST01.json')['members']:
 if row['kind']=='file':ok(sha((review/row['path']).read_bytes())==row['sha256'],'selection review body '+row['path'])
for stream in ('stdout','stderr'):
 b=(H/('ROOT_FINAL_SUPPLEMENT_REMOTE01.'+stream)).read_bytes();ok(sha(b)==terminal[stream+'_sha256'],'actual Root '+stream)
ok(terminal['actual_root_observed_helper_exit']==0 and (H/'ROOT_FINAL_SUPPLEMENT_REMOTE01.stderr').read_bytes()==b'','separate actual Root0/empty stderr')
ok(sha((T/'restore02.py').read_bytes())=='dcbf5ec290b1f34cb3a238be76976a0ad8ebf07003e8d5f43cfcbaacc1d8d5a0','exact scoped restore02')
spec=importlib.util.spec_from_file_location('review_scoped_flat',T/'restore02.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);R=m.R;m.pins_ready();rows=m.authenticate_selected(T,r);required=m.REQUIRED
ok(len(rows)==r['selected_count']==7 and r['selected_logical_bytes']==1063336,'actual7 exactscope')
entries={}
for record in git(repo,['ls-tree','-r','-z',commit,'--',*sorted(required)]).split(b'\0'):
 if record:
  a,n=record.split(b'\t');mode,kind,oid=a.decode().split();entries[n.decode()]=(mode,kind,oid)
ok(git(repo,['cat-file','-t',commit])==b'commit\n','actual commit distinct final FETCH_HEAD')
for name,row in rows.items():
 b=(T/'selected'/name).read_bytes();ok(entries[name]==(row['git_mode'],'blob',row['git_object']),'actual fetched tree '+name);ok(git(repo,['cat-file','blob',row['git_object']])==b==(ROOT/name).read_bytes(),'original current fetched saved byte identity '+name)
 ok(sha(b)==row['sha256']and len(b)==row['bytes']and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_object'],'actual whole body/OID '+name)
ok({str(p.relative_to(T/'selected'))for p in (T/'selected').rglob('*')if p.is_file()}==set(required),'saved namespace exact7')
ops=r['operations'];ok(len(ops)==25 and all(o['exit']==0 and o['cleanup_failures']==[]for o in ops),'all25 original operations0/cleanupempty')
for o in ops:
 pid=o['pid'];ok(type(pid)is int and not Path('/proc',str(pid)).exists(),'original Git PID currently absent '+str(pid))
 try:os.killpg(pid,0)
 except ProcessLookupError:checks.append('original Git group currently absent '+str(pid))
 else:raise AssertionError('group alive')
rev=next(o for o in ops if o['operation']=='rev-parse');ok(rev['stdout_bytes']==41 and rev['stdout_sha256']==sha((commit+'\n').encode()),'firstfetch actualcommit readback')
for o in [o for o in ops if o['operation']=='ls-remote']:ok(o['stdout_sha256']==sha((commit+'\t'+r['branch']+'\n').encode()),'actual initial/final remote HEAD readback')
fh=(repo/'FETCH_HEAD').read_text().splitlines();ok(len(fh)==7 and {v.split('\t')[0]for v in fh}=={v['git_object']for v in rows.values()},'final FETCH_HEAD7blobs not commit')
bundle=T/'selected'/m.REL;cap=read(bundle/'CAPTURE01.json');scopes=m.load_scopes(bundle,cap)
for label,x in scopes.items():
 raw=(bundle/('complete-'+label+'01.tar.gz')).read_bytes();frames=list(R.framed_members(raw));ok(len(frames)==len(x['manifest']['members']),'complete fetched frames '+label)
 for (name,t,b),row in zip(frames,x['manifest']['members']):
  ok(name==row['path']and t.mode==row['mode'],'actual fetched path+mode '+name);ok(row['kind']=='directory'and t.isdir()and not b or row['kind']=='file'and t.isfile()and len(b)==row['bytes']and sha(b)==row['sha256'],'actual fetched typed body '+name)
 snapshot=Path(cap['scopes'][label]['snapshot']);ok(R.scan(snapshot)==x['manifest'],'unchanged snapshot '+label);sink=io.BytesIO();R.tar_stream(snapshot,x['manifest'],sink);ok(sink.getvalue()==raw,'full fetched canonical recompression '+label)
absent=['flat-contract01','flat-support01','FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json']
for n in absent:ok(not os.path.lexists(T/n),'fresh restore name '+n)
active=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:argv=(p/'cmdline').read_bytes().split(b'\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if str(T/'restore02.py').encode()in argv or str(T/'recover01.py').encode()in argv:active.append(p.name)
ok(not active,'no current matching helper argv');ok(shutil.disk_usage(T).free>=10*1024**3,'observed10GiB floor')
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'readonly_Git_calls':calls,'receipt_sha256':sha((T/'REMOTE_RECOVERY01.json').read_bytes()),'original_Root_PID_history':None,'original_Git_current_absence':True,'fresh_names':absent,'actual_restore':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks)}))
