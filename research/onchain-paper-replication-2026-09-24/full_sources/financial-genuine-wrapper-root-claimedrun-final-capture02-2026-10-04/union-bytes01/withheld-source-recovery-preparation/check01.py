import hashlib,json,zlib,ast,sys
from pathlib import Path
import restore01 as S
from git_objects01 import tree_join
H=Path(__file__).resolve().parent;checks=[]
def ok(v,n):assert v,n;checks.append(n)
def refuse(f,n):
 try:f()
 except (ValueError,KeyError):checks.append(n)
 else:raise AssertionError(n)
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_bytes());refuse(lambda:S.validate_request(q),'no release')
source={}
def obj(kind,value):
 b=kind.encode()+b' '+str(len(value)).encode()+b'\0'+value;oid=hashlib.sha1(b).hexdigest();source['.git/objects/'+oid[:2]+'/'+oid[2:]]=zlib.compress(b);return oid
payload=b'opaque original body';blob=obj('blob',payload);tree=obj('tree',b'100644 body\0'+bytes.fromhex(blob));commit=obj('commit',b'tree '+tree.encode()+b'\n\nowned synthetic opaque object\n');source['body']=payload
ok(tree_join(source.__getitem__,set(source),commit,1)=={'body':('100644',blob)},'actual opaque commit/tree/blob')
for name in source:
 changed=dict(source);changed[name]=changed[name]+b'bad'
 refuse(lambda:tree_join(changed.__getitem__,set(changed),commit,1),'corrupt '+name)
for name in ('.git/objects/info/alternates','.git/info/grafts','.git/shallow','.git/refs/replace/x','.git/objects/pack/x'):
 refuse(lambda:tree_join(source.__getitem__,set(source)|{name},commit,1),'forbidden '+name)
refuse(lambda:tree_join(source.__getitem__,set(source),commit,2),'wrong count')
# Real tiny opaque complete-tree canonical archive/flat pipeline; no real capture restore.
root=H/'owned-source';root.mkdir();(root/'body').write_bytes(payload);m=S.R.scan(root);info=S.R.pack(root,m,H/'owned.tar.gz');flat=H/'owned-flat';S.reserve(flat);result=S.R.restore(H/'owned.tar.gz',info,m,flat)
meta=json.loads(S.R.read(flat,result['metadata_file']));ok(S.R.read(flat,meta['flat_members']['body'])==payload,'real owned R4 full recovery');refuse(lambda:S.reserve(flat),'exclusive destination')
for n,pin in S.PINS.items():ok(S.R.digest(S.R.read(H,n))==pin,'exact helper '+n)
cap=H.parent/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';body={n:S.R.read(cap,n) for n in S.EXPECTED}
for n,pin in S.EXPECTED.items():ok(S.R.digest(body[n])==pin['sha256'] and len(body[n])==pin['bytes'],'actual opaque capture pin '+n)
m,a,t=S.joins(body);ok(len(m['members'])==1029,'actual metadata join only')
for n in ('CAPTURE01.json','source-manifest.json'):
 changed=dict(body);v=json.loads(changed[n]);v['status']='bad' if n=='CAPTURE01.json' else v.get('status');
 if n=='source-manifest.json':v['members']=v['members'][:-1]
 changed[n]=S.R.encode(v);refuse(lambda:S.joins(changed),'changed metadata '+n)
for firsttype in (ValueError,MemoryError,KeyboardInterrupt):
 for secondtype in (OSError,MemoryError,KeyboardInterrupt):
  first=firsttype('primary');second=secondtype('cleanup');done=[]
  def fail():done.append(1);raise second
  try:
   try:raise first
   finally:S.R._cleanup((fail,lambda:done.append(2)))
  except BaseException as e:ok(e is first if firsttype in (MemoryError,KeyboardInterrupt) else e is second if secondtype in (MemoryError,KeyboardInterrupt) else isinstance(e,BaseException),'firstfatal pair')
  ok(done==[1,2],'all cleanup')
ok(not any(n in sys.modules for n in ('torch','numpy','pandas')),'no numeric imports')
(H/'CHECKS01.json').write_bytes(S.R.encode({'count':len(checks),'checks':checks,'actual_capture_restores':0,'claims':0}));print(len(checks))
