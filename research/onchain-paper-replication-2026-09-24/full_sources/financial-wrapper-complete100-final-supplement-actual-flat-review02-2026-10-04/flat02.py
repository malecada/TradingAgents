from pathlib import Path
import ast,gzip,hashlib,io,json,os,stat,subprocess,sys,tarfile,importlib.metadata,shutil
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';B=F/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';V=F/'financial-wrapper-complete100-final-supplement-actual-remote-review01-2026-10-04';checks=[];calls=[];pins={};sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,h=None):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2,'bounded regular evidence');b=p.read_bytes();pins[str(p)]=sha(b)
 if h:ok(sha(b)==h,'exact evidence hash')
 return b
remote=json.loads(read(T/'REMOTE_RECOVERY01.json','f58f20f14ea67c76f6d7571bd2f90e6c0d9374ca12d3e08f137188e8b5eae9bc'));flat=json.loads(read(T/'FLAT_RECOVERY01.json','7f1d96645c7f3017bb9ae78ae32d58cf345b21c290ab01ed34bf8c14dfe6295c'));cap=json.loads(read(B/'CAPTURE01.json','86b787a7a01f15a596f356c16b1c1b55060549159fb7a301cc173c814cfcb67e'));release=json.loads(read(V/'FLAT_RELEASE01.json','1f8a44635e7638f25f4094ea003c98cecb40b3c7f494a9f94895cffb396704f0'));review=json.loads(read(V/'MACHINE01.json'));ok(review['decision']=='accepted-actual-seven-body-final-supplement-remote' and review['remote_receipt_sha256']==sha((T/'REMOTE_RECOVERY01.json').read_bytes()),'genuine prior external acceptance')
vmraw=read(V/'MANIFEST01.json');ok(sha(vmraw).startswith('c6a091ad'),'actual remote review seal');vm=json.loads(vmraw);ok({p.relative_to(V).as_posix() for p in V.rglob('*') if p!=V/'MANIFEST01.json'}=={r['path'] for r in vm['members']}-{'.'},'full actualremote review membership')
for r in vm['members']:
 p=V/r['path'];s=p.lstat();mode=int(r['mode'],8) if isinstance(r['mode'],str) else r['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'review mode')
 if r['kind']=='file':ok(s.st_size==r['bytes'] and sha(read(p))==r['sha256'],'review member bytes')
 elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'review directory')
 else:ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'review literal link')
read(T/'restore02.py',release['helper_sha256']);read(T/'utilities/recovery04.py',release['explicit_PAX_dependency_sha256'])
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_NO_REPLACE_OBJECTS='1');bare=Path(remote['fresh_git_root'])
def git(root,args):
 p=subprocess.run(['git','--no-replace-objects','-C',str(root),*args],env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=10);ok(p.returncode==0 and not p.stderr and len(p.stdout)<=4*1024**2,'bounded offline Git');calls.append({'args':args,'sha256':sha(p.stdout),'bytes':len(p.stdout)});return p.stdout
required=json.loads(read(B/'REQUIRED_BODIES01.json'));ok(len(remote['selected_blobs'])==len(required)==7 and remote['selected_logical_bytes']==1063336,'exact external denominator')
for r in remote['selected_blobs']:
 b=read(T/'selected'/r['path'],r['sha256']);ok(b==read(ROOT/r['path']) and len(b)==r['bytes'] and required[r['path']]=={'bytes':r['bytes'],'sha256':r['sha256']},'external original required join');ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_object'] and r['git_mode']=='100644' and git(bare,['cat-file','blob',r['git_object']])==b,'fresh fetched Gitbody/OID')
recovered={};totals={'files':0,'typed':0}
for label in ('contract','support'):
 scope=T/('flat-'+label+'01');rec=flat['scopes'][label];meta=json.loads(read(scope/'body-metadata.json',rec['metadata_sha256']));mraw=read(T/'selected'/str((B/(label.upper()+'_MANIFEST01.json')).relative_to(ROOT)),rec['manifest_sha256']);m=json.loads(mraw);ok(meta['manifest']==m and meta['archive']==cap['scopes'][label]['archive'],'actual metadata full manifest/archive');rows=m['members'];files=[r for r in rows if r['kind']=='file'];ok(set(meta['flat_members'])=={r['path'] for r in files} and len(set(meta['flat_members'].values()))==len(files),'exact complete flat mapping');ok(set(p.name for p in scope.iterdir())==set(meta['flat_members'].values())|{'body-metadata.json'} and stat.S_IMODE(scope.stat().st_mode)==0o700,'fresh private exact output');data={}
 for r in files:
  p=scope/meta['flat_members'][r['path']];b=read(p,r['sha256']);ok(stat.S_IMODE(p.stat().st_mode)==0o600 and p.stat().st_nlink==1 and len(b)==r['bytes'],'private actual flatbody');ok(b==read(B/(label+'-snapshot')/r['path']),'flat snapshot bodyjoin');data[r['path']]=b
 archive=read(T/'selected'/str((B/('complete-'+label+'01.tar.gz')).relative_to(ROOT)),rec['archive_sha256']);out=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for r in rows:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tf.addfile(t)
    else:t.size=len(data[r['path']]);tf.addfile(t,io.BytesIO(data[r['path']]))
 ok(out.getvalue()==archive,'complete flat canonical gzip/PAX/footer reencoding');ok(len(rows)==rec['members'] and len(files)==rec['regular_bodies'] and m['root_mode']==rec['root_mode'],'all original mode/count metadata');totals['files']+=len(files);totals['typed']+=len(rows);recovered[label]=data
ok(totals=={'files':245,'typed':290},'full245/290')
q=json.loads(recovered['contract']['REQUEST_RELEASED01.json']);ok(sha(recovered['contract']['REQUEST_RELEASED01.json'])=='34d1a85660af70706bd52fd8187c9a48edec39841246f03b12e88051f92e56f9','actual recovered final request');contract=sha((json.dumps({k:v for k,v in q.items() if k!='final_review'},sort_keys=True,indent=2)+'\n').encode());ok(contract==cap['contract_sha256']=='6da30ea89cdf08a90de914fabdbc0616a4832cdbfaa363dec286ae43ff7751e4','nonrecursive contract');supporthash={sha(b) for b in recovered['support'].values()}
for ref in [*q['proofs'].values(),q['final_review']]:ok(sha(read(Path(ref['path']),ref['sha256'])) in supporthash,'genuine proofbytes restored')
ok(q['proofs']['full_recovery']['sha256']=='49e0ad65d23f34496963b09e82cb8744d0e56c6d5c1a598af48f7154bd0e9122','baselineproof never rewritten');C=Path(q['capsule_root']);P=Path(q['parent_root']);ok(git(C,['rev-parse','HEAD']).decode().strip()==q['source']==q['design_source']=='9dc5c79f738920b52947b4e63fed0397f1b5b207','current Source/design')
for name,h in q['source_files'].items():read(C/name,h)
reg=json.loads(read(C/q['registration'],q['registration_sha256']));exp=reg['experiments'][q['identity']];ok(len(q['source_files'])==338 and exp['source_files']==q['source_files'] and len(exp['inputs'])==8,'source338/eightroles')
for role,ref in exp['inputs'].items():read(C/ref['path'],q['input_hashes'][role]);ok(ref['sha256']==q['input_hashes'][role],'role joins')
r=q['runtime_mapping'];ok(len(r['distribution_records'])==251 and r['executable']==sys.executable and r['prefix']==sys.prefix,'runtime metadata domain');exe=Path(sys.executable).resolve();ok(exe.stat().st_size<=64*1024**2 and sha(exe.read_bytes())==r['executable_sha256'],'interpreter bounded hash');read(C/'uv.lock',r['lock_sha256'])
for row in r['distribution_records']:
 p=Path(row['record']);ok(p.is_relative_to(Path(sys.prefix)/'lib/python3.13/site-packages') and p.name=='RECORD','metadata RECORD domain');read(p,row['record_sha256']);ok(importlib.metadata.version(row['name'])==row['version'],'current metadata version')
claims=[]
for p in sorted((C/'research_runs').glob('*/claim.json')):
 z=json.loads(read(p));claims.append({'path':str(p),'sha256':sha(p.read_bytes()),'failed_sha256':sha(read(p.parent/'failed.json'))});ok(not os.path.lexists(p.parent/'complete.json'),'failed remains failed')
ok({x['sha256'] for x in claims}=={'4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b'},'both genuine spent claims only')
read(P/'recovery04.py','b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a');jobpath=next(x for x in q['source_files'] if x.endswith('/job.py'));ja=ast.parse((C/jobpath).read_bytes());prefix=ast.literal_eval(next(x.value for x in ja.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='PREFIX' for y in x.targets)))
for p in (P/'attempt',C/'research_runs'/q['identity'],C/prefix/'runs'/q['identity']):ok(not os.path.lexists(p),'no native/claim/job directory')
intent=json.loads(read(H/'ROOT_FINAL_SUPPLEMENT_FLAT01_INTENT.json'));exitbody=json.loads(read(H/'ROOT_FINAL_SUPPLEMENT_FLAT01_EXIT.json'));ok(intent['release_sha256']==sha((V/'FLAT_RELEASE01.json').read_bytes()) and intent['source_helper_sha256']==release['helper_sha256'] and intent['command']==[sys.executable,'-B',str(T/'restore02.py'),*release['argv']],'actual Root command release/source');stdout=read(H/'ROOT_FINAL_SUPPLEMENT_FLAT01.stdout');stderr=read(H/'ROOT_FINAL_SUPPLEMENT_FLAT01.stderr');ok(exitbody['actual_root_observed_helper_exit']==0 and not stderr and sha(stdout)==exitbody['stdout_sha256'] and sha(stderr)==exitbody['stderr_sha256'],'actual Root outer0/stdout/stderr');ok(flat['remote_receipt_sha256']==sha((T/'REMOTE_RECOVERY01.json').read_bytes()) and flat['capture_sha256']==sha((B/'CAPTURE01.json').read_bytes()) and flat['native_or_claim_started'] is False and flat['numerical_release'] is None,'actual receipt joins/qualification');ok(all(x['free_bytes']>=10*1024**3 and x['seconds']<180 for x in flat['floor_observations']) and len(flat['floor_observations'])<=32,'actual finitefloor observations');ok(not os.path.lexists(T/'FLAT_FAILED01.json'),'no failure receipt')
active=[];recorded={x['pid'] for x in remote['operations']};groups=[]
for p in Path('/proc').iterdir():
 if p.name.isdecimal():
  try:args=(p/'cmdline').read_bytes().split(b'\0');ps=(p/'stat').read_text().rsplit(')',1)[1].split()
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if int(p.name) in recorded or int(ps[2]) in recorded:groups.append(int(p.name))
  if any(v in args for v in (str(T/'restore02.py').encode(),str(T/'recover01.py').encode(),str(P/'parent01.py').encode(),q['identity'].encode())):active.append(int(p.name))
ok(not active and not groups,'current recorded Gitgroups/exact processes absent');ok(all(x['exit']==0 and x['cleanup_failures']==[] for x in remote['operations']) and len(remote['operations'])==25,'recorded actual remote operations');ok(shutil.disk_usage(D).free>=10*1024**3,'current10GiBfloor')
(D/'ACTUAL02.json').write_text(json.dumps({'checks':len(checks),'names':checks,'pins':pins,'totals':totals,'flat_receipt_sha256':sha((T/'FLAT_RECOVERY01.json').read_bytes()),'claims':claims,'offline_git_calls':calls,'current_processes':active,'current_recorded_groups':groups,'Root_original_PID_history':None,'native_authority':False},indent=2)+'\n');print(json.dumps({'checks':len(checks),'totals':totals}))
