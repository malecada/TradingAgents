import gzip,io,json,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import recovery_pax01 as R
checks=[]
def refuse(fn,n):
 try:fn()
 except (ValueError,TypeError,KeyError,tarfile.TarError,OSError,EOFError):checks.append(n)
 else:raise AssertionError(n)
def encode(items):
 b=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',mtime=0,fileobj=b) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as t:
   for info,body in items:t.addfile(info,io.BytesIO(body))
 return b.getvalue()
raw=(H/'tiny.tar.gz').read_bytes();frames=list(R.framed_members(raw));m=R.scan(H/'tiny')
def items():
 a=[]
 for name,t,b in frames:
  x=tarfile.TarInfo(name);x.mode=t.mode;x.size=t.size;x.type=t.type;a.append((x,b))
 return a
for label in ('order','mode','PAX-directory-vs-file','duplicate'):
 a=items()
 if label=='order':a.reverse()
 elif label=='mode':a[-1][0].mode^=1
 elif label=='PAX-directory-vs-file':a[-1][0].type=tarfile.DIRTYPE;a[-1][0].size=0;a[-1]=(a[-1][0],b'')
 else:a.append(a[-1])
 b=encode(a);p=H/(label+'.gz');p.write_bytes(b);out=H/('extra-refusal-'+label);out.mkdir(mode=0o700);info={'bytes':len(b),'sha256':R.digest(b),'manifest_sha256':R.digest(R.encode(m))};refuse(lambda:R.restore(p,info,m,out),label)
# Header-only declared oversize must refuse before trying to allocate/read that payload.
t=tarfile.TarInfo('file');t.size=R.FILE+1;t.mode=384;blob=t.tobuf(format=tarfile.PAX_FORMAT)+bytes(1024);refuse(lambda:list(R.framed_members(gzip.compress(blob,mtime=0))),'perfile bound before payload')
# Actual raw truncated slash headers, without touching original compressed bodies.
root=H.parent/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04';observed=[]
for num in (35,49):
 plain=gzip.decompress(R.read(root,'shards/shard-%04d.tar.gz'%num));offset=0;pending=False
 while any(plain[offset:offset+512]):
  head=plain[offset:offset+512];t=tarfile.TarInfo.frombuf(head,'utf-8','strict');offset+=512;name=head[:100].split(b'\0',1)[0]
  if pending and t.type==tarfile.REGTYPE and name.endswith(b'/'):observed.append({'shard':num,'raw_prefix':name.decode(),'raw_type':'REGTYPE'})
  pending=t.type==tarfile.XHDTYPE;offset+=((t.size+511)//512)*512
assert len(observed)==9;checks.append('nine genuine canonical truncated slash headers')
(H/'EXTRA_CHECKS01.json').write_text(json.dumps({'checks':checks,'actual_headers':observed,'actual_restore':False},indent=2)+'\n');print(len(checks))
