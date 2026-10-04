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


import subprocess,datetime,resource
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');FS=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
DEST=FS/'financial-wrapper-compatibility-preclaim-baseline-capture01-2026-10-05';CURRENT='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
PARENT=ROOT.parent/'onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01'
SCOPES={
 'delta04':FS/'financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04',
 'failed03':FS/'financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04',
 'coalesced':FS/'financial-wrapper-compatibility-coalesced-evidence-root03-2026-10-04',
 'coalesced-review':FS/'financial-wrapper-compatibility-coalesced-evidence-outcome-review04-2026-10-04',
 'postinstall':FS/'financial-wrapper-compatibility-coalesced-postinstall-review04-2026-10-04',
 'bridge':FS/'financial-wrapper-compatibility-final-source-runtime-bridge02-2026-10-04',
 'capture-review':FS/'financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04',
 'root-copy':FS/'financial-wrapper-compatibility-coalesced-evidence-root-launch04-2026-10-04',
}
PINS={
 'bridge/SOURCE_INPUT_RUNTIME_PROOF01.json':'ac1ed8a157d7ec113ebe1a8e2eb71a917f46572d0cc8b035c1ee850d9b10730c',
 'bridge/MANIFEST01.json':'e581f20cb295639283e33ca7bdbe9da811baa4eb14637a656d816eb5ddfe3f1b',
 'postinstall/MANIFEST01.json':'7e82b8c9b70e6dd2582282443894c479d30f965ed0b004395b9ec5d206b3a016',
 'coalesced-review/MANIFEST01.json':'2eb451cc119963749bc6ac3a2edaf089590b900de810625a888216bfe3f14b95',
 'capture-review/MANIFEST01.json':'4a21d4a7853e8386e72b700bca5243415caef1d4c0914c008547977e835ded84',
 'coalesced/MANIFEST01.json':'f6326fbf10f76c378f4070d7be91c2c4013d58dc2a0c64ca7e0da11cade56d6d',
 'delta04/MANIFEST01.json':'49df5d5e80f307948b32bb6a3eb1a2234f8bbd8ffb2c5592700b69828caaa913',
 'delta04/source-parent-delta04.tar.gz':'d90353cb0d72df5fca6ed2479f2ea6b28400a9dcdc6bc1143a8973665ca1d8b1',
 'failed03/FAILED_LOCAL_CAPTURE01.json':'07838977e0d6ec5e2e88c35cdd860d8c478c581ba09ccc9772470b5a618829d0',
}
ROOT_FILES=['COALESCED_CANDIDATES_INSTALL04_INTENT01.json','COALESCED_CANDIDATES_INSTALL04_OBSERVED01.json','COALESCED_CANDIDATES_INSTALL04_ACTUAL_TOOL_EXIT01.json']
def enc(x):return (json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def put(p,b):
 require(len(b)<=FILE and p.is_relative_to(DEST),'owned individual file');q=DEST
 for part in p.parent.relative_to(DEST).parts:
  q=q/part
  if not os.path.lexists(q):q.mkdir(mode=0o700)
  s=q.lstat();require(stat.S_ISDIR(s.st_mode)and stat.S_IMODE(s.st_mode)==0o700 and s.st_uid==os.getuid(),'owned private output')
 with IO._opened(p,'xb')as f:require(f.write(b)==len(b),'complete snapshot write');f.flush();os.fsync(f.fileno())
def git(*a):
 p=subprocess.run(['git',*a],cwd=CAP,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True);require(len(p.stdout)<=FILE and len(p.stderr)<=65536,'bounded metadata Git');return p.stdout
def main():
 resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE));require(not os.path.lexists(DEST),'fresh baseline capture');r=Reader()
 require(git('rev-parse','HEAD').decode().strip()==CURRENT and not git('status','--porcelain','--untracked-files=no'),'actual committed frozenCAP')
 oldmaster=r.j(SCOPES['delta04']/'snapshot/CAPSULE_MASTER605.json');actual=r.tree(CAP,('.git',));require(len(actual)==605 and set(actual)=={x['path']for x in oldmaster['members']},'exactfull605current')
 for row in oldmaster['members']:
  p=CAP/row['path'];require(stat.S_IMODE(p.lstat().st_mode)==row['mode'],'unchangedoriginalCAPmode')
  if row['kind']=='file':require(len(r.read(p,row['sha256']))==row['bytes'],'all605bodybasiscurrent')
 require(len({x.split()[0]for x in git('rev-list','--objects',CURRENT).splitlines()})==407,'actual407Gitmetadata')
 require(h(r.read(PARENT/'parent01.py'))=='424f13b653d970efc4994e76e27f4ff5e8cf732133daab6a956cb1a034299ea0','sameacceptedParent')
 require(h(r.read(PARENT/'REQUEST_DRAFT01.json'))=='e7579251741a865a2955917a3a9dc346ed6710ffc08388f1907c727e95d0a721','sameunreleaseddraft')
 require(not os.path.lexists(PARENT/'REQUEST_FINAL01.json')and not os.path.lexists(PARENT/'attempt'),'baselineexcludesfuturefinalbody')
 payload={};origins=[];scope_metadata={}
 for alias,root in sorted(SCOPES.items()):
  tree=r.tree(root);require(len(tree)<=4096,'boundedclosedscope');scope_metadata[alias]={'root':str(root),'original_root_mode':stat.S_IMODE(root.lstat().st_mode),'members':[]}
  for n in sorted(tree):
   p=root/n;s=p.lstat();row={'path':n,'kind':'directory'if stat.S_ISDIR(s.st_mode)else'file','mode':stat.S_IMODE(s.st_mode)}
   if row['kind']=='file':
    b=r.read(p,PINS.get(alias+'/'+n));payload[alias+'/'+n]=b;row.update(bytes=len(b),sha256=h(b));origins.append({'archive_path':alias+'/'+n,'original_path':str(p),'original_mode':row['mode'],'bytes':len(b),'sha256':h(b)})
   scope_metadata[alias]['members'].append(row)
 for n in ROOT_FILES:
  p=FS/'heartbeat-root-checkpoint10-2026-10-04'/n;b=r.read(p);payload['root-install/'+n]=b;origins.append({'archive_path':'root-install/'+n,'original_path':str(p),'original_mode':stat.S_IMODE(p.lstat().st_mode),'bytes':len(b),'sha256':h(b)})
 payload['ORIGINAL_SCOPES01.json']=enc(scope_metadata);payload['ORIGINAL_ORIGINS01.json']=enc(origins)
 require(sum(map(len,payload.values()))<=32*1024**2,'finite32MiBpayload');r.finish();require(os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize>=10*1024**3+64*1024**2,'floorplusconservativecaptureheadroom')
 rows={}
 for n,b in sorted(payload.items()):
  parts=Path(n).parts
  for i in range(1,len(parts)):rows['/'.join(parts[:i])]={'path':'/'.join(parts[:i]),'kind':'directory','mode':0o700}
  rows[n]={'path':n,'kind':'file','mode':0o600,'bytes':len(b),'sha256':h(b)}
 rows=[rows[n]for n in sorted(rows)];manifest={'schema_version':1,'root_mode':0o700,'members':rows};mr=enc(manifest)
 tar=io.BytesIO()
 with tarfile.open(fileobj=tar,mode='w',format=tarfile.USTAR_FORMAT)as t:
  for row in rows:
   info=tarfile.TarInfo(row['path']+('/'if row['kind']=='directory'else''));info.mode=row['mode'];info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
   if row['kind']=='directory':info.type=tarfile.DIRTYPE;t.addfile(info)
   else:info.size=row['bytes'];t.addfile(info,io.BytesIO(payload[row['path']]))
 archive=gzip.compress(tar.getvalue(),mtime=0);require(len(archive)<=FILE,'canonicalarchiveindividual4MiB');r.finish()
 DEST.mkdir(mode=0o700);snapshot=DEST/'snapshot';snapshot.mkdir(mode=0o700)
 for n,b in sorted(payload.items()):put(snapshot/n,b)
 put(DEST/'MANIFEST01.json',mr);put(DEST/'baseline01.tar.gz',archive)
 v=Reader();tree=v.tree(snapshot);require(set(tree)=={x['path']for x in rows},'actualcompletesnapshotnamespace')
 for row in rows:
  p=snapshot/row['path'];require(stat.S_IMODE(p.lstat().st_mode)==row['mode'],'actualsavedmode')
  if row['kind']=='file':require(v.read(p,row['sha256'])==payload[row['path']],'savedliteralbody')
 v.finish();r.finish();require(git('rev-parse','HEAD').decode().strip()==CURRENT,'terminalsourceunchanged')
 capture={'schema_version':1,'status':'FROZEN_BASELINE_LOCAL_BYTES_NOT_EXTERNAL_RECOVERY_NOT_FINAL_RELEASE','round':'BASELINE','source':CURRENT,'complete_current605_bodybasis':True,'logicalGit407_basis':'acceptedoriginal394plus13actualdelta04','original589_basis':'actualacceptedc5cf38d2BYTErecoveryplus15newCAPinputsandnewdirectory','parent_draft_files':10,'scopes':{k:str(p)for k,p in SCOPES.items()},'scope_count':len(SCOPES),'payload_files':len(payload),'payload_bytes':sum(map(len,payload.values())),'typed_members':len(rows),'manifest_sha256':h(mr),'archive_sha256':h(archive),'archive_bytes':len(archive),'origins_sha256':h(payload['ORIGINAL_ORIGINS01.json']),'original_scopes_sha256':h(payload['ORIGINAL_SCOPES01.json']),'full_recovery_proof':None,'final_request':None,'final_release':None,'actual_external_recovery':None,'numerical_authority':False,'installed_runtime_bodies':False,'POSIX_reconstruction':False,'qualification':'ordinary byte-preserving consolidated baseline; original modes inmetadata; futurefinalcaller/proofs needseparatesupplement; source/inodejoins aresampled, notcontinuouswriterexclusion'}
 put(DEST/'CAPTURE01.json',enc(capture));print(json.dumps({'status':capture['status'],'manifest_sha256':h(mr),'capture_sha256':h(enc(capture)),'archive_sha256':h(archive),'archive_bytes':len(archive),'payload_files':len(payload),'typed_members':len(rows)}))
if __name__=='__main__':main()
