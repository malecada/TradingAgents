"""Read-only genuine source/runtime census and unusable-for-launch auxiliary drafts."""
import argparse,hashlib,json,os,platform,re,shutil,stat,sys,time
from pathlib import Path
from email.parser import BytesParser
import recovery04 as R
from bounded_git01 import git
HERE=Path(__file__).resolve().parent
MAIN=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
COMMIT='390c82a9958e135c24bcca80f3a636313ca27932'
PRIOR_RUNTIME=MAIN/'research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-root-integration02-2026-10-03/installed-runtime-records02.json'
PRIOR_RUNTIME_SHA256='2fb523f58c562933a56762fcdbf1a1806bc5af3fe0a68020d4f5c70037ecc59a'
ORIGINS='768c6441c08d7d39a69435aff171db4912eb8f9e64e440e861c15eb54c32a0ab'
LOCK='f7a1829c0ae554fb00923eb07c3c5e5370c1eadb52698ea657446c64d6c83b9a'
STREAM=64*1024**2
BASE_INPUTS={'environment','execution_job','model','runtime_mapping','source_closure','synthetic_recipe','training','wrapper_plan'}

def blob_oid(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def read(path):
 p=Path(path);return R.read(p.parent,p.name)
def origins():
 raw=read(HERE/'ORIGIN_PINS01.json');R.require(R.digest(raw)==ORIGINS,'frozen origins differ');refs=json.loads(raw);values={}
 for role,ref in refs.items():
  raw=read(ref['path']);R.require(R.digest(raw)==ref['sha256'],'origin body differs: '+role);values[role]=raw
 return refs,values

def stream_pin(path,limit=STREAM,*,runtime_metadata=False):
 """Only the fixed resolved interpreter uses the 64MiB reader; no whole-body buffer."""
 p=Path(path);R.path_name(str(p).lstrip('/'));R.require(p.is_absolute() and p.resolve()==p,'canonical stream path');fd=None;parent=None
 try:
  parent=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);ps=os.fstat(parent);before=p.lstat()
  R.require(stat.S_ISREG(before.st_mode) and (before.st_nlink>=1 if runtime_metadata else before.st_nlink==1) and before.st_size<=limit,'stream regular/singlelink/extent')
  fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent);R.require(R.sig(os.fstat(fd))==R.sig(before),'stream replacement')
  h=hashlib.sha256();count=0;deadline=time.monotonic()+30;parts=[]
  while True:
   R.require(time.monotonic()<deadline,'stream deadline');b=os.read(fd,min(65536,limit-count+1))
   if not b:break
   count+=len(b);R.require(count<=limit,'stream exceeded64MiB');h.update(b)
   if runtime_metadata:parts.append(b)
  R.require(count==before.st_size and R.sig(before)==R.sig(os.fstat(fd))==R.sig(p.lstat()),'stream changed')
  R.require(R.sig(ps)==R.sig(os.fstat(parent))==R.sig(p.parent.lstat()) and p.resolve()==p,'stream parent changed')
  if runtime_metadata:return b''.join(parts)
  return {'path':str(p),'bytes':count,'sha256':h.hexdigest(),'mode':stat.S_IMODE(before.st_mode)}
 finally:R._cleanup((() if fd is None else (lambda:os.close(fd),))+(() if parent is None else (lambda:os.close(parent),)))

def parse_tree(raw):
 R.require(len(raw)<=R.FILE,'bounded Git tree');rows={}
 for item in raw.split(b'\0')[:-1]:
  header,name=item.split(b'\t',1);mode,kind,oid=header.decode().split();name=name.decode();R.path_name(name)
  R.require(name not in rows and kind=='blob' and mode in ('100644','100755') and len(oid)==40 and all(c in '0123456789abcdef' for c in oid),'Git tree mode/type/name')
  rows[name]={'git_mode':mode,'oid':oid}
 R.require(raw.endswith(b'\0'),'tree terminator');return rows

def authenticate_sources(values):
 R.require((CAP/'.git').is_dir() and (CAP/'.git').resolve()==CAP/'.git','genuine Git directory')
 for name in ('.git/objects/info/alternates','.git/info/grafts','.git/refs/replace'):R.require(not os.path.lexists(CAP/name),'foreign Git ancestry')
 closure=json.loads(values['SOURCE_CLOSURE01.json']);pins=closure['installed'];review=json.loads(values['INSTALLED_REVIEW']);selected={r['path']:r for r in review['joined']}
 R.require(review['source_commit']==COMMIT and review['source_root']==str(CAP) and len(pins)==194 and set(pins)==set(selected),'review source membership')
 R.require(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==COMMIT,'actual source HEAD')
 tree=parse_tree(git(CAP,['ls-tree','-r','-z',COMMIT],cap=R.FILE));R.require(set(tree)==set(pins),'complete committed194 set')
 package=R.scan(CAP/'tradingagents')
 live={'tradingagents/'+r['path'] for r in package['members'] if r['kind']=='file'}
 R.require(live=={p for p in pins if p.startswith('tradingagents/')} and len(live)==149,'complete package149')
 rows=[];names=sorted(pins);aggregate=0
 # Read original blobs in fresh bounded groups; no result persists across builder calls.
 for start in range(0,len(names),64):
  chunk=names[start:start+64];request=''.join(COMMIT+':'+n+'\n' for n in chunk).encode();reply=git(CAP,['cat-file','--batch'],request);offset=0
  for name in chunk:
   raw=R.read(CAP,name);aggregate+=len(raw);R.require(aggregate<=STREAM,'total source read bound')
   row=selected[name];current=(CAP/name).lstat();end=reply.index(b'\n',offset);oid,kind,size=reply[offset:end].decode().split();size=int(size);body=reply[end+1:end+1+size]
   R.require(kind=='blob' and size<=R.FILE and body==raw and reply[end+1+size:end+2+size]==b'\n','actual blob body framing')
   R.require(R.digest(raw)==pins[name]==row['sha256'] and len(raw)==row['bytes'] and stat.S_IMODE(current.st_mode)==row['mode'],'installed source bytes/mode')
   R.require(oid==blob_oid(raw)==tree[name]['oid']==row['oid'] and tree[name]['git_mode']==row['git_mode'],'source OID/mode')
   rows.append({'path':name,'sha256':R.digest(raw),'bytes':len(raw),'mode':stat.S_IMODE(current.st_mode),**tree[name]});offset=end+2+size
  R.require(offset==len(reply),'trailing source batch')
 R.require(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==COMMIT,'source HEAD changed')
 return rows

def baseline_runtime_join(mapping):
 raw=read(PRIOR_RUNTIME);R.require(R.digest(raw)==PRIOR_RUNTIME_SHA256,'prior runtime body pin');prior=json.loads(raw)
 def normalized(rows):
  result={}
  for row in rows:
   name=re.sub(r'[-_.]+','-',row['name']).lower();R.require(name not in result,'normalized distribution collision');result[name]={**row,'name':name}
  return result
 R.require(normalized(mapping['distribution_records'])==normalized(prior['distribution_records']),'all251 original RECORD/version/path pins differ')
 R.require(all(mapping[k]==prior[k] for k in mapping if k!='distribution_records'),'original interpreter/prefix/lock pins differ')
 return {'prior_runtime_path':str(PRIOR_RUNTIME),'prior_runtime_sha256':PRIOR_RUNTIME_SHA256,'all251_prior_records_equal':True}

def runtime(values):
 R.require(platform.python_version()=='3.13.13' and sys.executable==str(MAIN/'.venv/bin/python') and sys.prefix==str(MAIN/'.venv'),'actual pinned interpreter/prefix')
 executable=Path(sys.executable).resolve();ep=stream_pin(executable)
 lock=read(MAIN/'uv.lock');R.require(R.digest(lock)==LOCK,'locked runtime source changed')
 old=json.loads(values['RUNTIME_CHECK02.json']);versions=old['installed_versions']
 site=Path(sys.prefix)/'lib/python3.13/site-packages';R.require(site.resolve()==site,'runtime package root redirected')
 paths=[]
 with os.scandir(site) as entries:
  for entry in entries:
   if entry.name.endswith('.dist-info'):
    R.require(not entry.is_symlink() and entry.is_dir(follow_symlinks=False) and len(paths)<512,'runtime distribution bound/type');paths.append(site/entry.name)
 rows=[];metadata_pins=[];total=0
 for path in sorted(paths):
  raw=stream_pin(path/'METADATA',R.FILE,runtime_metadata=True);total+=len(raw);message=BytesParser().parsebytes(raw,headersonly=True);raw_name=message['Name'];version=message['Version'];R.require(type(raw_name) is str,'distribution name');name=re.sub(r'[-_.]+','-',raw_name).lower()
  R.require(type(name) is str and type(version) is str and versions.get(name)==version,'locked distribution name/version')
  record=stream_pin(path/'RECORD',R.FILE,runtime_metadata=True);total+=len(record);R.require(total<=STREAM,'runtime metadata64MiB aggregate')
  rows.append({'name':name,'version':version,'record':str(path/'RECORD'),'record_sha256':R.digest(record)})
  metadata_pins.append({'name':name,'metadata_sha256':R.digest(raw),'metadata_bytes':len(raw),'record_bytes':len(record)})
 R.require(len(rows)==251 and len({r['name'] for r in rows})==251 and set(r['name'] for r in rows)==set(versions),'complete251 distribution mapping')
 rows.sort(key=lambda r:r['name'])
 mapping={'python':platform.python_version(),'executable':sys.executable,'resolved_executable':str(executable),'prefix':sys.prefix,'executable_sha256':ep['sha256'],'lock_sha256':LOCK,'distribution_records':rows}
 env={'python':platform.python_version(),'cpu_count':os.cpu_count(),'lock_sha256':LOCK,'packages':{p:versions[p] for p in ('numpy','scipy','pyarrow','torch','scikit-learn')},'cuda_available':None,'torch_version':None,'cuda_build':None}
 return mapping,env,{'prior_runtime_join':baseline_runtime_join(mapping),'interpreter':ep,'metadata':metadata_pins,'metadata_bytes':total,'torch_imported':False,'dependency_bodies_fully_rehashed':False,'financial_root_lock_installed':(CAP/'uv.lock').exists()}

def refuse_runnable(_draft):raise ValueError('DRAFT_NOT_RELEASED: no runnable admission; identities, charter, registration, native Torch environment and genuine dependency outcomes unresolved')

def build():
 out=HERE/'generated02';R.require(not os.path.lexists(out),'one-use draft namespace already reserved');R.require(shutil.disk_usage(HERE).free>=R.FLOOR,'10GiB disk floor')
 refs,values=origins();source=authenticate_sources(values);mapping,env,observations=runtime(values)
 # All source/runtime reads precede reserving this new draft output. No live writes.
 out.mkdir(mode=0o700);prepared={}
 def save(name,raw):
  with R.new_file(out/name) as fd:s=R.Sink(fd);s.write(raw);os.fsync(fd)
  R.require(read(out/name)==raw,'draft readback');prepared[name]={'prepared_path':str(out/name),'bytes':len(raw),'sha256':R.digest(raw)}
 for role,n in [('source_closure','SOURCE_CLOSURE01.json'),('model','model.json'),('training','training.json'),('synthetic_recipe','RECIPE01.json')]:save(role+'.json',values[n])
 save('runtime_mapping.json',R.encode(mapping));save('environment.DRAFT.json',R.encode(env));save('SOURCE_READBACK01.json',R.encode({'source':COMMIT,'recipe_sources':194,'package':149,'nonpackage':45,'rows':source}))
 save('RUNTIME_READBACK01.json',R.encode(observations))
 # Metadata auxiliary origins are proposed separately; never folded into194.
 for name in ('uv.lock','pyproject.toml','.python-version'):save('proposed-'+name,read(MAIN/name))
 phases=json.loads(values['PHASE_TEMPLATES01.json'])['templates'];dag=json.loads(values['PHASE_DAG01.json']);R.require(len(phases)==len(dag['rows'])==18,'exact phase denominator')
 slots=[]
 for index,(plan,row) in enumerate(zip(phases,dag['rows'],strict=True),1):
  key=plan['task']+'/'+plan['execution']+'/'+plan['phase'];R.require(key==row['logical_key_not_identity'],'phase DAG order')
  R.require(all(plan[k] is None for k in ('cell_id','experiment','namespace')),'unreserved identities')
  job=json.loads(values['JOB_TEMPLATE01.json']);job['resources']['disk_paths']=[str(CAP)];job['resources']['storage_budget']['root']=str(CAP)
  pn='plan-'+str(index).zfill(2)+'.DRAFT.json';jn='job-'+str(index).zfill(2)+'.DRAFT.json';save(pn,R.encode(plan));save(jn,R.encode(job))
  bindings={}
  for role in sorted(BASE_INPUTS):
   name={'environment':'environment.DRAFT.json','wrapper_plan':pn,'execution_job':jn}.get(role,role+'.json')
   bindings[role]={'path':None,'dataset':None,'sha256':prepared[name]['sha256'],'prepared_path':prepared[name]['prepared_path']}
  R.require(set(bindings)==BASE_INPUTS,'exact8 role set')
  slots.append({'logical_key_not_identity':key,'slot_index':index,'inputs':bindings,'dependencies':row['dependencies'],'actual_outcome':None,'admitted':False})
 draft={'status':'DRAFT_NOT_RELEASED','source_commit_observed':COMMIT,'source_recipe_count':194,'package_count':149,'future_admitted_source_total':None,'phase_slots_unreserved':18,'paper_financial_fit_credit':0,'source_closure_is_complete_recipe_only':True,'slots':slots,'auxiliary_pins':prepared,'future':{k:None for k in ('program','family','cumulative_budget','charter','registration','release_caller','native_environment_evidence','genuine_dependency_outcomes','external_recovery')},'holds':['Live Torch/CUDA inventory cannot be observed without separately authorized numeric import','Root must adopt actual lock/project/runtime and all inputs in capsule','Every plan retains null fresh cell/experiment/namespace','Dependent outcomes remain unavailable','194 recipe is distinct from future total auxiliary/source admission pins']}
 R.put(out/'DRAFT01.json',draft);R.require(shutil.disk_usage(out).free>=R.FLOOR,'final10GiBfloor');return draft
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build-draft',action='store_true');p.add_argument('--release',action='store_true');a=p.parse_args()
 if a.release:refuse_runnable(None)
 R.require(a.build_draft,'explicit draft mode required');d=build();print(json.dumps({'status':d['status'],'source':COMMIT,'slots':18,'paper_fit_credit':0}))
