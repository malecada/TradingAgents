"""Owned opaque primitives only: never runs the public composition or a restoration."""
from pathlib import Path
import copy,gzip,hashlib,importlib.util,io,json,os,stat,tarfile
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('composed',D/'verify02.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
O=D/'owned-controls01';O.mkdir(mode=0o700);rows=[]
def record(name,f,refuse=False):
 try:f()
 except BaseException as e:
  if not refuse:raise
  rows.append({'name':name,'refused':True,'error_type':type(e).__name__});return
 if refuse:raise AssertionError('accepted '+name)
 rows.append({'name':name,'passed':True})
def file(name,b=b'opaque'):
 p=O/name;p.write_bytes(b);p.chmod(0o600);return p
p=file('normal');record('bounded real descriptor',lambda:V.Reader().read(p,V.h(b'opaque'),0o600))
record('wrong hash',lambda:V.Reader().read(p,'0'*64),True)
record('wrong mode',lambda:V.Reader().read(p,expected_mode=0o400),True)
s=O/'symlink';s.symlink_to(p);record('symlink refusal',lambda:V.Reader().read(s),True)
f=O/'fifo';os.mkfifo(f,0o600);record('FIFO refusal before open',lambda:V.Reader().read(f),True)
l=O/'hardlink';os.link(p,l);record('hardlink refusal',lambda:V.Reader().read(p),True)
big=file('extent');fd=os.open(big,os.O_WRONLY);os.ftruncate(fd,V.FILE+1);os.close(fd);record('4MiB bound',lambda:V.Reader().read(big),True)
p2=file('total');r=V.Reader();r.total=V.TOTAL;record('total bound',lambda:r.read(p2),True)
r=V.Reader();r.start-=V.SECONDS;record('deadline',lambda:r.read(p2),True)
r=V.Reader();r.read(p2);p2.write_bytes(b'changed');record('cached currentness',lambda:r.read(p2),True)
p3=file('late-a');p4=file('late-b');r=V.Reader();r.read(p3);real=os.close
try:
 def late(fd):
  real(fd);p3.write_bytes(b'later-close-mutation')
 V.os.close=late;r.read(p4)
finally:V.os.close=real
record('real late FD close changes earlier body final refusal',r.finish,True)
p5=file('primary');opened=[];realopen=os.open;realread=os.read;fatal=KeyboardInterrupt('primary');secondary=SystemExit('secondary')
try:
 def tracked(*a,**k):fd=realopen(*a,**k);opened.append(fd);return fd
 def badread(*a):raise fatal
 def badclose(fd):real(fd);raise secondary
 V.os.open=tracked;V.os.read=badread;V.os.close=badclose
 try:V.Reader().read(p5)
 except BaseException as e:
  assert e is fatal and secondary in e.__dict__['composed_failures']
  rows.append({'name':'first fatal identity and secondary close identity','passed':True})
 else:raise AssertionError('primary lost')
finally:V.os.open=realopen;V.os.read=realread;V.os.close=real
for fd in opened:record('actual closed FD',lambda:os.fstat(fd),True)
# Full namespace mutation detected after iterator cleanup.
t=O/'tree';t.mkdir(mode=0o700);(t/'a').write_bytes(b'a');r=V.Reader();r.tree(t);(t/'foreign').write_bytes(b'b');record('late foreign namespace',r.finish,True)
for n in ['../a','/absolute','x/../a','x//a','keys/a','.env']:
 record('unsafe '+n,lambda n=n:V.safe(n),True)
record('duplicate JSON keys',lambda:V.decode(b'{"x":1,"x":2}'),True)
record('nonfinite JSON',lambda:V.decode(b'{"x":NaN}'),True)
# Actual opaque flat layout, never a Root receipt or an accepted recovery proof.
flat=O/'opaque-flat';flat.mkdir(mode=0o700);b=b'only opaque engineering bytes';(flat/'body-00000.body').write_bytes(b);(flat/'body-00000.body').chmod(0o600)
m={'schema_version':1,'root_mode':0o775,'members':[{'path':'original-name','kind':'file','mode':0o664,'bytes':len(b),'sha256':V.h(b)}]}
sink=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
  ti=tarfile.TarInfo('original-name');ti.mode=0o664;ti.size=len(b);tar.addfile(ti,io.BytesIO(b))
a=sink.getvalue();mpin=V.h(json.dumps(m).encode());arc={'bytes':len(a),'sha256':V.h(a),'manifest_sha256':mpin};md={'schema_version':1,'manifest':m,'archive':arc,'flat_members':{'original-name':'body-00000.body'}};mp=flat/'body-metadata.json';mp.write_text(json.dumps(md));mp.chmod(0o600)
rec={'status':'fresh-flat-archival-recovery-not-origin-proof','instantiated_posix_tree':False,'recovered_tree_git_join':False,'runtime_package_bodies_recovered':False,'outside_stores_recovered':False,'research_authority':False,'metadata_file':mp.name,'metadata_sha256':V.h(mp.read_bytes()),'archive_sha256':V.h(a),'manifest_sha256':mpin,'members':1,'regular_bodies':1,'root_mode':0o775}
def check(rec=rec,m=m,a=a):
 r=V.Reader();V.flat_scope(r,flat,rec,m,a);r.finish()
record('actual opaque flat original664/root775 private600/700',check)
for key,value in [('research_authority',True),('root_mode',0o700),('members',2),('regular_bodies',0),('metadata_sha256','0'*64),('archive_sha256','0'*64),('manifest_sha256','0'*64),('metadata_file','../outside')]:
 q=copy.deepcopy(rec);q[key]=value;record('flat inverse '+key,lambda q=q:check(q),True)
record('trailing archive data',lambda:check(a=a+b'x'),True)
(flat/'body-00000.body').chmod(0o664);record('private output mode regression',check,True);(flat/'body-00000.body').chmod(0o600)
(flat/'foreign').write_bytes(b'foreign');record('flat missing denominator/foreign member',check,True)
# Full opaque Git logical graph. These are in-memory source metadata, never installed Git.
def obj(kind,b):return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
blob=b'opaque';bo=obj('blob',blob);tree=b'100644 name\0'+bytes.fromhex(bo);tr=obj('tree',tree);commit=b'tree '+tr.encode()+b'\n\nopaque\n';co=obj('commit',commit);objects={bo:('blob',blob),tr:('tree',tree),co:('commit',commit)}
record('complete opaque reachable graph',lambda:V.require(V.git_graph(objects,co)=={'name':('100644',blob)},'graph'))
q=dict(objects);q['0'*40]=('blob',b'extra');record('unreachable extra object',lambda:V.git_graph(q,co),True)
q=dict(objects);del q[bo];record('missing reached object',lambda:V.git_graph(q,co),True)
(D/'CONTROLS01.json').write_text(json.dumps({'schema_version':1,'opaque_engineering_only':True,'authority':False,'rows':rows},indent=2)+'\n');print(len(rows))
