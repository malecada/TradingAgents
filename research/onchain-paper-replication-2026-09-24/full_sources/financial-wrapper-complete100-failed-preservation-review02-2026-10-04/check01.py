from pathlib import Path
import ast,hashlib,json,stat,sys,importlib.util,subprocess,os,time
D=Path(__file__).resolve().parent;F=D.parent;A=F/'financial-wrapper-complete100-failed-preservation-tooling02-2026-10-04';C=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
ok(sha((A/'MANIFEST01.json').read_bytes())=='2a626b112f8119f77a483e0ca6ca7e1aafdabe8f5efa7b473389e326611e5fd7','exact126member authorseal');names=set()
for r in json.loads((A/'MANIFEST01.json').read_bytes())['members']:
 p=A/r['path'];s=p.lstat();names.add(r['path']);mode=int(r['mode'],8)if isinstance(r['mode'],str)else r['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'literal mode '+r['path'])
 if r['kind']=='file':ok(stat.S_ISREG(s.st_mode)and s.st_size==r['bytes']and sha(p.read_bytes())==r['sha256'],'wholebody '+r['path'])
 else:ok(stat.S_ISDIR(s.st_mode),'directory '+r['path'])
ok({p.relative_to(A).as_posix()for p in A.rglob('*')}==names|{'MANIFEST01.json'},'fullauthor closed membership')
for name,inv in json.loads((A/'SOURCE_INVERSE01.json').read_bytes()).items():
 s=(A/name).read_text()
 for e in reversed(inv['edits']):ok(s.count(e['new'])==1,'literalinverse occurrence '+name);s=s.replace(e['new'],e['old'])
 old=(A/('ORIGINAL_'+name)).read_text();ok(s==old and ast.dump(ast.parse(s))==ast.dump(ast.parse(old)),'wholeliteral AST inverse '+name)
sys.path.insert(0,str(A));import recover01 as R
ok(sha((A/'recover01.py').read_bytes())=='8b97e0219fdb8a85a9c0cdd0dde2cd8297d355d2cb5ef48ea661bae79f822d5c','exactremote candidate')
policy=dict(R.W.POLICY);ok(policy=={'logical':64*1024**2,'allocated':96*1024**2,'members':32768,'depth':32,'file':4*1024**2,'sample_seconds':5,'floor':10*1024**3,'samples':8192},'fixedforensic policy')
t=D/'owned';t.mkdir(mode=0o700);R.HERE=t;R.ROOT=t;R.START=time.monotonic();before=R.W.census(t);ok(before['logical_bytes']==0 and before['allocated_bytes']==t.stat().st_blocks*512,'initialempty whole allocation including root')
origin=t/'origin.git';received=t/'received.git';R.git(['init','--bare',str(origin)],t);R.git(['init','--bare',str(received)],t)
# Actual small local Git body only, no network or Main repository.
p=subprocess.run(['git','--git-dir',str(origin),'hash-object','-w','--stdin'],input=b'independent opaque body\0',capture_output=True,timeout=5);ok(p.returncode==0,'tiny actual object creation');oid=p.stdout.decode().strip();R.git(['fetch','--no-tags',str(origin),oid],received);ok(R.git(['cat-file','blob',oid],received)==b'independent opaque body\0','genuine local fetched bytes')
for row in R.CALLS:ok(row['actual_child_limits']=={'pid':row['pid'],'fsize':[4194304,4194304]}and row['exit']==0 and row['cleanup_failures']==[],'realchild PID/getrlimitreadback')
# Kernel-enforced individual file cap in a real local Git alias child.
probe=t/'fsize_probe.py';probe.write_text('import os\np=os.open("limit-negative",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\ntry:\n os.ftruncate(p,4194305)\nexcept OSError as e:\n print("LIMIT",e.errno)\nelse:\n raise AssertionError("cap bypass")\nfinally:\n os.close(p)\n')
output=R.git(['-c','alias.limit=!'+sys.executable+' -B '+str(probe),'limit'],t);ok(output.startswith(b'LIMIT '),'real inherited FSIZE refuses4MiBplus1')
# Actual bounded live child stopped/reaped on fatal census failure.
original_watch=R.watch;counter=[];fatal=MemoryError('independent sampledwatch fatal')
def injected():
 counter.append(1)
 if len(counter)==2:raise fatal
 return original_watch()
R.watch=injected
try:R.git(['-c','alias.pause=!sleep 2','pause'],t)
except BaseException as e:ok(e is fatal,'live child retainsfirstfatal')
else:raise AssertionError('watchfailure accepted')
finally:R.watch=original_watch
for row in R.CALLS:
 ok(not Path('/proc',str(row['pid'])).exists(),'actual localchild reaped '+str(row['pid']))
 try:os.killpg(row['pid'],0)
 except ProcessLookupError:checks.append('actual localgroup absent '+str(row['pid']))
 else:raise AssertionError('livegroup')
# Refusal types at exact whole-tree census; no limit widening.
safe=D/'safe';safe.mkdir(mode=0o700);(safe/'opaque').write_bytes(b'four');ok(R.W.census(safe)['logical_bytes']==4,'real tiny wholecensus')
for key,value in [('logical',3),('allocated',0),('members',1),('depth',-1),('sample_seconds',0),('floor',10**30)]:
 R.W.POLICY[key]=value
 try:
  try:R.W.census(safe)
  except ValueError:checks.append('tiny scaled refusal '+key)
  else:raise AssertionError(key)
 finally:R.W.POLICY.clear();R.W.POLICY.update(policy)
# Only changing-tree/FileNotFound have bounded complete sample retries.
original_sample=R.W._sample;calls=[]
def transient(root):
 calls.append(1)
 if len(calls)<3:raise FileNotFoundError('owned transient')
 return original_sample(root)
R.W._sample=transient
try:ok(R.W.census(safe)['complete_attempts']==3,'two transient complete retries then real sample')
finally:R.W._sample=original_sample
calls=[]
def fatal_sample(root):calls.append(1);raise fatal
R.W._sample=fatal_sample
try:
 try:R.W.census(safe)
 except BaseException as e:ok(e is fatal and len(calls)==1,'no fatal sampleretry')
finally:R.W._sample=original_sample
required=json.loads((A/'REQUIRED_BODIES01.json').read_bytes());ok(required==R.REQUIRED and len(required)==35,'unchanged35body scope');oids=set()
for name,row in required.items():
 b=(F.parents[2]/name).read_bytes();ok(len(b)==row['bytes']and sha(b)==row['sha256'],'actualselectedpin '+name);oids.add(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest())
ok(len(oids)==29 and 10+len(oids)+2*len(required)==109,'actual29uniqueOID109calls')
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'actual_local_Git_calls':R.CALLS,'actual_whole_tree_samples':R.WATCHES,'initial_actual_allocation':before,'fixed_policy':policy,'actual_external_or_entry':False,'sampling_is_not_continuous_quota':True},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks)}))
