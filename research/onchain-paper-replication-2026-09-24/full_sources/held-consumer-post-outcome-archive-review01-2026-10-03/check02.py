import ast,copy,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'held-consumer-post-outcome-archive-preparation01-2026-10-03';sys.path.insert(0,str(P));import post_outcome01 as W
R=W.R;checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def refuse(f,m):
 try:f()
 except (ValueError,TypeError,FileNotFoundError,FileExistsError):checks.append('refused '+m)
 else:raise AssertionError('accepted '+m)
ck(R.digest((P/'post_outcome01.py').read_bytes())=='eca351c9bf2d12fe4ae903c9358e2d7acb9c01833bc3a826b59635130ce752ce','wrapper pin');ck(R.digest((P/'MANIFEST01.json').read_bytes())=='65a6c490c392d6a4fc7719e91c6df1d5ddc8ceb5473df4099c7bf9032d859046','manifest pin')
m=json.loads((P/'MANIFEST01.json').read_bytes());decl=set()
for row in m['members']:
 p=P/row['path'];s=p.lstat();decl.add(row['path']);ck(stat.S_IMODE(s.st_mode)==row['mode'],'original manifest mode')
 if row['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'declared directory')
 else:b=p.read_bytes();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and len(b)==row['bytes'] and R.digest(b)==row['sha256'],'declared body')
ck({str(p.relative_to(P)) for p in P.rglob('*')}==decl|{'MANIFEST01.json'},'complete candidate membership')
for n in ('recovery04.py','owned_io.py','bounded_git01.py'):ck((P/n).read_bytes()==(F/'held-consumer-final-recovery-preparation04-2026-10-03'/n).read_bytes(),'full unchanged primitive '+n)
# Owned tiny opaque append case; never a source/claim/terminal authority fixture.
root=O/'tiny';root.mkdir(mode=0o700);(root/'before').write_bytes(b'opaque original\0');old=R.scan(root);(root/'nested').mkdir(mode=0o750);(root/'nested/after').write_bytes(b'opaque appended\xff');now=R.scan(root);ck(W.subset(old,now)['added_members']==2,'actual append subset');refuse(lambda:R.same(root,old),'old whole snapshot after append')
for key,value in [('mode',0o600),('bytes',999),('sha256','f'*64),('kind','directory')]:
 changed=copy.deepcopy(now);changed['members'][0][key]=value
 refuse(lambda:W.subset(old,changed),'original '+key+' change')
changed=copy.deepcopy(now);changed['root_mode']=0o755;refuse(lambda:W.subset(old,changed),'root mode');changed=copy.deepcopy(now);changed['members']=changed['members'][1:];refuse(lambda:W.subset(old,changed),'missing original');changed=copy.deepcopy(now);changed['members'].append(changed['members'][0]);refuse(lambda:W.subset(old,changed),'duplicate');refuse(lambda:W.request(json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes())),'null future request');refuse(lambda:W.evidence({},{}),'missing genuine evidence')
for value in ('../escape','/absolute','nested//bad','.env','a.key'):
 refuse(lambda:R.path_name(value),'unsafe '+value)
for value in ('A'*64,'a'*63,None,True):refuse(lambda:W.pin(value),'bad hash')
archive=O/'tiny.tar.gz';info=R.pack(root,now,archive);flat=O/'flat';flat.mkdir(mode=0o700);out=R.FlatOutput(flat);out.begin()
try:
 result=R.restore(archive,info,now,out,prefix='capsule');out.create('support-opaque.body',b'outside opaque\0');out.finish();ck(result['members']==3 and result['regular_bodies']==2,'actual complete opaque archive recovery');ck(R.read(flat,'support-opaque.body')==b'outside opaque\0','actual support-body FD roundtrip');refuse(lambda:out.create('support-opaque.body',b'collision'),'exclusive flat collision')
 # Independent canonical compressed reconstruction from actual recovered bodies.
 metadata=json.loads(R.read(flat,'capsule-metadata.json'));buffer=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=buffer,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in now['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:b=R.read(flat,metadata['flat_members'][r['path']]);t.size=len(b);tar.addfile(t,io.BytesIO(b))
 ck(buffer.getvalue()==archive.read_bytes(),'independent whole archive reencode from recovered bytes')
 (flat/'unlisted').write_bytes(b'x');refuse(out.finish,'foreign writable member')
finally:out.close()
for name,mutation in [('hash',lambda x:x.update(sha256='0'*64)),('bytes',lambda x:x.update(bytes=True))]:
 info2=dict(info);mutation(info2);dest=O/('refused-'+name);dest.mkdir(mode=0o700);refuse(lambda:R.restore(archive,info2,now,dest),'archive '+name);ck(not list(dest.iterdir()),'refusal before writes '+name)
# FD nofollow and first-fatal controls do not fabricate authority objects.
(root/'alias').symlink_to(root/'before');refuse(lambda:R.scan(root),'symlink inventory');refuse(lambda:R.read(root,'alias'),'symlink read')
from owned_io import _cleanup,CleanupFailure
for first,last in [(MemoryError('first'),SystemExit('later')),(SystemExit('first'),MemoryError('later'))]:
 calls=[]
 def fail():calls.append(1);raise last
 try:
  try:raise first
  finally:_cleanup((fail,lambda:calls.append(2)))
 except BaseException as e:ck(e is first and calls==[1,2],'original firstfatal/allcleanup')
source=ast.parse((P/'post_outcome01.py').read_bytes());functions={n.name:n for n in source.body if isinstance(n,ast.FunctionDef)};capture=ast.unparse(functions['capture']);recover=ast.unparse(functions['recover']);ck("R.authenticate_source(cap, q['baseline'])" in capture,'actual source authenticator with original baseline');ck(capture.index('decision = evidence')<capture.index('out.mkdir'),'closed evidence before output');ck('finally:\n        R._cleanup((output.close,))' in recover,'owned output firstfatal finally');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
(O/'READBACK01.json').write_text(json.dumps({'decision':'SOURCE_CHECKS_PASSED_ONLY','checks':len(checks),'checks_detail':checks,'actual_outcome_or_authority_constructed':False,'actual_roots_scanned':False},indent=2)+'\n');print('Independent checks',len(checks))
