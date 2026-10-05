"""One exact source inverse and real owned FD allocation RED/GREEN pair."""
from pathlib import Path
import sys,os,json,hashlib,ast,importlib.util,stat
H=Path(__file__).resolve().parent;F=H.parent;P=F/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05';N=F/'financial-wrapper-continuation-current-preservation-preparation02-2026-10-05';sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'));from verify_capture01 import Reader,R
rd=Reader();m=json.loads(rd.read(N/'MANIFEST01.json','c13ba272f78eaa6616f8da2fd9079b1c213e97343a1a9fa05a6cb447d50cbfd4'));actual=set()
for root,dirs,files in os.walk(N,followlinks=False):
 for name in dirs+files:actual.add((Path(root)/name).relative_to(N).as_posix())
rd.need(actual=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'complete successor seal')
for row in m['members']:
 p=N/row['path'];s=p.lstat();rd.need(stat.S_IMODE(s.st_mode)==row['mode'],'exact typed mode')
 if row['kind']=='file':rd.need(len(rd.read(p,row['sha256']))==row['bytes'],'every successor body')
 else:rd.need(row['kind']=='directory' and stat.S_ISDIR(s.st_mode),'ordinary successor directory')
old=rd.read(P/'bind02.py','9161fc3812687708f4365b3137b05f9d2b65bb8a8b9a314cdc966cf64b99ccec');new=rd.read(N/'bind03.py','53f4a5fc154311e7dcbbb77dcdd37954a6f07f9ab83e5ad7ecc543932b98375b')
a=b"child=os.open(e.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd);digest=hashlib.sha256();size=0;parts=[] if n in save else None";b=b"digest=hashlib.sha256();size=0;parts=[] if n in save else None;child=os.open(e.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)"
rd.need(old.count(a)==new.count(b)==1 and old.replace(a,b)==new and new.replace(b,a)==old,'complete single literal inverse');rd.need(ast.dump(ast.parse(new.replace(b,a)))==ast.dump(ast.parse(old)),'full AST inverse')
for n,h in {'owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():rd.need(rd.read(P/n,h)==rd.read(N/n,h),'unchanged actual primitive bytes')
results=[]
for label,path in [('old',P/'bind02.py'),('new',N/'bind03.py')]:
 sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location('bind_'+label,path);B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);root=H/('pair-'+label);root.mkdir(mode=0o700);f=root/'body';f.write_bytes(b'opaque real descriptor body');open0=os.open;close0=os.close;digest0=hashlib.sha256;opened=[];closed=[];primary=MemoryError('real digest allocation boundary')
 def opening(*args,**kw):
  fd=open0(*args,**kw);opened.append(fd);return fd
 def closing(fd):closed.append(fd);return close0(fd)
 def allocation(*args,**kw):raise primary
 os.open=opening;os.close=closing;hashlib.sha256=allocation
 try:
  try:B.Census().tree(root,{'body':'file'},set());raise AssertionError('missing allocation error')
  except BaseException as e:
   assert e is primary
   leaked=[]
   for fd in opened:
    try:os.fstat(fd);leaked.append(fd)
    except OSError:pass
 finally:os.open=open0;os.close=close0;hashlib.sha256=digest0
 for fd in leaked:close0(fd)
 rd.need(len(leaked)==(1 if label=='old' else 0),'exact original leak/successor zero leak');c=B.Census();v=c.tree(root,{'body':'file'},{'body'});c.finish();rd.need(c.saved[(str(root),'body')]==f.read_bytes() and v['members'][0]['sha256']==R.digest(f.read_bytes()),'real ordinary saved bytes unaffected')
 results.append({'source':label,'source_sha256':R.digest(old if label=='old' else new),'original_primary_preserved':True,'actual_opened_fds':opened,'candidate_closed_fds':closed,'fds_still_open_after_return':leaked,'reviewer_closed_after_observation':leaked,'ordinary_control_pass':True})
rd.finish();R.put(H/'SUCCESSOR_READBACK01.json',{'schema_version':1,'decision':'ACCEPTED_NARROW_ACQUISITION_CORRECTION_SOURCE_ONLY','source_sha256':R.digest(new),'old_source_sha256':R.digest(old),'literal_and_AST_inverse':True,'real_pair':results,'full_collect_executed':False,'old818_reread':False,'checks':rd.checks,'read_bytes':rd.total});print(json.dumps(results))
