import atexit,datetime,gzip,hashlib,importlib.util,io,json,os,shutil,stat,subprocess,sys,tarfile,time
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];D=B/'financial-wrapper-complete100-failed-root-remote03-2026-10-04';begun=time.monotonic();checks=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def save(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
atexit.register(lambda:save('CHECK01_PROGRESS.json',checks))
def raw(p):
 p=Path(p);s=p.lstat();ck('bounded canonical file '+str(p),stat.S_ISREG(s.st_mode) and s.st_size<=4194304 and p.resolve()==p);b=p.read_bytes();ck('stable file '+str(p),p.stat().st_size==len(b)==s.st_size);return b
def js(p):return json.loads(raw(p))
remote_raw=raw(D/'REMOTE_RECOVERY01.json');ck('exact actual remote receipt',sha(remote_raw)=='33c0a82e29d16415e233d51c32196fab850fedff9239e77b7dd64088b61b3cf9');r=json.loads(remote_raw)
selection=js(D/'SELECTED_BODIES01.json');installation=js(D/'ROOT_INSTALLATION_DRAFT01.json');release=js(B/'financial-wrapper-complete100-failed-root-remote-release03-2026-10-04/MACHINE01.json')
ck('exact original remote source/release joins',r['remote_commit']==selection['remote_commit']==installation['remote_commit']=='c23c91562abe772c90f3db60e139a01750190589' and sha(raw(D/'SELECTED_BODIES01.json'))==r['selection_sha256']==release['selection_sha256'])
ck('literal legacy02 status preserved',r['status']=='fresh-actual-remote-complete100-failed-outcome02-supervised-recovered')
retained=H/'actual_metadata';retained.mkdir()
for name in ['REMOTE_RECOVERY01.json','ROOT_REMOTE03_EXIT01.json','ROOT_REMOTE03_INTENT01.json','ROOT_REMOTE03_SPAWN01.json','ROOT_INSTALLATION_DRAFT01.json','SELECTED_BODIES01.json','ROOT_REMOTE03.stdout','ROOT_REMOTE03.stderr']:(retained/name).write_bytes(raw(D/name))
sourcepins={}
for n,pin in installation['helper_pins'].items():
 b=raw(D/n);ck('actual installed helper '+n,sha(b)==pin['sha256'] and len(b)==pin['bytes'] and release['helper_pins'][n]==pin);sourcepins[n]=pin
 p=H/'installed_source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
ck('exact restore8a4',sourcepins['restore01.py']['sha256']=='8a4cb8e01a1b639430c1e2f7dd77514a0b6b85ae19616ce2d724b0b173704d86')
spec=importlib.util.spec_from_file_location('verified_flat_readonly',D/'restore01.py');flat=importlib.util.module_from_spec(spec);spec.loader.exec_module(flat)
flat.authenticate_selected(D,r) # Read-only utility; never main/entry/restore.
records=r['selected_blobs'];ck('all35 exact selection rows',[{'path':x['path'],'bytes':x['bytes'],'sha256':x['sha256']} for x in records]==selection['rows'])
ck('35bodies/29objects/109operations',len(records)==35 and len({x['git_object'] for x in records})==29 and len(r['operations'])==109 and r['selected_logical_bytes']==sum(x['bytes'] for x in records)==16481302)
# Read only the actual fetched bare repository; no fetch, mutation or experiment.
gitroot=Path(r['fresh_git_root']);env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_OPTIONAL_LOCKS='0')
def git(*args):
 p=subprocess.run(['git','--git-dir',str(gitroot),*args],capture_output=True,timeout=20,env=env);ck('offline Git exit '+args[0],p.returncode==0 and len(p.stdout)<=4*1024**2);return p.stdout
ck('actual fetched head joins fixed commit',git('rev-parse','HEAD').decode().strip()==r['remote_commit'])
listing=git('ls-tree','-z',r['remote_commit'],'--',*[x['path'] for x in records]);tree={}
for line in listing.rstrip(b'\0').split(b'\0'):
 header,path=line.split(b'\t');mode,kind,oid=header.decode().split();tree[path.decode()]={'mode':mode,'kind':kind,'oid':oid}
ck('actual full35 tree leaves',set(tree)=={x['path'] for x in records})
for x in records:
 data=raw(D/'selected'/x['path']);ck('actual selected equals original '+x['path'],data==raw(MAIN/x['path']))
 ck('actual commit mode/type/blob '+x['path'],tree[x['path']]=={'mode':x['git_mode'],'kind':'blob','oid':x['git_object']})
 ck('actual pure blobOID '+x['path'],hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==x['git_object'])
ops=r['operations'];ck('all original child exit/reaped/cleanup/4MiB actual joins',all(o['exit']==o['actual_reaped_exit']==0 and o['cleanup_failures']==[] and o['actual_child_limits']=={'pid':o['pid'],'fsize':[4194304,4194304]} for o in ops))
ck('first-final remote stdout exactjoin',ops[1]['operation']==ops[-1]['operation']=='ls-remote' and ops[1]['stdout_sha256']==ops[-1]['stdout_sha256'] and ops[1]['stdout_bytes']==ops[-1]['stdout_bytes']==98)
obs=r['whole_tree_observations'];summary={'samples':len(obs),'maximum_logical':max(x['logical_bytes'] for x in obs),'maximum_allocated':max(x['allocated_bytes'] for x in obs),'maximum_members':max(x['members'] for x in obs),'extent_changes':sum(x['regular_extent_changes'] for x in obs),'initial':obs[0]}
ck('all genuine storage observations',summary['samples']==1342 and summary['maximum_logical']==35199442 and summary['maximum_allocated']==35631104 and summary['maximum_members']==174 and summary['extent_changes']==43 and r['initial_owned_allocation']==obs[0])
rootexit=js(D/'ROOT_REMOTE03_EXIT01.json');spawn=js(D/'ROOT_REMOTE03_SPAWN01.json');intent=js(D/'ROOT_REMOTE03_INTENT01.json')
ck('actual Root exit0 rawstream hashes',rootexit['actual_root_exit']==0 and rootexit['stderr_bytes']==0 and sha(raw(D/'ROOT_REMOTE03.stderr'))==rootexit['stderr_sha256'] and len(raw(D/'ROOT_REMOTE03.stdout'))==rootexit['stdout_bytes'] and sha(raw(D/'ROOT_REMOTE03.stdout'))==rootexit['stdout_sha256'])
ck('genuine single-source intent',intent['selection_sha256']==r['selection_sha256'] and intent['claims_or_numerical_started'] is False and intent['file_limit_hard_soft']==[4194304,4194304])
# /proc absence is a current read-only census, not historical descendant completeness.
pids={x['pid'] for x in ops}|{spawn['actual_root_child_pid']};proc=spawn['procstat'];fields=proc[proc.rfind(')')+2:].split();groups={int(fields[2])}|{x['pid'] for x in ops};present=[];unreadable=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
 except (FileNotFoundError,ProcessLookupError):continue
 except PermissionError:unreadable.append(int(p.name));continue
 if int(p.name) in pids or int(f[2]) in groups:present.append({'pid':int(p.name),'group':int(f[2]),'ticks':int(f[19])})
ck('all recordedPIDs/groups currently absent',not present)
process={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root_pid':spawn['actual_root_child_pid'],'root_start_ticks':int(fields[19]),'pids':sorted(pids),'groups':sorted(groups),'matching_current':present,'unreadable_proc':unreadable,'qualification':'Current recorded-PID/group absence only; historical descendant inventory is not reconstructed.'}
bundle=D/'selected'/flat.REL;capture=js(bundle/'CAPTURE01.json');scopes=flat.load_scopes(bundle,capture);archive_rows=[]
for label,item in scopes.items():
 m=item['manifest'];compressed=raw(bundle/('complete-'+label+'01.tar.gz'));framed=list(flat.R.framed_members(compressed));ck('complete parser count '+label,len(framed)==len(m['members']))
 bodies={}
 for (name,t,body),member in zip(framed,m['members']):
  ck('canonical member '+label+'/'+name,name==member['path'] and t.mode==member['mode'] and t.uid==t.gid==t.mtime==0 and t.uname==t.gname=='' and ((member['kind']=='directory' and t.isdir() and not body) or (member['kind']=='file' and t.isfile() and len(body)==member['bytes'] and sha(body)==member['sha256'])))
  if member['kind']=='file':bodies[name]=body
 # Independent canonical rebuild from only verified opaque body bytes; no extraction.
 output=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for member in m['members']:
    t=tarfile.TarInfo(member['path']);t.mode=member['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if member['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:t.size=member['bytes'];tar.addfile(t,io.BytesIO(bodies[member['path']]))
 ck('full canonical recompression '+label,output.getvalue()==compressed)
 # Snapshot bodies/modes are original captured scope, separate from fresh flat output.
 snapshot=Path(capture['scopes'][label]['snapshot'])
 for member in m['members']:
  p=snapshot/member['path'];st=p.lstat();ck('snapshot type/mode '+label+'/'+member['path'],stat.S_IMODE(st.st_mode)==member['mode'] and (stat.S_ISDIR(st.st_mode) if member['kind']=='directory' else stat.S_ISREG(st.st_mode)))
  if member['kind']=='file':ck('snapshot whole body '+label+'/'+member['path'],raw(p)==bodies[member['path']])
 archive_rows.append({'scope':label,'archive':item['archive'],'typed_members':len(m['members']),'regular_bodies':len(bodies),'logical_bytes':sum(len(v) for v in bodies.values()),'canonical':True})
 del framed,bodies
names=[f'flat-{x}01' for x in flat.LABELS]+['FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json'];ck('exactone-use flat namespaces absent',all(not os.path.lexists(D/x) for x in names));free=shutil.disk_usage(D).free;ck('current10GiB free floor',free>=10737418240)
# Retain actual predecessor failure receipt hashes without running them.
old02=B/'financial-wrapper-complete100-failed-root-remote02-2026-10-04';predecessors={}
for n in ['ROOT_REMOTE02_EXIT01.json','SELECTED_BODIES01.json']:
 b=raw(old02/n);predecessors[str(old02/n)]={'sha256':sha(b),'bytes':len(b)}
ck('remote02 failure remains failure',js(old02/'ROOT_REMOTE02_EXIT01.json')['actual_root_exit']!=0)
readback={'status':'ALL_CHECKS_PASS_ACTUAL_REMOTE_ONLY','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':time.monotonic()-begun,'remote_receipt_sha256':sha(remote_raw),'root_exit_sha256':sha(raw(D/'ROOT_REMOTE03_EXIT01.json')),'source_pins':sourcepins,'selection':{'count':35,'bytes':16481302,'objects':29,'operations':109,'commit':r['remote_commit'],'sha256':r['selection_sha256']},'storage_samples':summary,'process':process,'archives':archive_rows,'flat_absent':names,'free_bytes_at_review':free,'permanent_predecessor_hashes':predecessors,'checks':len(checks),'actual_flat_recovery':None,'numerical_authority':False}
save('READBACK01.json',readback);print(json.dumps({'status':'PASS_ACTUAL_REMOTE_ONLY','checks':len(checks),'seconds':readback['seconds']}))
