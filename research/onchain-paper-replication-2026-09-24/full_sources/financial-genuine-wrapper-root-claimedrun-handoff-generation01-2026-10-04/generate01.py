"""Fixed metadata handoff only. No target creation, admission or numerical import."""
import ast,copy,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
from owned_io import _cleanup,_opened
H=Path(__file__).resolve().parent
OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source')
NEW=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PREFIX='fixture_inputs/financial_wrapper_claimedrun01'
ID='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'
SOURCE='649fb8a11089524aaef7843dffeeb90a3a55ca17'
WRAPPER='tradingagents/research/onchain_replication/financial_wrapper_fixture.py'
CANDIDATE='f4ea651b4677c83f8e16c316d17f704d44d9ec86ff78a4bf7c4b895e92e1a16e'
FILE=4*1024**2

def require(v,m):
 if not v:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def read(p,cap=FILE):
 require(p.is_absolute() and p.resolve()==p and not p.is_symlink(),'redirected path')
 signature=lambda z:(z.st_dev,z.st_ino,z.st_mode,z.st_nlink,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 fds=[];parents=[]
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);fds.append(fd);current=Path('/')
  parents.append((current,fd,signature(os.fstat(fd))))
  for part in p.parts[1:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);fds.append(fd);current=current/part;parents.append((current,fd,signature(os.fstat(fd))))
  before=os.stat(p.name,dir_fd=fd,follow_symlinks=False)
  require(stat.S_ISREG(before.st_mode) and before.st_size<=cap,'file type/extent')
  leaf=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd);fds.append(leaf)
  require(signature(os.fstat(leaf))==signature(before),'opened different file')
  b=bytearray()
  while True:
   x=os.read(leaf,min(65536,before.st_size-len(b)+1))
   if not x:break
   b.extend(x);require(len(b)<=before.st_size,'file growth')
  require(len(b)==before.st_size and signature(os.fstat(leaf))==signature(before)==signature(os.stat(p.name,dir_fd=fd,follow_symlinks=False))==signature(p.lstat()),'changed body')
  for parent,owned,initial in parents:
   require(parent.resolve()==parent and signature(parent.lstat())==initial==signature(os.fstat(owned)),'changed parent')
  require(p.resolve()==p,'late redirected path');return bytes(b)
 finally:_cleanup(tuple(lambda fd=fd:os.close(fd) for fd in reversed(fds)))
def git(*args):
 q=subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=OLD,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
 require(q.returncode==0 and len(q.stdout)<=FILE,'bounded read-only Git');return q.stdout

def derive(closure,job,plan,candidate):
 require(sha(candidate)==CANDIDATE,'exact accepted body')
 delta=json.loads(read(H/'SOURCE_CLOSURE_DELTA01.json'))
 require(sha(read(H/'SOURCE_CLOSURE_DELTA01.json'))=='8f84c97f5ae3bd8a3dadd2ac6538bf3c2aa1eeade5cbbf9bc36c2b5aabc4810d','exact source delta')
 expected={r['path']:r['original_sha256'] for r in delta['rows']}
 require(closure['installed']==expected and len(expected)==194 and sum(n.startswith('tradingagents/') for n in expected)==149,'exact194/149 baseline')
 c=copy.deepcopy(closure);c['installed'][WRAPPER]=CANDIDATE
 j=copy.deepcopy(job);j['resources']['disk_paths']=[str(NEW)];j['resources']['storage_budget']['root']=str(NEW)
 p=copy.deepcopy(plan);p['experiment']=p['namespace']=ID
 require(p['phase']=='interrupt1' and p['prior_input'] is None and p['reference_input'] is None,'fresh initial only')
 return c,j,p

def build():
 require(not os.path.lexists(NEW.parent),'proposed fresh capsule already exists')
 require(git('rev-parse','HEAD').decode().strip()==SOURCE,'immutable original source')
 raw=read(H/'BASE_INPUT_PINS01.json');require(sha(raw)=='24dc47afa6d200f2242512f2c6b9bd96b714488c0e406351a9a834de756159fa','input pin set');pins=json.loads(raw)
 root=OLD/'fixture_inputs/financial_wrapper_recordfix01';bodies={n:read(root/(n+'.json')) for n in pins}
 for n,b in bodies.items():require(sha(b)==pins[n],'original input changed '+n)
 tree={}
 for item in git('ls-tree','-r','-z',SOURCE).split(b'\0'):
  if not item:continue
  info,name=item.split(b'\t');mode,kind,oid=info.decode().split();name=name.decode();require(kind=='blob','tracked blob only');b=read(OLD/name);require(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'committed body differs');tree[name]={'git_mode':mode,'git_object':oid,'sha256':sha(b),'mode':stat.S_IMODE((OLD/name).stat().st_mode),'bytes':len(b)}
 require(len(tree)==325,'original325 tracked');closure=json.loads(bodies['source_closure'])
 for n,pin in closure['installed'].items():require(tree[n]['sha256']==pin,'actual installed source differs')
 c,j,p=derive(closure,json.loads(bodies['execution_job']),json.loads(bodies['wrapper_plan']),read(H/'candidate.py'))
 runtime=json.loads(bodies['runtime_mapping']);require(len(runtime['distribution_records'])==251,'251 RECORDs')
 require(runtime['executable']==sys.executable and runtime['prefix']==sys.prefix,'checkout locked interpreter')
 require(sha(read(Path(runtime['resolved_executable']),64*1024**2))==runtime['executable_sha256'] and sha(read(OLD/'uv.lock'))==runtime['lock_sha256'],'interpreter/lock bytes')
 for row in runtime['distribution_records']:require(sha(read(Path(row['record'])))==row['record_sha256'],'actual RECORD hash '+row['name'])
 gate=json.loads(bodies['gates']);require(len(gate['experiments'])==11,'preserve11 gate definitions')
 out={n+'.json':b for n,b in bodies.items() if n!='gates'}
 out.update({'source_closure.json':enc(c),'execution_job.json':enc(j),'wrapper_plan.json':enc(p),'ORIGINAL_GATES_PRESERVED.json':bodies['gates']})
 roles={n:{'path':PREFIX+'/'+n+'.json','sha256':sha(out[n+'.json'])} for n in pins if n!='gates'}
 descriptor={'status':'DRAFT_NOT_RELEASED','proposed_root':str(NEW),'identity':ID,'input_roles':roles,'implementation':194,'package':149,'changed':1,'unchanged':193,'original_tracked':325,'original_gate_definitions':11,'new_source':None,'design_source':None,'registration':None,'charter':None,'cumulative19_admission':None,'independent_source_review':None,'caller':None,'complete_recovery':None,'bindings':{},'require_current_equals_design':True,'source_file_map':None,'final_tracked_count':None,'historical_claims_spent':1,'historical_claim_preservation_required':True,'checkpoint_ancestry_from_failed_recordfix':False,'native_cpus':2,'release':False}
 out['HANDOFF01.json']=enc(descriptor);out['ORIGINAL_SOURCE_READBACK01.json']=enc({'source':SOURCE,'tracked':tree,'runtime_record_hashes_verified':251,'runtime_dependency_bodies_recovered':False,'runtime_api_observed':False})
 return out

def main():
 require('--release' not in sys.argv,'source handoff cannot release')
 output=H/'generated01';require(not os.path.lexists(output),'one-use generated directory');bodies=build();output.mkdir(mode=0o700)
 for n,b in bodies.items():
  with _opened(output/n,'xb') as f:f.write(b)
 print(json.dumps({'status':'DRAFT_NOT_RELEASED','files':len(bodies),'roles':8}))
if __name__=='__main__':main()
