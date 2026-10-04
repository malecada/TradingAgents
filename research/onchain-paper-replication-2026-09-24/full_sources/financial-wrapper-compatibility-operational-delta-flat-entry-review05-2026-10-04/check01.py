from pathlib import Path
import ast,os,stat,sys,json,hashlib,types,importlib.util,shutil,time,resource,signal,subprocess,datetime
H=Path(__file__).resolve().parent;B=H.parent;C=B/'heartbeat-root-checkpoint10-2026-10-04';D=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';checks=[];cases=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
raw=(C/'root_operational_flat05.py').read_bytes();old=(C/'root_operational_flat04.py').read_bytes();ok(sha(raw)=='025a28c6a2c3d9ec296c895de086c003e23a25ecdd68b0743b8dec6f21cef9be','exact05');ok(sha(old)=='815d2a8872372a773cc68e48217a26051e1de497ba0e3986e314967f4ff6845b','exact preserved04')
inv=json.loads((C/'ROOT_FLAT_CALLER05_LITERAL_EDITS01.json').read_bytes());text=raw.decode()
for x in reversed(inv['replacement_segments']):ok(text[x['new_start']:x['new_end']]==x['new'],'inverse segment');text=text[:x['new_start']]+x['old']+text[x['new_end']:]
ok(text.encode()==old and ast.dump(ast.parse(text))==ast.dump(ast.parse(old)),'complete byte AST inverse')
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('review_installed_flat',D/'restore01.py');IO=load('review_ownedio',D/'utilities/owned_io.py')
def ns_for(source,where):
 t=ast.parse(source);f=[n for n in t.body if isinstance(n,ast.FunctionDef)];ns={'Path':Path,'os':os,'stat':stat,'json':json,'hashlib':hashlib,'FILE':4194304,'D':where,'IO':IO};exec(compile(ast.Module(body=f,type_ignores=[]),'exact-caller-functions','exec'),ns);return ns,t
ns,t=ns_for(raw,D);draft=json.loads(ns['read'](D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json','770f509c8a65a1a5a6cb33e2efbf8215c9466ba5af235251b883ac1452299e21'))
for n,p in draft['helpers_and_metadata'].items():body=ns['read'](D/n,p['sha256']);ok(len(body)==p['bytes'] and stat.S_IMODE((D/n).lstat().st_mode)==p['mode'],'installed exact '+n)
remote=json.loads(ns['read'](D/'REMOTE_RECOVERY01.json',draft['remote_receipt_sha256']));sel=json.loads(ns['read'](D/'SELECTED_BODIES01.json',draft['selection_sha256']));ns['read'](D/'ROOT_REMOTE03_EXIT01.json',draft['original_Root_exit_sha256']);co=M.VerifiedCohort();M.authenticate_selected(D,remote,sel,draft['selection_sha256'],co);co.check();ok(True,'genuine installed profile selected full join')
source_review=B/'financial-wrapper-compatibility-operational-delta-flat-source-mode-review04-2026-10-04'
for n,key in [('MACHINE01.json','source_review_machine_sha256'),('MANIFEST01.json','source_review_manifest_sha256')]:ok(sha((source_review/n).read_bytes())==draft[key],'actual independent source review '+n)
fresh=next(n for n in t.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='name' and isinstance(n.iter,ast.Tuple))
ns.update({'D':D});exec(compile(ast.Module(body=[fresh],type_ignores=[]),'exact-fresh-precondition','exec'),ns);ok(True,'both04 and05 complete fresh namespaces')
obs=M.W.census(D);free=shutil.disk_usage(D).free;ok(free>=M.W.POLICY['floor'],'actual disk floor');ok(D.resolve()==D and stat.S_IMODE(D.lstat().st_mode)==0o700,'actual private receiver')
# Exact selected executable path check; no commandline contents retained or printed.
matched=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:argv=(p/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 if str(D/'restore01.py').encode() in argv or str(D/'recover01.py').encode() in argv:matched.append(int(p.name))
ok(not matched,'current selected helper process census absent')
# EF1 actual descriptor failure: identical fdopen injection on exact old/new put.
for label,source in [('old04',old),('new05',raw)]:
 p=H/('fdopen-'+label);p.mkdir(mode=0o700);n,_=ns_for(source,p);real=IO.os;proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});fds=[];primary=MemoryError('owned fdopen failure')
 def fail(fd,*a,**kw):fds.append((fd,os.fstat(fd).st_ino));raise primary
 proxy.fdopen=fail;n['os']=proxy;IO.os=proxy
 try:
  try:n['put']('opaque.json',{'opaque':'owned'})
  except BaseException as e:ok(e is primary,'same injected firstfatal '+label)
  else:raise AssertionError('missing failure')
 finally:IO.os=real
 openfds=[]
 for fd,ino in fds:
  try:s=os.fstat(fd)
  except OSError:continue
  ok(s.st_ino==ino,'retained FD exact inode');openfds.append(fd);os.close(fd)
 ok(bool(openfds)==(label=='old04'),'old leaked/new closes real FD');cases.append({'case':'EF1','version':label,'fd_open_after':bool(openfds),'reviewer_closed_old_only':label=='old04'})
# Exact final-body plus subsequent primary propagation: actual owned writes/FD cleanup.
outer=next(n for n in t.body if isinstance(n,ast.Try) and n.finalbody);post=next(n for n in t.body if isinstance(n,ast.If) and ast.unparse(n.test)=='primary is not None');final=compile(ast.Module(body=outer.finalbody+[post],type_ignores=[]),'exact05-final-and-primary-propagation','exec')
typeset=[None,ValueError,KeyboardInterrupt,SystemExit,MemoryError]
for i,pt in enumerate(typeset):
 for j,st in enumerate(typeset):
  p=H/('pair-%d-%d'%(i,j));p.mkdir(mode=0o700);n,_=ns_for(raw,p);primary=None if pt is None else pt('primary');secondary=None if st is None else st('terminal');n.update({'primary':primary,'child':None,'code':0,'cleanup':[],'observations':[],'FAILURE_OBJECTS':[] if primary is None else [primary],'W':M.W,'resource':resource,'time':time,'begun':time.monotonic()});real=IO.os;proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});fds=[]
  def opened(fd,*a,**kw):
   fds.append((fd,os.fstat(fd).st_ino))
   if secondary is not None:raise secondary
   return os.fdopen(fd,*a,**kw)
  proxy.fdopen=opened;IO.os=proxy;error=None
  try:exec(final,n)
  except BaseException as e:error=e
  finally:IO.os=real
  def fatal(x):return x is not None and (isinstance(x,MemoryError) or not isinstance(x,Exception))
  expected=primary if fatal(primary) else secondary if fatal(secondary) else None
  if expected is not None:ok(error is expected,'exact firstfatal identity pair%d%d'%(i,j))
  elif secondary is not None:ok(isinstance(error,IO.CleanupFailure),'ordinary cleanup uncertainty pair%d%d'%(i,j))
  else:ok(error is primary,'no secondary preserves outcome pair%d%d'%(i,j))
  if secondary is not None:ok(any(z is secondary for z in n['FAILURE_OBJECTS']),'actual secondary retained pair%d%d'%(i,j))
  for fd,ino in fds:
   try:os.fstat(fd)
   except OSError:ok(True,'real terminal FD absent pair%d%d'%(i,j))
   else:raise AssertionError('new terminal FD leak')
  cases.append({'case':'final-pair','primary':None if pt is None else pt.__name__,'secondary':None if st is None else st.__name__,'escaped':None if error is None else type(error).__name__,'secondary_object_retained':secondary is None or any(z is secondary for z in n['FAILURE_OBJECTS'])})
# Actual tiny child kill/reap through exact cleanup; no helper/Root entry invoked.
p=H/'tiny-child';p.mkdir(mode=0o700);n,_=ns_for(raw,p);primary=KeyboardInterrupt('tiny cleanup');child=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(10)'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);n.update({'primary':primary,'child':child,'code':None,'cleanup':[],'observations':[],'FAILURE_OBJECTS':[primary],'W':M.W,'resource':resource,'time':time,'begun':time.monotonic(),'signal':signal})
try:
 try:exec(final,n)
 except BaseException as e:ok(e is primary,'actual tiny child final firstfatal')
 ok(child.returncode==-signal.SIGKILL and not Path('/proc',str(child.pid)).exists(),'actual tiny child killed/reaped absent');cases.append({'case':'actual tiny child','pid':child.pid,'returncode':child.returncode,'absent':True})
finally:
 if child.poll() is None:child.kill();child.wait()
# Exact stdout/stderr context cleanup with failed second fdopen; no body/child spawn.
withnode=outer.body[0];context=ast.With(items=withnode.items,body=[ast.Pass()],type_comment=None);ast.fix_missing_locations(context);code=compile(ast.Module(body=[context],type_ignores=[]),'exact-two-stdio-contexts-only','exec');p=H/'stdio-failure';p.mkdir(mode=0o700);n,_=ns_for(raw,p);real=IO.os;proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});fds=[];primary=KeyboardInterrupt('second stdio fdopen')
def second(fd,*a,**kw):
 fds.append(fd)
 if len(fds)==2:raise primary
 return os.fdopen(fd,*a,**kw)
proxy.fdopen=second;IO.os=proxy
try:
 try:exec(code,n)
 except BaseException as e:ok(e is primary,'second stdio fdopen original fatal')
finally:IO.os=real
for fd in fds:
 try:os.fstat(fd)
 except OSError:ok(True,'both stdio real descriptors closed')
 else:raise AssertionError('stdio descriptor leak')
# Actual final preconditions again after all owned controls; no namespace changes.
exec(compile(ast.Module(body=[fresh],type_ignores=[]),'exact-fresh-recheck','exec'),ns);co.check();ok(True,'terminal original receipt/profile/selection/currentness and fresh recheck')
(H/'READBACK01.json').write_text(json.dumps({'status':'PASS_EXACT_ENTRY05_REVIEW','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'assertions':len(checks),'checks':checks,'cases':cases,'original_root_observation':obs,'disk_free':free,'selected_process_matches':matched,'actual_public_entry':False,'actual_flat_result':None,'real_tiny_child_only':True,'sampled_not_continuous':True},indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'PASS','assertions':len(checks),'cases':len(cases)}))
