"""Root-request-bound one-use entry to the genuine accepted proof supervisor.
No automatic registration, source changes, review inference or numerical imports.
"""
import argparse,hashlib,importlib.util,json,os,re,resource,shutil,signal,stat,subprocess,sys,time
from pathlib import Path
MAX=4194304;GIB=1024**3
INV='e8d8594d1c7aabe4076bf2b4bab7454cb0fad48ec8f46b754e06fc3f3ddb6773'
IDS={'materialize':'compact-cold-inputs-20261003-01','compare':'compact-cold-comparison-20261003-01'}
NS=('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs')
REVIEWS={'composition','registration','release','recovery','withdrawal'}
class CleanupFailure(BaseException):pass
def require(v,message):
 if not v:raise ValueError(message)
def fatal(e):return e is not None and (isinstance(e,(MemoryError,RecursionError)) or not isinstance(e,Exception)) and not isinstance(e,CleanupFailure)
def select(first,later):
 if fatal(first):return first
 if fatal(later) or first is None:return later
 if isinstance(later,CleanupFailure):return later
 return first
def actions(callbacks,primary=None):
 selected=primary;uncertain=False
 for cb in callbacks:
  try:cb()
  except BaseException as e:selected=select(selected,e);uncertain=True
 if selected is not primary and fatal(selected):raise selected
 if uncertain and not fatal(selected):raise CleanupFailure('owned root cleanup uncertain')
def direct(path):
 p=Path(path);require(p.is_absolute() and str(p)==str(path) and p.resolve()==p,'absolute canonical direct path required')
 for ancestor in (p,*p.parents):require(not ancestor.is_symlink(),'redirected path')
 return p
def relative(path):
 require(type(path)is str and path and '\\' not in path and '\0' not in path,'relative path text required');p=Path(path)
 require(not p.is_absolute() and str(p)==path and path!='.' and '..' not in p.parts,'unsafe relative path')
 return p
def signature(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(path,limit=MAX):
 p=direct(path);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);primary=None
 try:
  before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'bounded single-link regular file required')
  parts=[];total=0
  while True:
   part=os.read(fd,min(65536,limit-total+1))
   if not part:break
   total+=len(part);require(total<=limit,'body bound exceeded');parts.append(part)
  require(signature(before)==signature(os.fstat(fd))==signature(p.lstat()),'original file identity changed');return b''.join(parts)
 except BaseException as e:primary=e;raise
 finally:actions((lambda:os.close(fd),),primary)
def sha(b):return hashlib.sha256(b).hexdigest()
def refshape(v):
 require(type(v)is dict and set(v)=={'path','sha256'} and type(v['sha256'])is str and re.fullmatch('[0-9a-f]{64}',v['sha256']) and v['sha256']!='0'*64,'exact nonplaceholder reference required');direct(v['path'])
def reference(v):refshape(v);b=read(v['path']);require(sha(b)==v['sha256'],'reference hash differs');return b
def request_shape(q):
 require(type(q)is dict and set(q)=={'schema_version','phase','capsule','source','release','inventory','reviews','recovery','old_roots','output_parent','known_processes'},'exact root request required')
 require(type(q['schema_version'])is int and q['schema_version']==1 and q['phase'] in IDS,'request schema/phase differs');direct(q['capsule']);direct(q['output_parent'])
 require(type(q['source'])is str and re.fullmatch('[0-9a-f]{40}',q['source']) and q['source']!='0'*40,'actual source required')
 for name in ('release','inventory','recovery'):refshape(q[name])
 require(type(q['reviews'])is dict and set(q['reviews'])==REVIEWS,'all independent review roles required')
 for v in q['reviews'].values():refshape(v)
 require(type(q['old_roots'])is list and 1<=len(q['old_roots'])<=8,'withdrawn roots required')
 for old in q['old_roots']:
  require(type(old)is dict and set(old)=={'root','source','withdrawal','baseline'},'exact withdrawn root evidence required');direct(old['root']);refshape(old['withdrawal']);refshape(old['baseline']);require(re.fullmatch('[0-9a-f]{40}',old['source']) is not None,'old source required')
 require(type(q['known_processes'])is list and len(q['known_processes'])<=1024,'finite known PID list required')
 for p in q['known_processes']:require(type(p)is int and p>0,'actual integer PID required')
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE,timeout=10).decode().strip()
def absent(root,identities):
 for identity in identities:
  for ns in NS:require(not os.path.lexists(root/ns/identity),'identity namespace already exists')
def recovery(q,root):
 # The request pins an actual full recovered tree index; every body is freshly
 # compared in both roots. An accepted flag alone is never sufficient.
 v=json.loads(reference(q['recovery']));require(set(v)=={'schema_version','source','original_root','recovered_root','members'} and type(v['schema_version'])is int and v['schema_version']==1,'exact recovery index required')
 other=direct(v['recovered_root']);require(v['source']==q['source'] and v['original_root']==str(root) and other!=root and not other.is_relative_to(root) and not root.is_relative_to(other),'distinct actual recovery/source join required')
 rows=v['members'];require(type(rows)is list and 0<len(rows)<=32768,'finite full recovery members required');expected=[];started=time.monotonic();total=0
 for row in rows:
  require(set(row) in ({'path','kind'},{'path','kind','sha256','bytes'}),'recovery member schema');name=str(relative(row['path']));expected.append(name);require(time.monotonic()-started<30,'recovery verification deadline')
  for base in (root,other):
   p=direct(base/name)
   if row['kind']=='directory':require(set(row)=={'path','kind'} and p.is_dir(),'recovery directory differs')
   else:
    require(row['kind']=='file' and type(row['bytes'])is int and 0<=row['bytes']<=MAX,'recovery file extent differs');b=read(p);require(len(b)==row['bytes'] and sha(b)==row['sha256'],'actual recovered body differs')
  if row['kind']=='file':total+=row['bytes'];require(total<=128*1024**2,'initial recovery extent ceiling')
 require(expected==sorted(set(expected)),'sorted exact recovery membership required')
 for base in (root,other):
  actual=[]
  for p in base.rglob('*'):
   require(len(actual)<32768 and time.monotonic()-started<30,'recovery tree deadline/count');actual.append(str(p.relative_to(base)))
  require(sorted(actual)==expected,'full recovered tree membership differs')
 return {'members':len(rows),'logical_bytes':total,'index':q['recovery']}
def load(name,path):
 require(name not in sys.modules,'module already loaded before source authentication');s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def validate(q):
 request_shape(q);root=direct(q['capsule']);require(root.is_dir() and direct(root/'.git').is_dir() and not (root/'.git/objects/info/alternates').exists(),'isolated Git/no alternates required')
 require(git(root,'rev-parse','HEAD')==q['source'],'source HEAD differs')
 for r in q['reviews'].values():require(len(reference(r))>0,'empty independent review')
 inv=json.loads(reference(q['inventory']));require(q['inventory']['sha256']==INV and len(inv['source_inventory'])==195 and inv['package_count']==147,'exact accepted195 inventory required')
 sources={}
 for row in inv['source_inventory']:
  path=root/relative(row['target']);data=read(path);require(len(data)==row['bytes'] and sha(data)==row['sha256'],'selected source body differs');sources[row['target']]=row['sha256']
 require(len(sources)==195 and sum(n.startswith('tradingagents/') for n in sources)==147,'complete selected source denominator')
 for old in q['old_roots']:
  other=direct(old['root']);require(other!=root and git(other,'rev-parse','HEAD')==old['source'],'withdrawn root/source differs');reference(old['withdrawal']);reference(old['baseline']);absent(other,IDS.values())
 absent(root,[IDS[q['phase']]])
 require(not any(Path('/proc',str(p)).exists() for p in q['known_processes']),'known process remains or PID reused')
 recovered=recovery(q,root);release=json.loads(reference(q['release']));relpath=direct(q['release']['path']);require(relpath.is_relative_to(root),'release must be relative within capsule')
 require(release['source']==q['source'] and release['root']==str(root),'release source/root differs')
 require(Path.cwd()==root,'wrapper must run from actual capsule root')
 load('proof_raw01',root/'proof_tools/proof_raw01.py');api=load('proof_release01',root/'proof_tools/proof_release01.py');ctx=api.check_release(root,release,q['phase'])
 require(ctx['sources']==sources,'release complete195 map differs')
 roles=set(ctx['experiment']['inputs']);require(roles=={'recipe','configs','model','training','anchor','future_resources','environment','cold_proof','execution_job'} if q['phase']=='materialize' else len(roles)==44,'phase input roles differ')
 runtime=api.module('root_runtime_check',root/'proof_tools/runtime_gate01.py',sources['proof_tools/runtime_gate01.py']);runtime.check(root,ctx['runtime'])
 resources=api.module('root_native_resources',root/'tradingagents/research/onchain_replication/resources.py',sources['tradingagents/research/onchain_replication/resources.py']);require(resources._native_owned_env(root)==ctx['environment'],'native map differs')
 require(set(release['cpus'])<=os.sched_getaffinity(0) and resources.mem_available()>=6*GIB and shutil.disk_usage(root).free>=10*GIB,'actual startup resources unavailable')
 out=direct(q['output_parent']);require(out.is_dir() and not out.is_relative_to(root) and not root.is_relative_to(out) and shutil.disk_usage(out).free>=10*GIB,'separate root-owned output required')
 require(not os.path.lexists(out/IDS[q['phase']]),'root identity already reserved')
 return root,release,ctx,resources,recovered,str(relpath.relative_to(root))
def encoded(v):return (json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode()
def write(directory,name,data):
 require(type(data)is bytes and len(data)<=MAX,'root receipt bound');fd=os.open(directory/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);primary=None
 try:
  off=0
  while off<len(data):
   n=os.write(fd,data[off:off+65536]);require(n>0,'root receipt short write');off+=n
  os.fsync(fd)
 except BaseException as e:primary=e;raise
 finally:actions((lambda:os.close(fd),),primary)
 parent=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(parent)
 finally:actions((lambda:os.close(parent),),sys.exception())
def reserve(parent,identity,intent):
 d=direct(parent)/identity;d.mkdir(exist_ok=False)
 fd=os.open(d.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:actions((lambda:os.close(fd),),sys.exception())
 write(d,'intent.json',encoded(intent));return d
def root_watch(directory):
 total=0;count=0
 for p in directory.iterdir():
  count+=1;s=p.lstat();require(count<=32 and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=MAX,'root output file/count/type bound');total+=s.st_blocks*512
 require(total<=32*1024**2 and shutil.disk_usage(directory).free>=10*GIB,'root output storage stop threshold')
 return {'files':count,'allocated_bytes':total}
def execute(q,request_reference):
 root,release,ctx,resources,recovered,relative_release=validate(q);identity=IDS[q['phase']]
 command=[sys.executable,'-B',str(root/'proof_tools/proof_supervise01.py'),'--release',relative_release,'--release-sha256',q['release']['sha256'],'--phase',q['phase']]
 raw=sys.modules['proof_raw01'];primary=None;process=None;fds=[];handlers={};result=None;observed={}
 # Readbacks immediately precede permanent root reservation. Native unit limits
 # are established and independently authenticated only by the original route.
 available=resources.mem_available();free=shutil.disk_usage(root).free
 require(available>=6*GIB and free>=10*GIB,'fresh pre-reservation resource eligibility failed')
 resource.setrlimit(resource.RLIMIT_FSIZE,(MAX,MAX));require(resource.getrlimit(resource.RLIMIT_FSIZE)==(MAX,MAX),'root inherited file cap differs')
 directory=reserve(q['output_parent'],identity,{'schema_version':1,'kind':'root-launch-intent-not-research-claim','identity':identity,'phase':q['phase'],'source':q['source'],'request':request_reference,'release':q['release'],'reviews':q['reviews'],'recovery':recovered,'command':command,'parent_pid':os.getpid(),'memory_available_bytes':available,'disk_free_bytes':free,'file_limit':[MAX,MAX],'automatic_retry':False})
 def retain(e):
  nonlocal primary
  primary=select(primary,e)
 def stop(number,frame):raise InterruptedError('root wrapper interrupted')
 started=time.monotonic()
 try:
  for sig in (signal.SIGTERM,signal.SIGINT):handlers[sig]=signal.signal(sig,stop)
  for name in ('supervisor.stdout','supervisor.stderr'):fds.append(os.open(directory/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600))
  process=subprocess.Popen(command,cwd=root,env={**os.environ,**ctx['environment']},stdout=fds[0],stderr=fds[1],start_new_session=True)
  write(directory,'child.json',encoded({'pid':process.pid,'start_ticks':Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]}))
  while process.poll() is None:
   require(time.monotonic()-started<2250,'root supervisor wait deadline exceeded');root_watch(directory)
   for name in ('supervisor.stdout','supervisor.stderr'):require((directory/name).stat().st_size<MAX,'root log reached cap')
   time.sleep(.25)
  require(process.returncode==0,'actual proof supervisor failed')
  require(not Path('/proc',str(process.pid)).exists(),'supervisor PID remains or reused')
  wait=json.loads(read(root/'proof_supervise'/identity/'exit.json',8192));accepted=json.loads(read(root/'proof_outer'/identity/'accepted.json',8192))
  require(wait['status']=='accepted' and wait['phase']==q['phase'] and wait['identity']==identity and wait['source']==q['source'] and wait['supervisor_pid']==process.pid and wait['controller_exit_code']==0 and wait['controller_pid_absent'] is True,'actual supervisor/outer wait joins differ')
  require(not Path('/proc',str(wait['controller_pid'])).exists(),'outer PID remains or reused')
  require(wait['release']==accepted['release']=={'path':relative_release,'sha256':q['release']['sha256']} and accepted['status']=='accepted' and accepted['source']==q['source'] and accepted['identity']==identity,'original release/outer acceptance differs')
  for ns in ('proof_supervise','proof_outer'):
   for name in ('failed.json','late-failure.json'):require(not (root/ns/identity/name).exists(),'original late failure exists')
  raw.DEADLINE=time.monotonic()+55
  try:raw.authenticate(root,q['phase'],ctx);raw.closure(root,q['phase'],ctx['job']['resources']['storage_budget']['limits'])
  finally:raw.DEADLINE=None
  require(git(root,'rev-parse','HEAD')==q['source'],'source changed during actual invocation')
  for name,expected in ctx['sources'].items():require(sha(read(root/name))==expected,'source changed after invocation')
  for info in ctx['experiment']['inputs'].values():require(sha(read(root/info['path']))==info['sha256'],'input changed after invocation')
  result={'wrapper_observation':'actual-supervisor-and-outer-exit0-authenticated','supervisor_pid':process.pid,'supervisor_exit_code':process.returncode,'outer_pid':wait['controller_pid'],'outer_exit_code':wait['controller_exit_code']}
 except BaseException as e:retain(e)
 finally:
  if process is not None:
   try:
    if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
   except BaseException as e:retain(e)
   try:
    try:process.wait(timeout=90)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5);raise CleanupFailure('supervisor forced kill; descendant cleanup requires retained original evidence')
   except BaseException as e:retain(e)
  try:actions(tuple(lambda fd=fd:os.close(fd) for fd in fds),primary)
  except BaseException as e:retain(e)
  for sig,handler in handlers.items():
   try:signal.signal(sig,handler)
   except BaseException as e:retain(e)
  # Pure observations only, never fabricate a lifecycle/native terminal. Missing
  # receipts remain missing and success is impossible without all joins above.
  try:
   for prefix in ('research_runs','proof_supervise','proof_outer'):
    for name in ('claim.json','complete.json','failed.json','accepted.json','late-failure.json','exit.json'):
     p=root/prefix/identity/name
     if p.exists():observed[prefix+'/'+name]={'path':str(p),'sha256':sha(read(p))}
   disposition='unclaimed' if 'research_runs/claim.json' not in observed else 'actual-complete-receipt-present' if 'research_runs/complete.json' in observed else 'actual-failed-receipt-present' if 'research_runs/failed.json' in observed else 'claimed-no-terminal-observed'
   summary={'schema_version':1,'kind':'root-observation-not-child-terminal','identity':identity,'phase':q['phase'],'source':q['source'],'request':request_reference,'supervisor_exit_code':None if process is None else process.returncode,'result':result if primary is None else None,'disposition':disposition,'original_receipts':observed,'root_output_before_own_tail':root_watch(directory),'automatic_retry':False}
   write(directory,'observation.json',encoded(summary))
  except BaseException as e:retain(e)
  if primary is not None:
   try:
    import traceback
    text=''.join(traceback.format_exception(primary)).encode('utf8','backslashreplace');require(len(text)<=MAX,'full error exceeds root log bound');write(directory,'error.txt',text)
   except BaseException as e:retain(e)
   try:write(directory,'failure.json',encoded({'kind':'root-wrapper-failed','error_type':type(primary).__name__,'automatic_retry':False,'child_terminal_synthesized':False}))
   except BaseException as e:retain(e)
  try:root_watch(directory)
  except BaseException as e:retain(e)
 if primary is not None:raise primary
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--request-sha256',required=True);a=p.parse_args()
 r={'path':str(direct(a.request)),'sha256':a.request_sha256};q=json.loads(reference(r));execute(q,r)
if __name__=='__main__':main()
