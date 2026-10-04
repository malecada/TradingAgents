"""Prospective one-use external financial caller. No release from a null template."""
import argparse,ast,hashlib,importlib,json,os,re,resource,shutil,signal,stat,sys,time
from pathlib import Path
from types import SimpleNamespace
import recovery04 as R
from bounded_git01 import git
from supervisor01 import supervise
from descendants01 import pin as process_pin
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source')
PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-root-launch-20261004-01')
IDENTITY='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'
PYTHON='/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python'
PREFIX='tradingagents/research/onchain_replication/'
GIB=1024**3
PROOFS={'cumulative','full_recovery','independent_source_input_runtime'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(v,m):R.require(v,m)
def reference(ref):
 require(type(ref)is dict and set(ref)=={'path','sha256'},'exact external reference');p=Path(ref['path']);require(p.is_absolute() and p.resolve()==p,'reference canonical');raw=R.read(p.parent,p.name);require(sha(raw)==ref['sha256'],'reference bytes differ');return raw

def contract(q):return sha(R.encode({k:v for k,v in q.items() if k!='final_review'}))
def validate_release(q):
 fields={'schema_version','status','capsule_root','parent_root','identity','source','design_source','registration','registration_sha256','source_files','input_hashes','runtime_mapping','caller_sha256','helper_hashes','proofs','final_review','expected_phase'}
 require(type(q)is dict and set(q)==fields and q['schema_version']==1,'exact contract fields')
 require(q['status']=='RELEASED_ONE_USE_FINANCIAL_PARENT' and q['capsule_root']==str(CAP),'no draft release')
 for k in ('parent_root','identity','source','design_source','registration','registration_sha256','source_files','input_hashes','runtime_mapping','caller_sha256','helper_hashes','proofs','final_review','expected_phase'):require(q[k] is not None,'unresolved release field '+k)
 require(q['source']==q['design_source'] and re.fullmatch('[0-9a-f]{40}',q['source']) is not None,'job CLI requires identical source/design')
 require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',q['identity']) is not None,'fresh identity syntax')
 require(q['parent_root']==str(PARENT) and q['identity']==IDENTITY and q['expected_phase']=='interrupt1','fixed fresh recordfix initial context')
 require(set(q['proofs'])==PROOFS,'required actual proof roles')
 proof_pins={k:sha(reference(v)) for k,v in q['proofs'].items()}
 review=json.loads(reference(q['final_review']))
 require(review=={'schema_version':1,'decision':'accepted-exact-one-use-financial-parent','contract_sha256':contract(q),'proof_sha256':proof_pins,'identity':q['identity'],'source':q['source'],'caller_sha256':q['caller_sha256']},'exact independent release contract')
 return review

def stream_hash(path,limit):
 p=Path(path);require(p.is_absolute() and p.resolve()==p,'canonical read');fd=None
 try:
  s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_size<=limit,'stream extent/type');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);require(R.sig(s)==R.sig(os.fstat(fd)),'stream inode changed');h=hashlib.sha256();n=0;deadline=time.monotonic()+30
  while True:
   require(time.monotonic()<deadline,'read deadline');b=os.read(fd,min(65536,limit-n+1))
   if not b:break
   n+=len(b);require(n<=limit,'bounded read');h.update(b)
  require(n==s.st_size and R.sig(s)==R.sig(os.fstat(fd))==R.sig(p.lstat()),'stream changed');return h.hexdigest()
 finally:R._cleanup(() if fd is None else (lambda:os.close(fd),))

def memory():
 fields={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))}
 require(fields['MemTotal']<=16*GIB,'physical16GiB ceiling');require(fields['MemAvailable']>=6*GIB,'startup6GiB availability');return fields

def preflight(q):
 validate_release(q);parent=Path(q['parent_root']);require(parent.is_absolute() and parent.resolve()==parent and not parent.is_relative_to(CAP) and not CAP.is_relative_to(parent),'external parent')
 require(Path(__file__).resolve()==parent/'parent01.py' and sha(R.read(parent,'parent01.py'))==q['caller_sha256'],'installed exact parent')
 require(set(q['helper_hashes'])=={'supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json'},'exact parent helper closure')
 for name,pin in q['helper_hashes'].items():require('/' not in name and sha(R.read(parent,name))==pin,'parent helper hash')
 require(sys.executable==PYTHON,'checkout-local interpreter')
 require(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==q['source'],'actual source')
 for name,pin in q['source_files'].items():require(sha(R.read(CAP,name))==pin,'current source body')
 # Each registered source body is independently matched to the actual committed blob.
 names=sorted(q['source_files']);require(len(names)<=512,'source count')
 for start in range(0,len(names),64):
  batch=names[start:start+64];request=''.join(q['source']+':'+n+'\n' for n in batch).encode();raw=git(CAP,['cat-file','--batch'],request);offset=0
  for name in batch:
   end=raw.index(b'\n',offset);oid,kind,size=raw[offset:end].decode().split();size=int(size);body=raw[end+1:end+1+size]
   require(kind=='blob' and 0<=size<=R.FILE and sha(body)==q['source_files'][name] and raw[end+1+size:end+2+size]==b'\n','committed source body framing');offset=end+2+size
  require(offset==len(raw),'source batch tail')
 regraw=R.read(CAP,q['registration']);require(sha(regraw)==q['registration_sha256'] and git(CAP,['show',q['source']+':'+q['registration']])==regraw,'genuine committed registration')
 reg=json.loads(regraw);exp=reg['experiments'][q['identity']];require(exp['source_files']==q['source_files'],'full selected source map')
 require(reg['program_id'].startswith('financial-wrapper-engineering-'),'separate engineering program')
 family=reg['families'][exp['family']];require(type(family['attempt_budget'])is int and family['attempt_budget']==18 and type(family['prior_attempts'])is int and family['prior_attempts']==0 and 'cumulative_budget_extension' not in exp,'unchanged numerical18/prior0 without extension')
 require(set(exp['inputs'])==set(q['input_hashes']) and len(exp['inputs'])==8,'eight exact initial inputs')
 for role,ref in exp['inputs'].items():require(sha(R.read(CAP,ref['path']))==ref['sha256']==q['input_hashes'][role],'actual input pin')
 runtime=json.loads(R.read(CAP,exp['inputs']['runtime_mapping']['path']));require(runtime==q['runtime_mapping'],'runtime mapping')
 require(runtime['executable']==sys.executable and runtime['prefix']==sys.prefix and runtime['python']=='3.13.13','runtime mapping prefix')
 require(stream_hash(Path(sys.executable).resolve(),64*1024**2)==runtime['executable_sha256'] and sha(R.read(CAP,'uv.lock'))==runtime['lock_sha256'],'runtime interpreter/lock')
 require(len(runtime['distribution_records'])==251,'251 RECORDs')
 import importlib.metadata
 seen=set()
 for row in runtime['distribution_records']:
  require(row['name'] not in seen and importlib.metadata.version(row['name'])==row['version'],'runtime unique/version');seen.add(row['name']);p=Path(row['record']);require(p.is_relative_to(Path(sys.prefix)/'lib/python3.13/site-packages') and p.name=='RECORD' and p.parent.name.endswith('.dist-info'),'runtime RECORD scope');require(stream_hash(p,R.FILE)==row['record_sha256'],'runtime RECORD pin')
 protocol=json.loads(R.read(parent,'PROTOCOL_PINS01.json'))
 for name,pin in protocol.items():require(q['source_files'].get(name)==pin,'unchanged admitted job/native protocol')
 require(q['source_files'].get(PREFIX+'financial_wrapper_fixture.py')=='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c','accepted exact runtime RECORD correction required')
 require(not any(n.startswith('tradingagents') for n in sys.modules),'fresh package import')
 sys.path.insert(0,str(CAP));job=importlib.import_module('tradingagents.research.onchain_replication.job');fw=importlib.import_module('tradingagents.research.onchain_replication.financial_wrapper_fixture');storage=importlib.import_module('tradingagents.research.onchain_replication.workflow_storage')
 for name,module in tuple(sys.modules.items()):
  if name=='tradingagents' or name.startswith('tradingagents.'):
   path=Path(module.__file__).resolve();require(path.is_relative_to(CAP) and sha(R.read(CAP,path.relative_to(CAP).as_posix()))==q['source_files'][path.relative_to(CAP).as_posix()],'actual package prefix/hash')
 require(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no outside-native numerical import')
 j=json.loads(R.read(CAP,exp['inputs']['execution_job']['path']));job.job_schema(j);job.resource_policy(j['resources'],CAP);fw.schema(j)
 p=json.loads(R.read(CAP,exp['inputs']['wrapper_plan']['path']));fw.validate_plan(p);require(p['experiment']==q['identity'] and p['phase']==q['expected_phase'],'phase identity')
 r=j['resources'];require(r['disk_paths']==[str(CAP)] and r['storage_budget']['root']==str(CAP),'whole root watch')
 args=SimpleNamespace(root=str(CAP),registration=q['registration'],experiment=q['identity'],source=q['source'])
 # Genuine read-only admission executes the wrapper's exact installed runtime
 # predicate before any owned attempt directory, intent, or child creation.
 admitted,admitted_job=job._admitted(args)
 require(admitted_job==j and admitted.root==CAP and admitted.experiment_id==q['identity'] and admitted.experiment['source_files']==q['source_files'],'actual admission/source/job joins')
 require(admitted.effective_attempt_budget==18,'actual numerical ceiling18')
 for name,module in tuple(sys.modules.items()):
  if name=='tradingagents' or name.startswith('tradingagents.'):
   path=Path(module.__file__).resolve();require(path.is_relative_to(CAP) and sha(R.read(CAP,path.relative_to(CAP).as_posix()))==q['source_files'][path.relative_to(CAP).as_posix()],'post-admission actual package prefix/hash')
 require(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no preflight numerical import')
 command=job._command(args,'launch');require(command[:5]==[sys.executable,'-B','-m','tradingagents.research.onchain_replication.job','--mode'],'genuine job command')
 for path in (CAP/'research_runs'/q['identity'],job._base(args),parent/'attempt'):
  require(not os.path.lexists(path),'spent or reserved identity')
 memory();require(shutil.disk_usage(CAP).free>=10*GIB,'disk10GiB floor')
 return parent,args,command,job,storage,r

def child_cleanup(q,args,process,directory):
 base=Path(args.root)/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/args.experiment
 require(process is not None and process.poll() is not None,'supervisor not reaped')
 launch_path=base/'launch.json';live_path=base/'guard/live.json'
 cleanup=json.loads(R.read(directory,'owned-tree-cleanup.json'))
 require(cleanup['subreaper_used'] is True and cleanup['remaining_original_identities']==[],'owned descendant drainage incomplete')
 # Authenticate the unchanged pre-dispatch protocol, not merely absent live data.
 protocol=json.loads(R.read(Path(__file__).resolve().parent,'PROTOCOL_PINS01.json'))
 for name,pin in protocol.items():require(q['source_files'][name]==pin==sha(R.read(CAP,name)),'original creation protocol changed')
 if not live_path.exists():
  first=base/'guard';observed=[]
  for name in ('live.json','final.json','cpu_ready.json','release.json','child.log'):
   require(not os.path.lexists(first/name),'native record exists without original pre-dispatch live intent');observed.append(name)
  for row in cleanup['owned_pid_start_records']:
   current=process_pin(row['pid']);require(current is None or current['ticks']!=row['ticks'],'an original owned process can still dispatch')
  return {'existing_pre_dispatch_protocol_sha256':protocol,'owned_tree_cleanup_sha256':sha(R.read(directory,'owned-tree-cleanup.json')),'stable_absent_native_records':observed,'source_bound_no_dispatch':True,'requires_independent_outcome_review':True,'supervisor_pid':process.pid,'supervisor_exit':process.returncode}
 launch=json.loads(R.read(base,'launch.json'));owner=json.loads(R.read(base,'owner.json'));live=json.loads(R.read(base/'guard','live.json'))
 require(launch['supervisor_pid']==process.pid and launch['experiment']==q['identity'] and launch['source_commit']==q['source'] and all(owner[k]==v for k,v in launch.items()) and live['owner_identity']==owner,'native ownership joins')
 owned={row['pid']:row for row in cleanup['owned_pid_start_records']}
 require(owner['monitor_pid'] in owned and owned[owner['monitor_pid']]['ticks']==str(owner['monitor_start_ticks']),'original monitor PID/start join unavailable')
 unit=live['unit'];require(re.fullmatch(r'onchain-replication-[0-9a-f]{32}\.service',unit) is not None,'exact native unit')
 native_pids=[]
 ready=base/'guard/cpu_ready.json'
 if ready.exists():
  value=json.loads(R.read(base/'guard','cpu_ready.json'));pid=value.get('pid')
  if type(pid)is int:
   current=process_pin(pid)
   if current is not None:native_pids.append(current)
 known=live.get('cgroup')
 if known:
  cg=Path(known);require(cg.is_relative_to('/sys/fs/cgroup/user.slice') and cg.name==unit,'cgroup scope before census')
  if cg.exists():
   raw=(cg/'cgroup.procs').read_bytes();require(len(raw)<=65536,'finite cgroup PID list');pids=raw.split();require(len(pids)<=64,'native TasksMax census')
   for item in pids:
    current=process_pin(int(item))
    if current is not None:native_pids.append(current)
 results={}
 def control(label,command):
  target=directory/label;target.mkdir(mode=0o700)
  results[label]=supervise(['systemctl','--user',*command],CAP,os.environ.copy(),target,10)
  results[label]['stdout']=R.read(target,'stdout').decode('utf-8','strict');results[label]['stderr']=R.read(target,'stderr').decode('utf-8','replace')
 R._cleanup(tuple(lambda label=label,command=command:control(label,command) for label,command in [('before',['show',unit,'--property=ControlGroup,ActiveState,SubState,Result']),('stop',['stop',unit]),('after',['show',unit,'--property=ControlGroup,ActiveState,SubState,Result'])]))
 after=dict(line.split('=',1) for line in results['after']['stdout'].splitlines() if '=' in line)
 known=live.get('cgroup')
 if known:
  cg=Path(known);require(cg.is_relative_to('/sys/fs/cgroup/user.slice') and cg.name==unit,'native cgroup path');require(not cg.exists(),'native cgroup remains')
 else:
  require(not after.get('ControlGroup') and results['after']['exit_code']!=0,'unobserved original cgroup remains uncertain')
 require((after.get('ActiveState') in ('inactive','failed') and after.get('SubState') in ('dead','failed')) or (results['after']['exit_code']!=0 and not after),'native unit remains active')
 for row in cleanup['owned_pid_start_records']+native_pids:
  current=process_pin(row['pid']);require(current is None or current['ticks']!=row['ticks'],'original owned/native PID remains')
 return {'unit':unit,'cgroup':known,'actual_control_operations':results,'original_parent_exit':process.returncode,'joined_unit_stopped':True,'cgroup_absent':True,'native_pid_start_records':native_pids,'native_pid_census_is_complete_history':False,'subreaper_cleanup_sha256':sha(R.read(directory,'owned-tree-cleanup.json'))}

def launch(q):
 parent,args,command,job,storage,policy=preflight(q)
 # Search only actual job-module processes for this exact capsule, not arbitrary
 # command strings embedded in the coordinator's Python or shell source.
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:argv=(proc/'cmdline').read_bytes().split(b'\0')
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  if b'tradingagents.research.onchain_replication.job' in argv and str(CAP).encode() in argv:raise ValueError('an actual capsule job is active')
 watch=storage.StorageWatch(CAP,policy['storage_budget']['limits'])
 parentwatch=storage.StorageWatch(parent,{'max_allocated_bytes':80*1024**2,'max_logical_bytes':64*1024**2,'max_entries':512,'max_depth':12,'max_scan_seconds':5})
 def checked():
  watch.check();parentwatch.check();require(shutil.disk_usage(CAP).free>=10*GIB,'active disk floor')
 checked();memory();resource.setrlimit(resource.RLIMIT_FSIZE,(R.FILE,R.FILE));directory=parent/'attempt';directory.mkdir(mode=0o700)
 fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:R._cleanup((lambda:os.close(fd),))
 require(directory.resolve()==directory,'attempt redirected');child={'process':None};primary=None;result=None;cleanup_result=None
 handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
 def interrupted(number,frame):raise InterruptedError('financial parent interrupted')
 for sig in handlers:signal.signal(sig,interrupted)
 def spawned(process):child['process']=process;R.put(directory/'spawn.json',{'pid':process.pid,'argv':command,'source':q['source'],'identity':q['identity']})
 try:
  R.put(directory/'intent.json',{'identity':q['identity'],'source':q['source'],'contract':contract(q),'command':command,'cwd':str(CAP),'outer_active_seconds':1840,'phase':q['expected_phase']})
  env=os.environ.copy();env.update(job.resources._native_owned_env(CAP));env['PYTHONPATH']=str(CAP)
  result=supervise(command,CAP,env,directory,1840,checked,spawned)
 except BaseException as error:primary=error
 finally:
  def retain_cleanup():
   nonlocal cleanup_result
   if child['process'] is not None:cleanup_result=child_cleanup(q,args,child['process'],directory)
  def retain_terminal():
   R.put(directory/'parent-terminal.json',{'identity':q['identity'],'source':q['source'],'actual_child_exit':None if child['process'] is None else child['process'].returncode,'supervisor_result':result,'cleanup':cleanup_result,'primary_exception_observed':primary is not None,'actual_parent_exit':None,'error_type':None if primary is None else type(primary).__name__,'planned_interrupt_requested':q['expected_phase']=='interrupt1','outcome_semantics_accepted':False,'retained_outputs_location':str(job._base(args))})
  R._cleanup((retain_cleanup,retain_terminal,checked)+tuple(lambda sig=sig,old=old:signal.signal(sig,old) for sig,old in handlers.items()),primary=primary)
 if primary is not None:raise primary
 return result['exit_code']

def main():
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--launch',action='store_true');a=p.parse_args();raw=R.read(a.request.parent.resolve(),a.request.name);require(sha(raw)==a.sha256,'request pin');q=json.loads(raw)
 if a.launch:raise SystemExit(launch(q))
 else:validate_release(q)
if __name__=='__main__':main()
