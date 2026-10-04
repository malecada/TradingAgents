from pathlib import Path
import os,stat,json,hashlib,ast,types,time,importlib.util,shutil,datetime
H=Path(__file__).resolve().parent;B=H.parent;D=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';C=B/'heartbeat-root-checkpoint10-2026-10-04/root_operational_flat04.py';checks=[];results=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
raw=C.read_bytes();ok(sha(raw)=='815d2a8872372a773cc68e48217a26051e1de497ba0e3986e314967f4ff6845b','exact caller pin');tree=ast.parse(raw)
names={'digest','signature','read','put'};functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];mod=ast.Module(body=functions,type_ignores=[]);ns={'Path':Path,'os':os,'stat':stat,'json':json,'hashlib':hashlib,'FILE':4194304,'D':H};exec(compile(mod,'actual-extracted-caller-functions','exec'),ns)
draft_raw=ns['read'](D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json','770f509c8a65a1a5a6cb33e2efbf8215c9466ba5af235251b883ac1452299e21');draft=json.loads(draft_raw)
for n,pin in draft['helpers_and_metadata'].items():
 b=ns['read'](D/n,pin['sha256']);ok(len(b)==pin['bytes'] and stat.S_IMODE((D/n).lstat().st_mode)==pin['mode'],'installed body/mode '+n)
for name,pin in [('REMOTE_RECOVERY01.json',draft['remote_receipt_sha256']),('SELECTED_BODIES01.json',draft['selection_sha256']),('ROOT_REMOTE03_EXIT01.json',draft['original_Root_exit_sha256'])]:ns['read'](D/name,pin);ok(True,'actual prerequisite '+name)
review=B/'financial-wrapper-compatibility-operational-delta-flat-source-mode-review04-2026-10-04';ok(sha((review/'MACHINE01.json').read_bytes())==draft['source_review_machine_sha256'] and sha((review/'MANIFEST01.json').read_bytes())==draft['source_review_manifest_sha256'],'genuine independently accepted source review')
fresh=('flat-operational-delta01','flat-failed-remote02-01','FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json','FLAT_POSTWRITE_OBSERVATION01.json','ROOT_FLAT04_INTENT01.json','ROOT_FLAT04_SPAWN01.json','ROOT_FLAT04.stdout','ROOT_FLAT04.stderr','ROOT_FLAT04_EXIT01.json')
for n in fresh:ok(not os.path.lexists(D/n),'fresh namespace '+n)
spec=importlib.util.spec_from_file_location('installed_flat',D/'restore01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);r=json.loads((D/'REMOTE_RECOVERY01.json').read_bytes());sel=json.loads((D/'SELECTED_BODIES01.json').read_bytes());co=M.VerifiedCohort();records=M.authenticate_selected(D,r,sel,draft['selection_sha256'],co);co.check();ok(len(records)==15,'genuine installed read-only15 component')
observation=M.W.census(D);free=shutil.disk_usage(D).free;ok(free>=10*1024**3,'instantaneous10GiBfloor');ok(stat.S_IMODE(D.lstat().st_mode)==0o700,'private D root')
# Real descriptor handed to an fdopen that fails. Never reclose the original integer until identity verified.
original_os=ns['os'];proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});opened=[];err=MemoryError('owned fdopen witness')
def failing_fdopen(fd,*a,**kw):opened.append((fd,os.fstat(fd).st_ino));raise err
proxy.fdopen=failing_fdopen;ns['os']=proxy
try:
 try:ns['put']('FDOPEN_FAILURE01.json',{'opaque':'owned fixture'})
 except BaseException as e:ok(e is err,'real original fdopen fatal propagated')
 else:raise AssertionError('fdopen did not fail')
 fd,ino=opened[0];actual=os.fstat(fd);ok(actual.st_ino==ino,'EF1 real descriptor remains open after source put exits')
 results.append({'id':'EF1','line':26,'error':'MemoryError from os.fdopen','descriptor':fd,'inode':ino,'observed_open_after_exception':True,'partial_body_bytes':(H/'FDOPEN_FAILURE01.json').stat().st_size})
finally:
 ns['os']=original_os
 for fd,ino in opened:
  if os.fstat(fd).st_ino==ino:os.close(fd)
for fd,ino in opened:
 try:os.fstat(fd)
 except OSError:ok(True,'reviewer-only descriptor cleanup confirmed')
 else:raise AssertionError('reviewer cleanup failed')
# Exact actual outer finally clause around an active fatal; genuine W.census on tiny owned root.
outer=next(n for n in tree.body if isinstance(n,ast.Try) and n.finalbody)
final=compile(ast.Module(body=outer.finalbody,type_ignores=[]),'actual-extracted-outer-finally','exec')
primary=KeyboardInterrupt('original owned fatal');later=SystemExit(17);seen=[];ns.update({'child':None,'primary':primary,'cleanup':[],'observations':[],'W':M.W,'time':time,'begun':time.monotonic(),'code':None})
proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)})
def fail_terminal_fdopen(fd,*a,**kw):seen.append((fd,os.fstat(fd).st_ino));raise later
proxy.fdopen=fail_terminal_fdopen;ns['os']=proxy
try:
 try:
  try:raise primary
  finally:exec(final,ns)
 except BaseException as e:
  ok(e is later and e is not primary,'EF2 unguarded terminal publication replaces original fatal');results.append({'id':'EF2','line':95,'primary':'KeyboardInterrupt','terminal_publication_error':'SystemExit','observed_top_level':'SystemExit','original_primary_in_context':e.__context__ is primary,'primary_identity_preserved':False})
 else:raise AssertionError('fatal disappeared')
finally:
 ns['os']=original_os
 for fd,ino in seen:
  if os.fstat(fd).st_ino==ino:os.close(fd)
# Refuse ordinary changed pin and redirected owned inputs using exact caller read.
p=H/'valid-owned-body';p.write_bytes(b'opaque');valid=sha(p.read_bytes());ok(ns['read'](p,valid)==b'opaque','exact caller read valid')
for path,pin in [(p,'0'*64),(H/'absent',valid)]:
 try:ns['read'](path,pin)
 except (AssertionError,OSError):ok(True,'caller negative pinned read '+str(path))
 else:raise AssertionError('invalid read accepted')
link=H/'negative-link';link.symlink_to(p.name)
try:ns['read'](link,valid)
except AssertionError:ok(True,'caller redirected read refused')
else:raise AssertionError('symlink accepted')
# Do not inspect unrelated process commandlines: exact previously recorded transfer PIDs only.
pids={o['pid'] for o in r['operations']}|{json.loads((D/'ROOT_REMOTE03_INTENT01.json').read_bytes())['parent_pid'],json.loads((D/'ROOT_REMOTE03_SPAWN01.json').read_bytes())['pid']}
ok(all(not Path('/proc',str(p)).exists() for p in pids),'recorded completed-transfer PIDs absent')
(H/'READBACK01.json').write_text(json.dumps({'status':'WITHHELD_EF1_EF2','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'assertions':len(checks),'checks':checks,'findings':results,'current_owned_observation':observation,'current_disk_free':free,'all_fixed_flat_names_absent':True,'actual_public_entry':False,'actual_flat_result':None,'no_live_source_or_modes_changed':True,'complete_unrelated_process_census':None},indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'WITHHELD_EF1_EF2','assertions':len(checks),'findings':results}))
