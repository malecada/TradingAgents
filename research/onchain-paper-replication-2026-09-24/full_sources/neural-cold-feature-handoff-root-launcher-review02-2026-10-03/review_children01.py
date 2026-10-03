"""Actual tiny new process cleanup; all research/native authority preflight mocked."""
import ast,hashlib,importlib.util,json,os,pathlib,signal,subprocess,sys,time,types
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent;A=P.parent/'neural-cold-feature-handoff-root-launcher-preparation02-2026-10-03'
s=importlib.util.spec_from_file_location('review_launcher02_children',A/'launcher02.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
result={'original_research_or_native_execution':False,'preflight_context_and_resource_setter_mocked':True}
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
 def cleanup(*args,**kwargs):cleanupcalls.append(case);return {'synthetic_no_native_or_controller':True}
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
