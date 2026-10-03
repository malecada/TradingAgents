"""Independent source boundaries and tiny owned child cleanup; no native/research work."""
import ast,copy,hashlib,importlib.util,json,os,pathlib,signal,subprocess,sys,time,types
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent;BASE=P.parent;ROOT=P.parents[3]
A=BASE/'neural-cold-feature-handoff-root-launcher-preparation01-2026-10-03'
C=BASE/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha((A/'MANIFEST01.json').read_bytes())=='3b71efb204e0e2512c2555cffb4525166ce5d88ea0d2a450f38e2a0b519ef0f6'
manifest=json.loads((A/'MANIFEST01.json').read_bytes())
for r in manifest['files']:
 b=(A/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
for target,r in json.loads((A/'SOURCE_ORIGINS01.json').read_bytes()).items():assert sha((ROOT/r['path']).read_bytes())==r['sha256'] and (ROOT/r['path']).read_bytes()==(C/'source-bodies'/target).read_bytes()
s=importlib.util.spec_from_file_location('review_root_launcher',A/'launcher01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
result={'manifest_files':len(manifest['files']),'source_origins':7,'native_or_research_execution':False}
# Canonical class reducer counterexample only. No reachable raise from stop_native
# is claimed: its current no-callback body doesn't construct this class.
t=ast.parse((C/'source-bodies/tradingagents/research/onchain_replication/owned_io.py').read_bytes());ns={};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='CleanupFailure'],type_ignores=[]),'canonical-class-only','exec'),ns)
u=ns['CleanupFailure']('synthetic uncertainty');actual=MemoryError('later actual fatal')
assert m.fatal(u) and m.select(u,actual) is u
result['canonical_class_reducer_gap_only']={'reproduced':True,'production_reachability_not_established':True}
# Exact actual terminal-finally source, excluding prior child cleanup. A synthetic
# result stands for reaching this block, NOT an actual accepted experiment.
tree=ast.parse((A/'launcher01.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');outer=next(n for n in fn.body if isinstance(n,ast.Try));tail=outer.finalbody
start=next(i for i,n in enumerate(tail) if isinstance(n,ast.Try) and any(isinstance(c,ast.Name) and c.id=='disposition' for c in ast.walk(n)))
selected=copy.deepcopy(tail[start:]);directory=P/'tail-fixture';directory.mkdir();empty=P/'empty-source';empty.mkdir();watches=[]
def watch(d):
 watches.append(str(d))
 if len(watches)==2:raise ValueError('synthetic final-tail floor refusal')
 return {'files':0,'allocated_bytes':0}
ns=dict(m.__dict__);ns.update(directory=directory,root=empty,identity='synthetic-review-tail',q={'phase':'materialize','source':'b'*40},request_reference={'synthetic':True},process=None,observed={},primary=None,result={'synthetic_reached_success_tail':True},root_watch=watch)
def retain(e):ns['primary']=m.select(ns['primary'],e)
ns['retain']=retain
exec(compile(ast.Module(body=selected,type_ignores=[]),'actual-terminal-finally','exec'),ns)
assert isinstance(ns['primary'],ValueError) and len(watches)==2
ob=json.loads((directory/'observation.json').read_bytes());assert ob['result']=={'synthetic_reached_success_tail':True}
assert not (directory/'failure.json').exists() and not (directory/'error.txt').exists()
result['late_tail_failure']={'reproduced':True,'original_observation_result_not_revoked':True,'failure_marker_absent':True,'would_raise_nonzero':True}
# Genuine source read and descriptor cleanup with first-fatal identity.
body=P/'tiny-source';body.write_bytes(b'one')
for i,err in enumerate((MemoryError('read'),KeyboardInterrupt(),SystemExit(5))):
 closed=[];realclose=os.close
 def badclose(fd):closed.append(fd);realclose(fd);raise OSError('close ordinary')
 with patch.object(os,'read',side_effect=err),patch.object(os,'close',side_effect=badclose):
  try:m.read(body)
  except BaseException as got:assert got is err
  else:raise AssertionError('lost fatal')
 assert len(closed)==1
result['read_firstfatal_closeonce_cases']=3
# Safe new children: execute's preflight/context and descendant helper are mocks;
# Popen really spawns only stdlib sleep in an owned working directory. No proof
# supervisor, unit, Owner, claim, array or numerical module can run.
realpopen=subprocess.Popen;realwrite=m.write;realsleep=time.sleep;children=[];cleanupcalls=[]
for case in ('start-receipt-fatal','actual-SIGTERM-cancellation'):
 sandbox=P/case;sandbox.mkdir();root=sandbox/'source';root.mkdir();out=sandbox/'out';out.mkdir()
 q={'phase':'materialize','source':'c'*40,'output_parent':str(out),'release':{'sha256':'a'*64},'reviews':{},'capsule':str(root)}
 ctx={'environment':{},'release':{'source':q['source']},'sources':{},'experiment':{'inputs':{}}};mem=types.SimpleNamespace(mem_available=lambda:7*m.GIB)
 def popen(command,**kwargs):
  p=realpopen([sys.executable,'-B','-c','import time;time.sleep(10)'],**kwargs);children.append(p);return p
 sentinel=MemoryError('synthetic child start receipt failure')
 def write(d,n,b):
  if case=='start-receipt-fatal' and n=='child.json':raise sentinel
  return realwrite(d,n,b)
 sent=[]
 def sleep(seconds):
  if not sent:sent.append(True);os.kill(os.getpid(),signal.SIGTERM)
  else:realsleep(min(seconds,.01))
 def cleanup(*args):cleanupcalls.append(case);return {'synthetic_no_native_or_controller':True}
 fake_resource=types.SimpleNamespace(RLIMIT_FSIZE=1,setrlimit=lambda *a:None,getrlimit=lambda *a:(m.MAX,m.MAX))
 oldraw=sys.modules.get('proof_raw01');sys.modules['proof_raw01']=types.SimpleNamespace()
 initial_handlers={sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT)}
 try:
  with patch.object(m,'validate',return_value=(root,{},ctx,mem,{},'unused-release.json')),patch.object(m,'resource',fake_resource),patch.object(m.shutil,'disk_usage',return_value=types.SimpleNamespace(free=20*m.GIB)),patch.object(m,'IDS',{'materialize':'synthetic-owned-review'}),patch.object(m.subprocess,'Popen',side_effect=popen),patch.object(m,'write',side_effect=write),patch.object(m,'cleanup_descendants',side_effect=cleanup),patch.object(m.time,'sleep',side_effect=sleep if case=='actual-SIGTERM-cancellation' else realsleep):
   try:m.execute(q,{'synthetic_request':True})
   except BaseException as e:
    if case=='start-receipt-fatal':assert e is sentinel
    else:assert isinstance(e,InterruptedError)
   else:raise AssertionError('unexpected wrapper success')
 finally:
  if oldraw is None:sys.modules.pop('proof_raw01',None)
  else:sys.modules['proof_raw01']=oldraw
  for p in children:
   if p.poll() is None:p.kill();p.wait(timeout=3)
 assert all(signal.getsignal(sig)==v for sig,v in initial_handlers.items())
 child=children[-1];assert child.returncode is not None and not pathlib.Path('/proc',str(child.pid)).exists()
 own=out/'synthetic-owned-review';assert (own/'intent.json').exists() and (own/'failure.json').exists()
 # Permanent synthetic one-use output refuses, no original experiment namespace.
 try:m.reserve(out,'synthetic-owned-review',{})
 except FileExistsError:pass
 else:raise AssertionError('reservation reused')
 result[case]={'pid':child.pid,'exit':child.returncode,'absent':True,'original_signal_handlers_restored':True,'permanent_synthetic_reservation':True}
assert len(cleanupcalls)==2
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps(result,indent=2))
