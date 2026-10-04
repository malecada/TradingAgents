"""Read-only exact actual baseline recovery checker. No helper entry or network.
Needs genuine Root actual receipt refs supplied after the operations; absence
refuses before any verdict. Outputs only in this new review directory.
"""
from pathlib import Path
import argparse,hashlib,json,os,stat,time,io,gzip,tarfile,sys,subprocess
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B.parents[2];D=B/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05';CAP=ROOT.parent/'onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source';PARENT=CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01'
MAIN='d15e720ff6143350052b90c563ead1f950dd8be3';SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41';FILE=4194304;START=time.monotonic();cache={};pins={};treepins={};count=0;total=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,msg):
 global count
 if not v:raise ValueError(msg)
 count+=1
sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p,pin=None):
 global total
 p=Path(p);s=p.lstat();ok(time.monotonic()-START<180 and p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE,'bounded stable regular')
 if p not in cache:
  with p.open('rb') as f:b=f.read(FILE+1)
  ok(len(b)==s.st_size and sig(s)==sig(p.lstat()),'physical read stable');cache[p]=b;pins[p]=sig(s);total+=len(b);ok(total<=64*1024**2,'64MiB total audit bytes')
 else:ok(pins[p]==sig(s),'retained exact signature');b=cache[p]
 ok(pin is None or sha(b)==pin,'exact real body hash');return b
def j(p,pin=None):return json.loads(read(p,pin))
def ref(v):
 ok(type(v)is dict and set(v)=={'path','sha256'},'literal actual evidence ref');return read(Path(v['path']),v['sha256'])
def census(root,exclude=()):
 out={};todo=[root]
 while todo:
  p=todo.pop()
  with os.scandir(p) as it:
   for e in it:
    if p==root and e.name in exclude:continue
    s=e.stat(follow_symlinks=False);ok(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode),'whole ordinary population');n=str(Path(e.path).relative_to(root));out[n]=sig(s)
    if stat.S_ISDIR(s.st_mode):todo.append(Path(e.path))
 ok(len(out)<32768,'finite population');prior=treepins.get(root);ok(prior is None or prior==(tuple(exclude),out),'unchanged whole namespace');treepins[root]=(tuple(exclude),out);return out

CALLER='13548eb3206febfb13e1dff0d5f63159176fb8ba1dae819f8de89b9a499cb8b7'
remote=j(D/'REMOTE_RECOVERY01.json','304745e0fb0774935e154377b05c97dcc263b6ab52e689652995b93c272f233b');tool=j(D/'ROOT_TOOL_EXIT_REMOTE01.json','0e76c23ebf964e2d7e02a9bc66e0a0ca1e594f542e7b7194c255ecd2eecb5d1f');profile=j(D/'SELECTED_MODE_PROFILE01.json','edd63f3ef43ba205eab3141e2947a2b82e46edcee1038d2138b706e7c5d7cc3d');q=j(D/'ROOT_REQUEST_FLAT_DRAFT01.json','46722ede3d775754553a2c17a85d267111e31562e1ec516c82a39e8a85f5f3b4')
freeze=j(D/'ROOT_BINDING_FREEZE01.json');selection=j(D/'SELECTED_BODIES01.json',freeze['selection_sha256']);base=j(D/'ROOT_REQUEST_BASELINE01.json',freeze['request_sha256']);accepted=j(B/'financial-wrapper-compatibility-final-bundle-transport-source-review04-2026-10-05/MACHINE01.json','2b4b5c04102d81644ed24786aa712f92124f5030410baba489cd1032785563fe')
for n,h in freeze['helper_pins'].items():read(D/n,h)
read(D/'caller02.py',CALLER);read(D/'recover01.py',freeze['generated_source_sha256']);ok(accepted['caller_sha256']==CALLER and accepted['baseline_restore_sha256']==freeze['helper_pins']['restore_bundle01.py'],'unchanged peer accepted caller/source04')
sys.path.insert(0,str(D/'utilities'));sys.path.insert(0,str(D));import receipt01 as V;import recovery_pax01 as R;import binding01 as BINDER;import watch01 as W
expected={x['path']:{'bytes':x['bytes'],'sha256':x['sha256']} for x in selection['rows']};V.validate_remote(remote,selection,freeze['selection_sha256'],expected)
ok(remote['remote_commit']==MAIN and remote['selected_count']==44 and remote['selected_logical_bytes']==6089473 and remote['expected_operations']==132 and remote['unique_selected_objects']==34,'fixed actual complete remote denominators')
ok(remote['operations'][1]['stdout_sha256']==remote['operations'][-1]['stdout_sha256']==sha((MAIN+'\t'+V.BRANCH+'\n').encode()) and remote['operations'][7]['stdout_sha256']==sha((MAIN+'\n').encode()),'actual first/final remote and fetched commit output hashes')
selected=D/'selected';ok(R.scan(selected)==profile['full_manifest'] and profile['actual_selected_root']==str(selected),'complete genuine selected mode profile');census(selected)
for row in remote['selected_blobs']:
 data=read(selected/row['path'],row['sha256']);ok(len(data)==row['bytes'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_object'],'every actual selected Git blob');ok(read(ROOT/row['path'],row['sha256'])==data,'current exact committed source origin')
exitrow=j(D/'ROOT_BASELINE_REMOTE01_EXIT.json');intent=j(D/'ROOT_BASELINE_REMOTE01_INTENT.json');spawn=j(D/'ROOT_BASELINE_REMOTE01_SPAWN.json');release=j(D/'REMOTE_ENTRY_RELEASE01.json','f438191c7734415551e95fd127559cfcff1fcb2a086591466257f11a311b3e94');contract=j(D/'REMOTE_CONTRACT01.json','ffe5b475e31ad63d04ef6416b462eac093fe9db4315e83c743a8324d723db224')
ok(tool['actual_exit']==0 and tool['session_id']==61499 and tool['completion_chunk']=='6beeb0' and exitrow['child_exit']==0 and exitrow['parent_failure_type'] is None and exitrow['cleanup_failures']==[] and exitrow['actual_parent_exit'] is None and tool['original_parent_exit_field'] is None and exitrow['parent_fsize_readback']==[FILE,FILE],'actual originalNULL separate Root0 and clean child0')
ok(intent['contract_sha256']==release['contract_sha256']==sha(read(D/'REMOTE_CONTRACT01.json')) and intent['entry_release_sha256']==sha(read(D/'REMOTE_ENTRY_RELEASE01.json')) and release['caller_sha256']==CALLER and intent['argv']==spawn['argv'],'exact genuine entry context')
ok(read(D/'ROOT_BASELINE_REMOTE01.stderr')==b'','empty original stderr');out=j(D/'ROOT_BASELINE_REMOTE01.stdout');ok(all(out[k]==remote[k] for k in out),'actual stdout summary joins receipt')
for sample in exitrow['observations']:ok(0<=sample['logical_bytes']<=64*1024**2 and 0<=sample['allocated_bytes']<=96*1024**2 and sample['seconds']<5,'actual whole Root bounded observation')
pids=sorted({x['pid'] for x in remote['operations']}|{intent['parent_pid'],spawn['pid']});ok(pids==tool['recorded_original_pids_absent'],'all134 actual recorded PIDs')
for pid in pids:
 ok(not Path('/proc',str(pid)).exists(),'recorded PID currently absent')
 try:os.killpg(pid,0)
 except ProcessLookupError:pass
 else:raise ValueError('recorded process group exists')
allowed={'actual_remote_receipt','actual_selected_mode_profile','actual_restore_release'};ok({k:v for k,v in q.items() if k not in allowed}=={k:v for k,v in base.items() if k not in allowed} and q['actual_restore_release'] is None,'only actual refs populated, inner release remains null')
for field,name in [('actual_remote_receipt','REMOTE_RECOVERY01.json'),('actual_selected_mode_profile','SELECTED_MODE_PROFILE01.json')]:row=q[field];ok(ROOT/row['path']==D/name and row['sha256']==sha(read(D/name)) and row['bytes']==len(read(D/name)),'genuine actual flat request binding')
ok(BINDER.validate(q)==expected,'genuine binder accepts unchanged full declared archive/evidence scope')
for bundle in q['bundles']:
 manifest=j(selected/bundle['manifest']['path'],bundle['manifest']['sha256']);archive=read(selected/bundle['archive']['path'],bundle['archive']['sha256']);R.validate(manifest);raw=gzip.decompress(archive);ok(len(raw)<=64*1024**2,'finite whole archive stream');buf=io.BytesIO()
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar,tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as out:
  members=tar.getmembers();ok(len(members)==len(manifest['members']),'full canonical member denominator')
  for actual,row in zip(members,manifest['members']):
   ok(actual.name.rstrip('/')==row['path'] and actual.mode==row['mode'] and actual.uid==actual.gid==actual.mtime==0 and actual.uname==actual.gname=='','canonical path/header/modes');info=tarfile.TarInfo(row['path']+('/' if row['kind']=='directory' else ''));info.mode=row['mode'];info.uid=info.gid=info.mtime=0;info.uname=info.gname=''
   if row['kind']=='directory':ok(actual.isdir(),'directory type');info.type=tarfile.DIRTYPE;out.addfile(info)
   else:ok(actual.isfile() and actual.size==row['bytes']<=FILE,'regular bounded type');body=tar.extractfile(actual).read(FILE+1);ok(len(body)==row['bytes'] and sha(body)==row['sha256'],'all archived bytes');info.size=len(body);out.addfile(info,io.BytesIO(body))
 ok(gzip.compress(buf.getvalue(),mtime=0)==archive,'full original archive/footer/recompression')
fresh=['BUNDLE_FLAT_INTENT01.json','BUNDLE_FLAT_RECOVERY01.json','BUNDLE_FLAT_FAILED01.json']+['flat-'+b['name'] for b in q['bundles']]+['ROOT_BASELINE_FLAT01'+s for s in ('_INTENT.json','_SPAWN.json','.stdout','.stderr','_EXIT.json')]
ok(all(not os.path.lexists(D/n) for n in fresh) and not os.path.lexists(D/'FAILED01.json'),'one fresh flat scope and no remote failure')
now=W.census(D);vfs=os.statvfs(D);current_free=vfs.f_bavail*vfs.f_frsize;ok(current_free>=10*1024**3,'actual current disk floor')
for root,(exclude,_) in list(treepins.items()):census(root,exclude)
for p,s in pins.items():ok(sig(p.lstat())==s,'final current input signatures')
release={'schema_version':1,'decision':'ACCEPTED_EXACT_BASELINE_BUNDLE_FLAT','contract_sha256':R.digest(R.encode({k:v for k,v in q.items() if k!='actual_restore_release'})),'remote_sha256':sha(read(D/'REMOTE_RECOVERY01.json')),'source_sha256':sha(read(D/'restore_bundle01.py'))}
result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_BASELINE_REMOTE_AND_EXACT_INNER_FLAT_BINDING','reviewer':'combined_worker_review','actual_remote_sha256':release['remote_sha256'],'actual_root_tool_exit_sha256':sha(read(D/'ROOT_TOOL_EXIT_REMOTE01.json')),'original_root_exit_sha256':sha(read(D/'ROOT_BASELINE_REMOTE01_EXIT.json')),'caller_sha256':CALLER,'request_draft_sha256':sha(read(D/'ROOT_REQUEST_FLAT_DRAFT01.json')),'profile_sha256':sha(read(D/'SELECTED_MODE_PROFILE01.json')),'inner_release_sha256':sha(R.encode(release)),'checks':count,'files_read':len(cache),'bytes_read':total,'actual_operations':132,'actual_selected_files':44,'actual_selected_bytes':6089473,'recorded_pids_currently_absent':pids,'current_storage_observation':now,'current_free_bytes':current_free,'sample_floor_readbacks':'not serialized; original pinned watcher enforces floor at both sample boundaries','actual_flat_recovery':None,'numerical_authority':False}
for name,obj in [('REMOTE_READBACK01.json',result),('INNER_FLAT_RELEASE01.json',release)]:
 with (H/name).open('xb') as f:f.write(R.encode(obj))
print(json.dumps({k:v for k,v in result.items() if k not in ('recorded_pids_currently_absent','current_storage_observation')}))
