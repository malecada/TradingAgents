import ast,dataclasses,difflib,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-batch-output-transport-spool-preparation03-2026-10-04';O=F/'financial-batch-output-transport-spool-preparation02-2026-10-04';V=F/'financial-batch-output-transport-spool-source-review02-2026-10-04';B=F/'financial-batch-output-transport-spool-preparation01-2026-10-04';sys.path.insert(0,str(A));import spool05 as S
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0

def ok(v):
 global checks
 assert v;checks+=1
for root,mname,want,count in [(A,'MANIFEST01.json','b154c571ee476a9e7835949d3494be74de879fc94403354717ccbf2dc9fb019f',581),(V,'MANIFEST02.json','207f5fb1e5e30c590cef7defc0c4f56d9d9807e998fb299297990016d50085a7',520),(O,'MANIFEST01.json','a165e90de609e87d92f602bb4a845f538eed6e1f522aa8e471ab798d8ad70273',520)]:
 ok(sha((root/mname).read_bytes())==want);rows=json.loads((root/mname).read_text())['members'];ok(len(rows)==count)
 ok(sorted(str(p.relative_to(root)) for p in root.rglob('*') if p!=root/mname)==sorted(r['path'] for r in rows))
 for r in rows:
  p=root/r['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==r['mode'])
  if r['kind']=='file':b=p.read_bytes();ok(stat.S_ISREG(s.st_mode) and len(b)==r['bytes'] and sha(b)==r['sha256'])
  elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode))
  else:ok(r['kind']=='symlink' and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'])
old=(O/'spool04.py').read_text();new=(A/'spool05.py').read_text();inv=json.loads((A/'INVERSE01.json').read_text());delta=inv['removed_exact_addition'];ok(new.count(delta)==1);ok(new.replace(delta,'')==old);ok(ast.dump(ast.parse(new.replace(delta,'')))==ast.dump(ast.parse(old)))
ok(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original02/spool04.py',tofile='successor03/spool05.py'))==(A/'INVERSE01.diff').read_text())
ok((A/'owned_io.py').read_bytes()==(O/'owned_io.py').read_bytes());ok(sha((A/'owned_io.py').read_bytes())=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb')
ok(sha((A/'ROOT_CODEC_SPOOL_INTEGRATION_GAP01.json').read_bytes())=='3afc500164f19191e3f3b81b4babfc1c19eaec1f15abfaaae3fcbc60070fa838')
for r in json.loads((B/'SOURCE_PINS01.json').read_text()):
 p=Path(r['path']);b=p.read_bytes();ok(p.resolve()==p and len(b)==r['bytes'] and sha(b)==r['sha256'] and stat.S_IMODE(p.lstat().st_mode)==r['mode'])
a=S.Ack('a'*64,0,0,1,'b'*64,'c'*64);ok(S.valid_ack(a))
for field in ('page','chunk','size'):
 for value in (False,True,0.0,1.0,'0',None,[],{},-1):ok(not S.valid_ack(dataclasses.replace(a,**{field:value})))
for field in ('plan','sha256','receipt_sha256'):
 for value in (None,True,0,b'a'*64,'A'*64,'a'*63,'a'*65,[]):ok(not S.valid_ack(dataclasses.replace(a,**{field:value})))
# Constructor ancestry pins must precede allocation, and the postcleanup check
# follows the walk but precedes root stat and all inode/payload observations.
t=ast.parse(new);cl=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Spool');funs={n.name:n for n in cl.body if isinstance(n,ast.FunctionDef)}
check_text=ast.get_source_segment(new,funs['check']);ok(check_text.index('_path_identity')<check_text.index('resolve(strict=True)')<check_text.index('os.stat'))
init=ast.get_source_segment(new,funs['__init__']);ok(init.index('_path_pin=self._path_identity')<init.index("self._allocate('plan'"))
# Actual walker primary fatal plus three real descriptor close failures.
p=S.Plan((S.Member(0,0,1,S.digest(b'x')),),1,0,0);l,a0=p.required();p=dataclasses.replace(p,logical_reservation=l,allocated_reservation=a0)
r=H/'walk-fatal04';r.mkdir(mode=0o700);s=S.Spool(r,p);real_open=os.open;real_close=os.close;opened=[];closed=[];primary=KeyboardInterrupt('walker primary');counter=[0]
def op(*args,**kw):
 counter[0]+=1
 if counter[0]==4:raise primary
 fd=real_open(*args,**kw);opened.append(fd);return fd
def close(fd):real_close(fd);closed.append(fd);raise OSError('after real close')
try:
 os.open=op;os.close=close
 try:s.transfer(b'x',None,None)
 except BaseException as e:ok(e is primary)
 else:raise AssertionError('missing fatal')
finally:os.open=real_open;os.close=real_close
ok(s.failed and len(opened)==3 and set(opened)==set(closed))
for fd in opened:
 try:os.fstat(fd)
 except OSError:ok(True)
 else:raise AssertionError('fd leak')
s.close()
# Controlled low-free-space metadata at cleanup tests the sampled guard only;
# no actual filesystem is filled or actual resource capacity inferred.
r=H/'cleanup-floor04';r.mkdir(mode=0o700);s=S.Spool(r,p);real_vfs=os.fstatvfs;consumed=s.consumed
v=list(real_vfs(s.fd));v[4]=0;low=os.statvfs_result(v)
def cleanup():os.fstatvfs=lambda fd:low
def ack(i,m,b):return S.Ack(i,m.page,m.chunk,m.size,m.sha256,'a'*64)
try:
 try:s.transfer(b'x',ack,lambda a:S.Recovery(a,b'x'),cleanup)
 except ValueError as e:ok('floor' in str(e));ok(s.failed and s.states==('RECOVERED',) and s.consumed==consumed and 'terminal' in s._sealed)
 else:raise AssertionError('floor bypass')
finally:os.fstatvfs=real_vfs;s.close()
# Constructor rejects a pre-existing canonical-parent alias before any file.
parent=H/'constructor-parent';parent.mkdir();target=H/'constructor-target';target.mkdir();r=target/'root';r.mkdir(mode=0o700);alias=parent/'alias';alias.symlink_to(target,target_is_directory=True)
try:S.Spool(alias/'root',p)
except ValueError:ok(not list(r.iterdir()))
else:raise AssertionError('constructor alias accepted')
ok(all(n not in sys.modules for n in ('numpy','torch','pandas','tradingagents.research.lifecycle')))
(H/'AUTH04.json').write_text(json.dumps({'checks':checks,'whole_byte_AST_inverse':True,'all_source_and_review_members':1621,'unchanged_IO_refs_gap':True,'real_walker_fatal_closes':3,'controlled_floor_test_not_actual_capacity':True},sort_keys=True,indent=2)+'\n');print(checks,'checks passed')
