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
DEST=FS/'financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04'
PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
CURRENT='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
def enc(x):return (json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def put(p,b):
 require(len(b)<=FILE,'snapshot file cap');p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 with IO._opened(p,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def git(*a,input=None):
 p=subprocess.run(['git',*a],cwd=CAP,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)
 require(len(p.stdout)<=FILE and len(p.stderr)<=65536,'bounded Git pipe');return p.stdout

def main():
 resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE));require(not os.path.lexists(DEST),'fresh capture')
 r=Reader();require(git('rev-parse','HEAD').decode().strip()==CURRENT and not git('status','--porcelain','--untracked-files=no'),'actual frozen source')
 actual=r.tree(CAP,('.git',));require(len(actual)==605,'whole605');master={'schema_version':1,'root_mode':stat.S_IMODE(CAP.lstat().st_mode),'members':[]}
 for n in sorted(actual):
  s=(CAP/n).lstat();x={'path':n,'mode':stat.S_IMODE(s.st_mode),'kind':'directory' if stat.S_ISDIR(s.st_mode) else 'file'}
  if x['kind']=='file':body=r.read(CAP/n);x.update(bytes=len(body),sha256=h(body))
  master['members'].append(x)
 preview=r.j(FS/'financial-wrapper-compatibility-gate-preview02-2026-10-04/PREVIEW01.json','b725fa4f1f6b071cf910eeb24edab11aaa20c9e50475fcda54dc5e1dcc15c0d2')
 payload={};origins={}
 for n,pin in sorted(preview['new_file_pins'].items()):
  q='source-inputs/'+n;payload[q]=r.read(CAP/n,pin);origins[q]={'origin':str(CAP/n),'original_mode':stat.S_IMODE((CAP/n).lstat().st_mode),'sha256':pin,'bytes':len(payload[q])}
 oldindex=r.j(FS/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/snapshot/SOURCE_GIT394_METADATA01.json');old={x['oid']:x for x in oldindex['objects']}
 oids=sorted({line.split()[0].decode() for line in git('rev-list','--objects',CURRENT).splitlines()});require(len(oids)==407 and set(old)<=set(oids),'394 original407 current')
 index=[];new=[]
 for line in git('cat-file','--batch-check',input=('\n'.join(oids)+'\n').encode()).splitlines():
  oid,kind,size=line.decode().split();size=int(size);require(oid in oids and 0<=size<=FILE and kind in ('blob','tree','commit','tag'),'logical Git extent/type')
  if oid in old:
   require(kind==old[oid]['type'] and size==old[oid]['bytes'],'old Git unchanged');row=dict(old[oid]);row['body_basis']='accepted-original394-composition'
  else:
   body=git('cat-file',kind,oid);require(len(body)==size and hashlib.sha1(kind.encode()+b' '+str(size).encode()+b'\0'+body).hexdigest()==oid,'new logical Git framing')
   name='git-delta/'+oid+'.body';payload[name]=body;new.append(oid);row={'oid':oid,'type':kind,'bytes':size,'sha256':h(body),'body_basis':name}
  index.append(row)
 require(len(new)==13 and len(index)==407,'13new407')
 parenttree=r.tree(PARENT);require(len(parenttree)==10 and all(stat.S_ISREG((PARENT/n).lstat().st_mode) for n in parenttree),'complete10 Parent source files')
 for n in sorted(parenttree):
  body=r.read(PARENT/n);payload['parent/'+n]=body;origins['parent/'+n]={'origin':str(PARENT/n),'original_mode':stat.S_IMODE((PARENT/n).lstat().st_mode),'sha256':h(body),'bytes':len(body)}
 require(h(payload['parent/parent01.py'])=='424f13b653d970efc4994e76e27f4ff5e8cf732133daab6a956cb1a034299ea0','actual source-accepted caller')
 refs=[]
 for name,pins in [('financial-wrapper-compatibility-postcommit-admission-review01-2026-10-04',{'MACHINE01.json':'62b5fa80f2a0a1275398156194daef3b809bb983966077f30b669e403be60874','MANIFEST01.json':'da5de0fa5f5956149abd05c73b8e5b7525ea5ada2c1e44ae6514486c1d1b63da','REPORT01.md':'4e3ea04fa80c1c2d01468406717f48c8d7b46a77df3a19dff8c8f305592b95be'}),('financial-wrapper-compatibility-parent-source-review01-2026-10-04',{'MACHINE01.json':'faaad64cfe9931f64f45fea7eb364fdf2e6219082ad2de8aea69b0ccde3b8dbc','MANIFEST01.json':'dc43830ad8fe17741bc85df2a6ed19da38cb3902c6685f2dce6258b0ef2de3e9','REPORT01.md':'96ba781dab08b7dc4074e536576ec1ca7ea541c74e99ac9d05198affe5626a46'})]:
  for n,pin in pins.items():
   path=FS/name/n;body=r.read(path,pin);q='reviews/'+name+'/'+n;payload[q]=body;origins[q]={'origin':str(path),'original_mode':stat.S_IMODE(path.lstat().st_mode),'sha256':pin,'bytes':len(body)};refs.append({'path':str(path),'sha256':pin})
 payload['CAPSULE_MASTER605.json']=enc(master);payload['SOURCE_GIT407_METADATA01.json']=enc({'schema_version':1,'source':CURRENT,'old_original394_basis':SOURCE,'objects':index});payload['ORIGINAL_ORIGINS01.json']=enc(origins)
 r.finish();require(git('rev-parse','HEAD').decode().strip()==CURRENT,'source terminal unchanged');require(os.statvfs(CAP).f_bavail*os.statvfs(CAP).f_frsize>=10*1024**3,'disk floor')
 # No release or accepted recovery is emitted by local capture.
 DEST.mkdir(mode=0o700);snapshot=DEST/'snapshot';snapshot.mkdir(mode=0o700)
 for n,b in payload.items():put(snapshot/n,b)
 rows=[]
 for n in sorted(payload):
  parts=Path(n).parts
  for i in range(1,len(parts)):
   name='/'.join(parts[:i])
   if not any(x['path']==name for x in rows):rows.append({'path':name,'kind':'directory','mode':0o700})
  rows.append({'path':n,'kind':'file','mode':0o600,'bytes':len(payload[n]),'sha256':h(payload[n])})
 rows.sort(key=lambda x:x['path']);manifest={'schema_version':1,'root_mode':0o700,'members':rows};manifestraw=enc(manifest);put(DEST/'MANIFEST01.json',manifestraw)
 tar=io.BytesIO()
 with tarfile.open(fileobj=tar,mode='w',format=tarfile.USTAR_FORMAT) as t:
  for x in rows:
   info=tarfile.TarInfo(x['path']+('/' if x['kind']=='directory' else ''));info.mode=x['mode'];info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
   if x['kind']=='directory':info.type=tarfile.DIRTYPE;t.addfile(info)
   else:info.size=x['bytes'];t.addfile(info,io.BytesIO(payload[x['path']]))
 archive=gzip.compress(tar.getvalue(),mtime=0);require(len(archive)<=FILE,'archive4MiB');put(DEST/'source-parent-delta03.tar.gz',archive)
 # Fresh output byte/type/mode membership check; source stays read-only.
 v=Reader();output=v.tree(snapshot);require(set(output)=={x['path'] for x in rows},'complete output namespace')
 for x in rows:
  s=(snapshot/x['path']).lstat();require(stat.S_IMODE(s.st_mode)==x['mode'],'output mode')
  if x['kind']=='file':require(v.read(snapshot/x['path'],x['sha256'])==payload[x['path']],'exact snapshot copy')
 v.finish();r.finish();require(git('rev-parse','HEAD').decode().strip()==CURRENT,'capture terminal source')
 receipt={'schema_version':1,'status':'FROZEN_SOURCE_PARENT_DELTA_NOT_EXTERNAL_RECOVERY_NOT_RELEASE','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_design':CURRENT,'whole_current_capsule605':605,'original394_retained':394,'full_logical_git407':407,'new_logical_git13':13,'new_source_inputs15':15,'complete_draft_parent_files':10,'master605_sha256':h(payload['CAPSULE_MASTER605.json']),'manifest_sha256':h(manifestraw),'archive_sha256':h(archive),'archive_bytes':len(archive),'payload_files':len(payload),'payload_bytes':sum(map(len,payload.values())),'source_parent_review_refs':refs,'old_full605_body_basis':'accepted full589/585 composition c5cf plus exact15new source inputs; current605 whole master hashes retained','actual_external_recovery':None,'full_final_contract_release_proofs_not_present':True,'installed_runtime_package_bodies':False,'numerical_job_or_claim_started':False,'excluded':['final request/release','future source-runtime proof/external refs','future full-recovery proof','coalesced evidence successor','installed runtime package bodies','POSIX reconstruction','unrelated empirical stores','whole capacity','numerical release']}
 put(DEST/'CAPTURE01.json',enc(receipt));print(json.dumps({'status':receipt['status'],'manifest_sha256':h(manifestraw),'capture_sha256':h(enc(receipt)),'archive_sha256':h(archive),'archive_bytes':len(archive),'files':len(payload)}))
if __name__=='__main__':main()
