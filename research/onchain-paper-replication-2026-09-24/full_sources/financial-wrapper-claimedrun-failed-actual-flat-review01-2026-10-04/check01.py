import gzip,hashlib,io,json,os,stat,subprocess,sys,tarfile
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';C=F/'financial-wrapper-claimedrun-failed-capture01-2026-10-04';V=F/'financial-wrapper-claimedrun-failed-actual-remote-review01-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';P=F/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P));import recovery04 as R
checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
flatraw=(T/'FLAT_RECOVERY01.json').read_bytes();flat=json.loads(flatraw);remote_raw=(T/'REMOTE_RECOVERY01.json').read_bytes();remote=json.loads(remote_raw);capraw=(C/'CAPTURE01.json').read_bytes();cap=json.loads(capraw)
ok(sha(flatraw)=='e53f91d9161d4903a3762ef69b65a0d6addb9bdf9909a5c1b6a071e0cb5f527e','actual flat receipt');ok(sha(remote_raw)==flat['remote_receipt_sha256']=='8f294d8140030deb66b0db32481247019a0b86d279b54b965ee3d19bff87d268','actual accepted remote chain');ok(sha(capraw)==flat['capture_sha256']=='08f69b601770c81572e5223f1f5cdec21e2c48072ba86394255b0c5bcddc9ae1','actual capture pin')
# Preserve full actual remote review, including its initial FETCH_HEAD harness error.
vraw=(V/'MANIFEST01.json').read_bytes();ok(sha(vraw)=='59c2c092b5f087efac91d7d2800763efc1823043016f685c5d11abf065ef20c1','remote review seal');vm=json.loads(vraw)
for row in vm['members']:
 p=V if row['path']=='.'else V/row['path'];s=p.lstat();mode=int(row['mode'],8)if isinstance(row['mode'],str)else row['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'remote review mode '+row['path'])
 if row['kind']=='file':ok(sha(p.read_bytes())==row['sha256']and s.st_size==row['bytes'],'remote review body '+row['path'])
ok({p.relative_to(V).as_posix()for p in V.rglob('*')if p.name!='MANIFEST01.json'}=={r['path']for r in vm['members']if r['path']!='.'},'complete preserved remote review')
env=dict(os.environ);env['GIT_NO_REPLACE_OBJECTS']='1';calls=[]
def git(repo,args):
 p=subprocess.run(['git','--no-replace-objects','-C',str(repo),*args],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=10)
 ok(p.returncode==0 and not p.stderr and len(p.stdout)<=4*1024**2,'bounded local Git '+args[0]);calls.append({'args':args,'repo':str(repo),'exit':p.returncode,'stdout_sha256':sha(p.stdout),'bytes':len(p.stdout)});return p.stdout
repo=Path(remote['fresh_git_root']);commit=remote['remote_commit'];rows=remote['selected_blobs'];ok(len(rows)==8 and len({r['path']for r in rows})==8,'actual selected8 exact unique')
tree=git(repo,['ls-tree','-r','-z',commit,'--',*[r['path']for r in rows]]);objects={}
for item in tree.rstrip(b'\0').split(b'\0'):
 a,b=item.split(b'\t');objects[b.decode()]=tuple(a.decode().split())
for row in rows:
 mode,kind,oid=objects[row['path']];body=git(repo,['cat-file','blob',oid]);saved=R.read(T/'selected',row['path']);original=(ROOT/row['path']).read_bytes();ok(mode==row['git_mode']and kind=='blob'and oid==row['git_object']and body==saved==original and len(body)==row['bytes']and sha(body)==row['sha256'],'actual external Git saved original body '+row['path']);ok(hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'actual blob OID '+row['path'])
roles=[];flatfiles={};fingerprints={}
for role,scope in cap['scopes'].items():
 dest=T/('flat-'+role+'01');summary=flat['actual'][role];meta_raw=R.read(dest,summary['metadata_file']);meta=json.loads(meta_raw);manifest=json.loads((C/(role.upper()+'_MANIFEST01.json')).read_bytes());mapping=meta['flat_members'];archive=(C/('complete-'+role+'01.tar.gz')).read_bytes()
 ok(dest.resolve()==dest and stat.S_IMODE(dest.lstat().st_mode)==0o700,'private actual flat root '+role)
 ok(sha(meta_raw)==summary['metadata_sha256']and R.encode(meta)==meta_raw and meta=={'schema_version':1,'manifest':manifest,'archive':scope['archive'],'flat_members':mapping},'full canonical flat metadata '+role)
 R.validate(manifest);files=[r for r in manifest['members']if r['kind']=='file'];ok(mapping=={r['path']:'body-'+str(i).zfill(5)+'.body'for i,r in enumerate(files)},'complete ordered one-to-one mapping '+role)
 ok(set(p.name for p in dest.iterdir())==set(mapping.values())|{summary['metadata_file']},'noextra no missing private files '+role)
 for p in dest.iterdir():
  s=p.lstat();ok(stat.S_ISREG(s.st_mode)and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size<=R.FILE,'actual flat0600 singleton '+role+'/'+p.name);fingerprints[str(p)]=R.sig(s)
 origin=Path(scope['origin']);snapshot=Path(scope['snapshot']);ok(R.scan(snapshot)==manifest,'whole saved snapshot unchanged '+role)
 if role!='root':
  actual=[]
  for p in origin.rglob('*'):
   rel=p.relative_to(origin).as_posix()
   if role=='capsule'and rel.split('/')[0]=='.git':continue
   actual.append(rel)
  ok(sorted(actual)==[r['path']for r in manifest['members']],'whole actual original membership '+role)
 for r in manifest['members']:
  p=origin/r['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==r['mode'],'original literal mode '+role+'/'+r['path'])
  if r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'original directory '+role+'/'+r['path']);continue
  body=R.read(dest,mapping[r['path']]);ok(len(body)==r['bytes']and sha(body)==r['sha256']and body==R.read(snapshot,r['path'])==R.read(origin,r['path']),'every opaque flat-original-snapshot byte '+role+'/'+r['path']);flatfiles[(role,r['path'])]=body
 sink=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0)as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT)as tar:
   for r in manifest['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;tar.addfile(t)
    else:body=flatfiles[(role,r['path'])];t.size=len(body);tar.addfile(t,io.BytesIO(body))
 ok(sink.getvalue()==archive and sha(archive)==summary['archive_sha256']==scope['archive']['sha256'],'complete flat-derived canonical compressed archive '+role)
 for (name,t,body),r in zip(R.framed_members(archive),manifest['members']):ok(name==r['path']and t.mode==r['mode']and (r['kind']=='directory'and t.isdir()or r['kind']=='file'and body==flatfiles[(role,name)]),'all bounded raw framing '+role+'/'+name)
 roles.append({'role':role,'members':len(manifest['members']),'bodies':len(files),'body_bytes':sum(r['bytes']for r in files),'metadata_sha256':sha(meta_raw),'archive_sha256':sha(archive),'physical_files':len(files)+1})
# Actual Source339 commit graph remains outside this new non-Git flat scope.
S=Path(cap['scopes']['capsule']['origin']);ok(git(S,['rev-parse','HEAD']).decode().strip()==cap['source'],'current Source339 HEAD unchanged');tree=git(S,['ls-tree','-r','-z',cap['source']]);count=0
for item in tree.rstrip(b'\0').split(b'\0'):
 a,b=item.split(b'\t');mode,kind,oid=a.decode().split();body=flatfiles[('capsule',b.decode())];ok(kind=='blob'and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'all recovered currentSource Git blobs '+b.decode());count+=1
ok(count==339,'source339 complete immutable body set')
id=flat['identity'];claimpath='research_runs/'+id+'/claim.json';failpath='research_runs/'+id+'/failed.json';claim=json.loads(flatfiles[('capsule',claimpath)]);failed=json.loads(flatfiles[('capsule',failpath)])
ok(sha(flatfiles[('capsule',claimpath)])=='d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b'and sha(flatfiles[('capsule',failpath)])=='4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558','genuine original failed and claim pins')
ok(claim['design_source']==cap['source']and claim['effective_attempt_budget']==19 and failed['claim_sha256']==sha(flatfiles[('capsule',claimpath)])and failed['status']=='failed'and failed['reason'].startswith('PlannedInterruption:')and failed['output_sha256']=={},'failed permanent spent planned interruption distinction')
for role,row in claim['experiment']['inputs'].items():ok(sha(flatfiles[('capsule',row['path'])])==row['sha256'],'recovered genuine input role '+role)
outcome=json.loads((F/'financial-wrapper-claimedrun-native-outcome-review01-2026-10-04/MACHINE01.json').read_bytes());checkpoints=[(n,b)for (r,n),b in flatfiles.items()if r=='capsule'and sha(b)==outcome['checkpoint_state_sha256']];ok(len(checkpoints)==1 and len(checkpoints[0][1])==493424,'opaque checkpoint exact extent/hash only')
parentterm=json.loads(flatfiles[('parent','attempt/parent-terminal.json')]);rootexit=json.loads(flatfiles[('root','ROOT_NATIVE_LAUNCH01_EXIT.json')]);ok(parentterm['actual_parent_exit']is None and rootexit['actual_outer_process_exit_code']==1 and rootexit['original_parent_terminal_sha256']==sha(flatfiles[('parent','attempt/parent-terminal.json')]),'original Parent null distinct Root1')
exitp=H/'ROOT_FAILED_FLAT01_EXIT.json';exitraw=exitp.read_bytes();ex=json.loads(exitraw);ok(sha(exitraw)=='b3ea38b97a5ff47fecc591c4e0f50c0fde5996ed864b35f7582746acbdd903a4'and ex['actual_exec_return_exit_code']==0 and ex['launch_tool']=='737925'and ex['actual_flat_receipt_sha256']==sha(flatraw),'actual original flat tool exit0')
for k,n in [('root_intent_sha256','ROOT_FAILED_FLAT01_INTENT.json'),('root_stdout_sha256','ROOT_FAILED_FLAT01.stdout'),('root_stderr_sha256','ROOT_FAILED_FLAT01.stderr')]:ok(sha((H/n).read_bytes())==ex[k],'actual flat stream/intent '+n)
ok(all(x['free_bytes']>=R.FLOOR and x['seconds']<120 for x in flat['floor_observations'])and len(flat['floor_observations'])==7,'all seven actual floors within sampleddeadline')
for call in remote['operations']:ok(call['exit']==0 and not call['cleanup_failures']and not Path('/proc',str(call['pid'])).exists(),'original remote operation absent '+str(call['pid']))
for p,signature in fingerprints.items():ok(R.sig(Path(p).lstat())==signature,'flat final current inode unchanged '+p)
ok(not any(n in sys.modules for n in ('numpy','torch','scipy')),'no numerical imports');ok(sum(r['bodies']for r in roles)==402 and sum(r['physical_files']for r in roles)==405,'full402 plus3 metadata')
(D/'READBACK01.json').write_bytes(R.encode({'checks':len(checks),'checks_detail':checks,'roles':roles,'local_git_calls':calls,'capture_sha256':sha(capraw),'remote_sha256':sha(remote_raw),'flat_sha256':sha(flatraw),'root_actual_exit_sha256':sha(exitraw),'source':cap['source'],'checkpoint_sha256':sha(checkpoints[0][1]),'checkpoint_bytes':len(checkpoints[0][1]),'checkpoint_decoded':False,'all_actual_original_flat_inodes_stable':True,'flat_original_OS_PID_history_recorded':False,'remote_review_manifest_sha256':sha(vraw)}));print(json.dumps({'checks':len(checks),'roles':roles,'actual_flat_files':405}))
