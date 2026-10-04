"""Read-only opaque composition observations. Never creates a proof, restores, or grants entry."""
import argparse,gzip,hashlib,io,json,os,re,stat,tarfile,time,types
from pathlib import Path
FILE=4*1024**2; TOTAL=256*1024**2; LIMIT=32768; SECONDS=180
SOURCE='7b056a574e3e7b3c7ba209a39ee6a615e649d60c'
POLICY='ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887'
CLOSURE='af61a1de642d029579230fb3980e87eefe8dc5e0e7ba6a965393f194e996c92c'
CHECKER='d0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8'
OLDMAP='ebb1727ccb55678aead9f0d5b5ee43ec81a46019c7fbb13c4b4f76144507bbca'
NEWMAP='2e281f7ca64a12be316424d8e93b0eab28ba0d121214e79ada7249c96930b040'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
INPUTS_PIN='f992329f1e0baf29bff17eaa1ba82d0f0fe73edf5f8845b9d30a7386f630f4af'
def h(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def require(v,msg):
 if not v:raise ValueError(msg)
def unique(pairs):
 d={}
 for k,v in pairs:require(k not in d,'duplicate JSON key');d[k]=v
 return d
def decode(b):return json.loads(b,object_pairs_hook=unique,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def sig(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks','st_uid'))
def mode(x):return int(x,8) if isinstance(x,str) else x
def safe(n):
 require(type(n) is str and n and not n.startswith('/') and all(x not in ('','.','..','keys','apis','.env','hf_token.txt') for x in n.split('/')) and len(n.split('/'))<=32,'unsafe relative name');return n
# Exact pinned owned_io dependency is embedded as immutable bytes to avoid introducing
# another filesystem/bootstrap cleanup path. The retained owned_io.py is byte-identical.
OWNED_IO_BYTES = b'"""Owned IO cleanup only; pure stdlib, no numerical or authority imports."""\nimport os\nimport sys\nfrom contextlib import contextmanager\n\ndef _require(value,message):\n    if not value:raise ValueError(message)\n\nclass CleanupFailure(BaseException):\n    """An owned close was uncertain; stop the worker, never retry its fd integer."""\n\n_UNSET = object()\n\ndef _fatal(error):\n    return (isinstance(error,MemoryError) or not isinstance(error,Exception)) and not isinstance(error,CleanupFailure)\n\ndef _flatten(errors):\n    # Only owned cleanup wrappers carry this tuple; retain actual fatal objects.\n    result=[];seen=set();pending=list(reversed(errors))\n    while pending:\n        error=pending.pop()\n        if id(error) in seen:continue\n        seen.add(id(error))\n        if isinstance(error,CleanupFailure) and hasattr(error,\'failures\'):\n            pending.extend(reversed(error.failures))\n        else:result.append(error)\n    return result\n\ndef _cleanup(actions,*,primary=_UNSET):\n    """Close every owned resource once; first actual fatal outranks uncertainty."""\n    if primary is _UNSET:primary=sys.exception()\n    failures=[]\n    for close in actions:\n        try:close()\n        except BaseException as error:failures.append(error)\n    if not failures:return\n    causes=_flatten(([primary] if primary is not None else [])+failures)\n    selected=next((error for error in causes if _fatal(error)),None)\n    if selected is not None:\n        others=[error for error in causes if error is not selected]\n        if selected is primary:return\n        if others:\n            # Optional evidence attachment must never replace the selected fatal.\n            try:\n                if selected.__cause__ is not None and all(selected.__cause__ is not e for e in others):others.append(selected.__cause__)\n                selected.__cause__=others[0] if len(others)==1 else BaseExceptionGroup(\'prior body/cleanup evidence\',others)\n            except BaseException:pass\n        raise selected\n    failure=CleanupFailure(\'score storage cleanup unresolved; worker must stop\')\n    failure.failures=tuple(causes)\n    failure.__cause__=causes[0] if len(causes)==1 else BaseExceptionGroup(\'body/cleanup failures\',causes)\n    raise failure\n\ndef _close_after_failure(close,primary):\n    _cleanup((close,),primary=primary)\n\ndef _release(close):\n    _cleanup((close,))\n\n@contextmanager\ndef _closing(value):\n    try:yield value\n    finally:_release(value.close)\n\n@contextmanager\ndef _opened(path,mode):\n    _require(mode in (\'rb\',\'xb\'),\'explicit immutable file mode required\')\n    flags=os.O_NOFOLLOW|os.O_CLOEXEC\n    flags|=(os.O_RDONLY|os.O_NONBLOCK) if mode==\'rb\' else (os.O_WRONLY|os.O_CREAT|os.O_EXCL)\n    fd=os.open(path,flags,0o600);stream=None\n    try:\n        stream=os.fdopen(fd,mode,closefd=False)\n        yield stream\n    finally:\n        _cleanup((() if stream is None else (stream.close,))+(lambda:os.close(fd),))\n\ndef _read_path(path,limit):\n    with _opened(path,\'rb\') as stream:\n        raw=stream.read(limit+1)\n        _require(len(raw)<=limit,\'immutable metadata bound exceeded\')\n        return raw\n'
require(h(OWNED_IO_BYTES)=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','owned IO dependency pin')
IO=types.ModuleType('_composed_pinned_owned_io')
exec(compile(OWNED_IO_BYTES,'<pinned owned_io09d1fbcc>','exec'),IO.__dict__)
def _retain(selected,errors):
 # Diagnostic retention is optional and cannot replace the already selected error.
 if selected is None:return
 try:
  namespace=BaseException.__dict__['__dict__'].__get__(selected)
  prior=namespace.get('composed_failures',())
  if not isinstance(prior,tuple):prior=(prior,)
  retained=list(prior)
  for error in errors:
   if error is not None and error is not selected and all(error is not e for e in retained):retained.append(error)
  if retained:namespace['composed_failures']=tuple(retained)
 except BaseException:pass
def _finish(actions,primary):
 failures=[];selected=primary
 def wrapped(action):
  def close():
   try:action()
   except BaseException as error:failures.append(error);raise
  return close
 try:IO._cleanup(tuple(wrapped(action) for action in actions),primary=primary)
 except BaseException as error:selected=error;raise
 finally:_retain(selected,([primary] if primary is not None else [])+failures)
class Reader:
 def __init__(self):self.start=time.monotonic();self.cache={};self.pins={};self.anchors={};self.trees={};self.total=0
 def tick(self):require(time.monotonic()-self.start<SECONDS,'deadline');require(len(self.pins)+len(self.anchors)<=LIMIT,'member bound')
 def anchor(self,p):
  self.tick();require(p.is_absolute() and p.resolve(strict=True)==p,'canonical path');s=p.lstat();require(stat.S_ISDIR(s.st_mode),'directory type')
  q=(s.st_dev,s.st_ino,s.st_mode,s.st_uid);require(p not in self.anchors or self.anchors[p]==q,'ancestor changed');self.anchors[p]=q
 def read(self,p,pin=None,expected_mode=None):
  p=Path(p);self.tick()
  for q in reversed(p.parents):self.anchor(q)
  s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE,'regular extent/link')
  require(expected_mode is None or stat.S_IMODE(s.st_mode)==expected_mode,'file mode')
  before=sig(s);require(p not in self.pins or self.pins[p]==before,'changed cached file')
  if p in self.cache:b=self.cache[p]
  else:
   fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);primary=None;parts=[];count=0
   try:
    require(sig(os.fstat(fd))==before,'open identity')
    while True:
     self.tick();chunk=os.read(fd,min(65536,FILE+1-count))
     if not chunk:break
     parts.append(chunk);count+=len(chunk);require(count<=FILE,'read extent')
    require(sig(os.fstat(fd))==before,'descriptor changed')
   except BaseException as e:primary=e;raise
   finally:_finish((lambda:os.close(fd),),primary)
   b=b''.join(parts);require(sig(p.lstat())==before and len(b)==s.st_size,'post-close currentness');self.total+=len(b);require(self.total<=TOTAL,'total read bound');self.cache[p]=b;self.pins[p]=before
  require(pin is None or h(b)==pin,'body hash '+str(p));return b
 def j(self,p,pin=None):return decode(self.read(p,pin))
 def tree(self,root,exclude=()):
  root=Path(root);self.anchor(root);found={};pending=[root]
  while pending:
   p=pending.pop();self.tick();s=p.lstat();require(stat.S_ISDIR(s.st_mode),'tree directory')
   it=None;primary=None
   try:
    it=os.scandir(p)
    for e in it:
     self.tick();n=str(Path(e.path).relative_to(root))
     if p==root and e.name in exclude:continue
     safe(n);t=os.lstat(e.path);require(stat.S_ISREG(t.st_mode) or stat.S_ISDIR(t.st_mode),'tree special');require(len(found)<LIMIT,'tree members');found[n]=sig(t)
     if stat.S_ISDIR(t.st_mode):pending.append(Path(e.path))
   except BaseException as error:primary=error;raise
   finally:_finish(() if it is None else (lambda:it.close(),),primary)
  old=self.trees.get(root);require(old is None or old==(tuple(exclude),found),'tree changed');self.trees[root]=(tuple(exclude),found);return found
 def finish(self):
  # All read descriptors and scandir iterators have closed before the final global join.
  for root,(exclude,_) in list(self.trees.items()):self.tree(root,exclude)
  for p in list(self.anchors):self.anchor(p)
  for p,s in self.pins.items():self.tick();require(sig(p.lstat())==s,'final whole-reader currentness')
  self.tick()
def manifest_rows(m):
 rows=m['members'];require(type(rows) is list and len(rows)<=LIMIT,'manifest rows');out={}
 for x in rows:
  n=safe(x['path']);require(n not in out,'duplicate manifest path');require(x['kind'] in ('file','directory'),'manifest kind');require(type(mode(x['mode'])) is int,'mode');out[n]=x
 return out

# Root-owned one-use metadata integration; no lifecycle or numerical execution.
import datetime,resource
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
FS=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
PREVIEW=FS/'financial-wrapper-compatibility-gate-preview02-2026-10-04'
OUT=FS/'financial-wrapper-compatibility-gate-root-adoption01-2026-10-04'
NEW='fixture_inputs/financial_wrapper_compatibility01'
OLD_GATE='fixture_inputs/financial_wrapper_claimedrun01/gates.json'
PREVIEW_PIN='b725fa4f1f6b071cf910eeb24edab11aaa20c9e50475fcda54dc5e1dcc15c0d2'
BASIS=FS/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/snapshot/COMPOSITION_BASIS01.json'
BASIS_PIN='297336727f249a6fd3f6861374fa74d243674522e7e791a85be11aa7198c8f45'
OLD_GATE_PIN='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c'
IDENTITY='financial-wrapper-classification-eager-complete100-compatibility-20261004-01'

def encode(v):return (json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def put(p,b):
 require(type(b) is bytes and len(b)<=FILE,'output extent')
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600);primary=None
 try:
  os.fchmod(fd,0o600);view=memoryview(b)
  while view:
   n=os.write(fd,view);require(n>0,'short write');view=view[n:]
  os.fsync(fd)
 except BaseException as error:primary=error;raise
 finally:_finish((lambda:os.close(fd),),primary)

def head(r):
 s=r.read(CAP/'.git/HEAD').decode().strip()
 return r.read(CAP/'.git'/safe(s[5:])).decode().strip() if s.startswith('ref: ') else s

def read_release(r,root,source_sha,pins):
 root=Path(root);require(root.is_absolute() and root.resolve(strict=True)==root,'canonical review')
 m=r.j(root/'MANIFEST01.json');rows={x['path']:x for x in m['members']};require(len(rows)==len(m['members']),'unique release members')
 machine=r.j(root/'MACHINE01.json');report=r.read(root/'REPORT01.md')
 for n in ('MACHINE01.json','REPORT01.md'):
  x=rows[n];b=r.read(root/n,x['sha256'],mode(x['mode']));require(x['kind']=='file' and len(b)==x['bytes'],'release seal')
 require(machine['report_sha256']==h(report),'release report')
 require(machine['decision']=='ACCEPTED_EXACT_ROOT_GATE_METADATA_ADOPTION_ONLY','release decision')
 require(machine['root_adopter_sha256']==source_sha and machine['preview_sha256']==PREVIEW_PIN and machine['composition_basis_sha256']==BASIS_PIN,'exact source binding')
 require(machine['allowed_new_file_pins']==pins and machine['root']==str(CAP) and machine['source_before']==SOURCE,'exact release scope')
 for k in ('numerical_authority','claim_authority','existing_body_mutation_allowed'):require(machine[k] is False,'no additional authority')
 return {'manifest':{'path':str(root/'MANIFEST01.json'),'sha256':h(r.read(root/'MANIFEST01.json'))},'machine':{'path':str(root/'MACHINE01.json'),'sha256':h(r.read(root/'MACHINE01.json'))},'report':{'path':str(root/'REPORT01.md'),'sha256':h(report)}}

def main(review_root):
 resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE));require(resource.getrlimit(resource.RLIMIT_FSIZE)==(FILE,FILE),'hard soft output cap')
 r=Reader();source_sha=h(r.read(Path(__file__).resolve()));preview=r.j(PREVIEW/'PREVIEW01.json',PREVIEW_PIN);basis=r.j(BASIS,BASIS_PIN)
 require(preview['status']=='CONCRETE_GATE_PREVIEW_NOT_ADOPTED' and preview['source_before']==SOURCE and preview['root']==str(CAP),'exact preview')
 require(preview['identity']==IDENTITY and preview['parent'] is None and preview['roles']==11 and preview['source_pins']==354 and preview['prospective_tracked']==355,'identity roles pins')
 require(preview['actual_highest']==19 and preview['actual_spent_failed']==3 and preview['prospective_amendment']==20 and preview['old_experiments_preserved']==12,'cumulative history')
 pins=preview['new_file_pins'];require(len(pins)==15 and all(str(Path(safe(n)).parent)==NEW for n in pins),'exact15 destinations')
 release=read_release(r,review_root,source_sha,pins)
 require(not os.path.lexists(OUT) and not os.path.lexists(CAP/NEW) and not os.path.lexists(CAP/'research_runs'/IDENTITY),'one-use fresh namespaces')
 require(head(r)==SOURCE,'current source HEAD')
 oldrows=manifest_rows(basis['current589_manifest']);require(len(oldrows)==589,'whole589 basis')
 require(stat.S_IMODE(CAP.lstat().st_mode)==basis['current589_manifest']['root_mode'],'capsule original root mode')
 before=r.tree(CAP,('.git',));require(set(before)==set(oldrows),'whole589 current namespace')
 for n,x in oldrows.items():
  s=(CAP/n).lstat();require(stat.S_IMODE(s.st_mode)==mode(x['mode']) and s.st_uid==os.getuid(),'original mode/owner')
  if x['kind']=='file':require(len(r.read(CAP/n,x['sha256']))==x['bytes'],'whole original body')
  else:require(stat.S_ISDIR(s.st_mode),'original directory')
 files={n:r.read(PREVIEW/n,pin) for n,pin in sorted(pins.items())}
 newgate=decode(files[NEW+'/gates.json']);oldgate=r.j(CAP/OLD_GATE,OLD_GATE_PIN)
 require(set(newgate['experiments'])==set(oldgate['experiments'])|{IDENTITY} and len(oldgate['experiments'])==12,'12 preserved definitions')
 require(all(newgate['experiments'][n]==x for n,x in oldgate['experiments'].items()),'all original experiments identical')
 require({k:v for k,v in newgate.items() if k!='experiments'}=={k:v for k,v in oldgate.items() if k!='experiments'},'unchanged program/families/header')
 experiment=newgate['experiments'][IDENTITY];require(experiment['parent'] is None and len(experiment['inputs'])==11 and len(experiment['source_files'])==354,'new exact experiment')
 for n,pin in experiment['source_files'].items():require(h(files[n] if n in files else r.read(CAP/safe(n)))==pin,'all354 source pins')
 for x in preview['actual_history']:
  d=CAP/'research_runs'/x['identity'];require(not os.path.lexists(d/'complete.json'),'failed stays failed')
  r.read(d/'claim.json',x['claim_sha256']);r.read(d/'failed.json',x['failed_sha256'])
 require(set(x.name for x in (CAP/'research_runs').iterdir())=={x['identity'] for x in preview['actual_history']}|{'.lock'},'exact original history namespace')
 require(os.statvfs(CAP).f_bavail*os.statvfs(CAP).f_frsize>=10*1024**3,'10GiB disk floor')
 r.finish()
 OUT.mkdir(mode=0o700);os.chmod(OUT,0o700)
 intent={'schema_version':1,'status':'ONE_USE_METADATA_ADOPTION_RESERVED','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(CAP),'source_before':SOURCE,'root_adopter_sha256':source_sha,'preview_sha256':PREVIEW_PIN,'new_file_pins':pins,'review':release,'numerical_or_claim_started':False,'budget_spent_before':19,'actual_failed_before':3}
 put(OUT/'INTENT01.json',encode(intent))
 (CAP/NEW).mkdir(mode=0o700)
 for n,b in files.items():put(CAP/n,b)
 # Finite terminal verification after every output descriptor is closed.
 after=Reader();actual=after.tree(CAP,('.git',));require(set(actual)==set(oldrows)|set(files)|{NEW},'only15files plus new directory')
 require(stat.S_IMODE((CAP/NEW).lstat().st_mode)==0o700,'new private input directory')
 for n,x in oldrows.items():
  s=(CAP/n).lstat();require(stat.S_IMODE(s.st_mode)==mode(x['mode']) and s.st_uid==os.getuid(),'old mode/owner preserved')
  if x['kind']=='file':
   require(sig(s)==before[n],'old full regular-file signature preserved');require(len(after.read(CAP/n,x['sha256']))==x['bytes'],'old complete body preserved')
  else:require((s.st_dev,s.st_ino,s.st_uid)==(before[n][0],before[n][1],before[n][8]),'old directory identity preserved')
 for n,b in files.items():require(after.read(CAP/n,pins[n],0o600)==b,'new exact body')
 require(head(after)==SOURCE and after.read(CAP/OLD_GATE,OLD_GATE_PIN)==r.read(CAP/OLD_GATE),'source HEAD/oldgate preserved')
 after.finish();require(os.statvfs(CAP).f_bavail*os.statvfs(CAP).f_frsize>=10*1024**3,'remaining10GiB disk floor')
 put(OUT/'INSTALLED_NOT_COMMITTED01.json',encode({**intent,'status':'EXACT_GATE_INPUTS_INSTALLED_NOT_COMMITTED_NOT_ADMITTED_NOT_NUMERICALLY_RELEASED','whole_before':589,'whole_after':605,'old_body_metadata_preserved':True,'old_definitions_preserved':12,'new_files':15,'prospective_tracked':355,'source_pins':354,'roles':11,'actual_highest_spent_allowance':19,'prospective_registered_amendment':20,'Admission_or_Run_started':False,'paper_budget_changed':False,'excluded':['Git commit/adoption verification','genuine Admission','final writable caller recovery','native eligibility','numerical execution','POSIX reconstruction','whole fit capacity']}))
 print(json.dumps({'status':'EXACT_GATE_INPUTS_INSTALLED_NOT_COMMITTED_NOT_ADMITTED_NOT_NUMERICALLY_RELEASED','new_files':15,'whole_after':605}))

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--review-root',required=True);q=a.parse_args();main(q.review_root)
