from pathlib import Path
import ast,copy,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile,traceback
from unittest.mock import patch
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-final-recovery-preparation04-2026-10-03';OLD=R.parent/'held-consumer-final-recovery-preparation03-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes())
assert H((A/'MANIFEST04.json').read_bytes())=='7764229f794d10aa61b999c311e9ddfe69f11f3938b83c57b4e959ad9a69f54d'
man=J(A/'MANIFEST04.json');rows=man['members'];assert len(rows)==343;names=[]
for r in rows:
 p=A/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode'];k=r['kind'];names.append(r['path'])
 if k=='file':assert stat.S_ISREG(s.st_mode) and s.st_nlink==r['nlink'] and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256']
 elif k=='directory':assert stat.S_ISDIR(s.st_mode)
 elif k=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
 elif k=='fifo':assert stat.S_ISFIFO(s.st_mode)
 else:raise AssertionError(k)
actual=[]
for p,ds,fs in os.walk(A,followlinks=False):
 for n in ds+fs:
  rel=(Path(p)/n).relative_to(A).as_posix()
  if rel not in ('MANIFEST04.json','MANIFEST04.sha256'):actual.append(rel)
assert sorted(actual)==sorted(names)
new=(A/'recovery04.py').read_bytes();old=(OLD/'recovery03.py').read_bytes();assert H(new)=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a';assert H(old)=='785b957f93e22b18b1d3c00a73cacc75b6028bab9566d737b40903dcffc4964e'
oldtree=ast.parse(old);newtree=ast.parse(new);before={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};after={n.name:n for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};assert set(before)==set(after)
for name in before:
 if name!='framed_members':assert ast.dump(before[name])==ast.dump(after[name])
inverse=copy.deepcopy(newtree)
for i,n in enumerate(inverse.body):
 if isinstance(n,ast.FunctionDef) and n.name=='framed_members':inverse.body[i]=copy.deepcopy(before[n.name])
assert ast.dump(inverse)==ast.dump(oldtree)
def without_frame(raw):
 t=ast.parse(raw);n=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='framed_members');lines=raw.splitlines(keepends=True);return b''.join(lines[:n.lineno-1]+lines[n.end_lineno:])
assert without_frame(new)==without_frame(old)
for name in ('owned_io.py','bounded_git01.py','REQUEST_TEMPLATE01.json'):assert (A/name).read_bytes()==(OLD/name).read_bytes()
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
m=load(A/'recovery04.py','independent_recovery04');oldm=load(OLD/'recovery03.py','independent_old03')
assert (m.FILE,m.BASE,m.INFLATED,m.PAX,m.FLOOR)==(4194304,134217728,201326592,8192,10737418240)
# Reviewer-owned tiny raw archives preserve deliberately malformed raw syntax.
def header(name,kind,size=0):
 t=tarfile.TarInfo('placeholder');t.type=kind;t.size=size;h=bytearray(t.tobuf(format=tarfile.USTAR_FORMAT));b=name.encode();assert len(b)<=100;h[:100]=b+bytes(100-len(b));h[156:157]=kind;h[148:156]=b'        ';h[148:156]=('%06o\0 '%sum(h)).encode();return bytes(h)
def arc(name,kind=tarfile.DIRTYPE,pax=False,body=b'',rawname='entry'):
 parts=[]
 if pax:
  value=('path='+name+'\n').encode();n=len(value)+3
  while n!=len(str(n))+1+len(value):n=len(str(n))+1+len(value)
  payload=str(n).encode()+b' '+value;parts+=[header('././@PaxHeader',tarfile.XHDTYPE,len(payload)),payload,bytes((-len(payload))%512)]
 parts+=[header(rawname if pax else name,kind,len(body)),body,bytes((-len(body))%512),bytes(1024)]
 return gzip.compress(b''.join(parts),mtime=0)
cases=[]
def refusal(label,raw):
 (R/(label+'.gz')).write_bytes(raw)
 try:list(m.framed_members(raw))
 except ValueError:cases.append(label)
 else:raise AssertionError(label+' accepted')
for i,name in enumerate(('','/','//','./','../','a//','a/../','a/./','a//b/','/a/','a\\b/','a\0b/','.env/','keys/a/','a/'+'b'*2048+'/')):refusal('pax-invalid-'+str(i),arc(name,pax=True))
for i,kind in enumerate((tarfile.REGTYPE,tarfile.AREGTYPE)):
 refusal('pax-regular-slash-'+str(i),arc('a/',kind,pax=True));refusal('raw-regular-slash-'+str(i),arc('a/',kind))
for i,name in enumerate(('a//','/','a/../','a//b/')):refusal('raw-directory-'+str(i),arc(name))
for i,kind in enumerate((tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.GNUTYPE_LONGNAME,tarfile.GNUTYPE_SPARSE)):
 refusal('unknown-type-'+str(i),arc('a/',kind,pax=True))
for name,pax in [('a/',False),('a/',True),('é'*70+'/',True)]:
 result=list(m.framed_members(arc(name,pax=pax)));assert len(result)==1 and result[0][0]==name[:-1] and result[0][1].type==tarfile.DIRTYPE and result[0][2]==b''
# Bound precedes PAX payload reads; bad ordinary slash precedes ordinary body read.
realread=gzip.GzipFile.read;calls=[]
def traced(obj,n):calls.append(n);return realread(obj,n)
bomb=gzip.compress(header('././@PaxHeader',tarfile.XHDTYPE,8193),mtime=0)
with patch.object(gzip.GzipFile,'read',traced):refusal('oversized-pax',bomb)
assert calls==[512]
calls=[]
with patch.object(gzip.GzipFile,'read',traced):refusal('regular-refuse-before-payload',arc('a/',tarfile.REGTYPE,body=b'opaque'))
assert calls==[512]
# Actual old decoder refuses canonical long directory; exact exception retained.
long='d'*110;raw=arc(long+'/',pax=True);(R/'old-red-long-directory.gz').write_bytes(raw)
try:list(oldm.framed_members(raw))
except ValueError as e:assert str(e)=='unsafe member path';(R/'OLD_RED04.log').write_text(traceback.format_exc())
else:raise AssertionError('old failure absent')
assert list(m.framed_members(raw))[0][0]==long
# First actual fatal survives gzip close error; each acquired gzip closed once.
first=MemoryError('read first');realclose=gzip.GzipFile.close;closed=[]
def later(obj):closed.append(id(obj));realclose(obj);raise OSError('after close')
with patch.object(gzip.GzipFile,'read',side_effect=first),patch.object(gzip.GzipFile,'close',later):
 try:list(m.framed_members(raw))
 except BaseException as e:assert e is first
 else:raise AssertionError('firstfatal absent')
assert len(closed)==len(set(closed))==1
# Read-only actual fetched archives: stream all members, never restore/capture.
remote=R.parent/'held-consumer-final-baseline-root-remote-recovery02-2026-10-03';base='research/onchain-paper-replication-2026-09-24/full_sources/held-consumer-final-baseline-root-capture01-2026-10-03';bundle=remote/'selected'/base/'bundle01';q=J(remote/'selected'/base/'REQUEST01.json');results={}
for role,count in [('capsule',925),('external',12)]:
 ar=(bundle/(role+'.tar.gz')).read_bytes();expected=q[role+'_manifest']['members'];out=io.BytesIO();gz=gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0);tw=tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT);seen=[];total=0
 for i,(name,t,b) in enumerate(m.framed_members(ar)):
  row=expected[i];assert name==row['path'] and t.mode==row['mode'];nt=tarfile.TarInfo(name);nt.mode=row['mode'];nt.uid=nt.gid=0;nt.uname=nt.gname='';nt.mtime=0
  if row['kind']=='directory':assert t.isdir() and t.size==0 and b==b'';nt.type=tarfile.DIRTYPE;nt.size=0;tw.addfile(nt)
  else:assert t.isfile() and len(b)==row['bytes'] and H(b)==row['sha256'];nt.size=len(b);tw.addfile(nt,io.BytesIO(b));total+=len(b)
  seen.append(name)
 tw.close();gz.close();assert len(seen)==count==len(expected) and out.getvalue()==ar
 results[role]={'members':count,'logical':total,'archive_sha256':H(ar),'canonical_reencoding_identical':True}
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
(R/'READBACK04.json').write_text(json.dumps({'decision':'accepted_source_only','author_manifest_members':343,'source_sha256':H(new),'inverse_all_other_bytes_and_ast':True,'tiny_refusals':cases,'single_directory_slash_positive':3,'first_fatal_identity_and_close_once':True,'actual_fetched_archive_streams':results,'actual_flat_restore_or_capture':False,'numerical_or_native_or_authority':False},indent=2,sort_keys=True)+'\n')
print('PASS343author members/full inverse;old actual-sourceRED;'+str(len(cases))+' tiny refusals/3directory positives/firstfatal closeonce;actual925+12archive stream+exactcanonical bytes. No restore/capture/native.')
