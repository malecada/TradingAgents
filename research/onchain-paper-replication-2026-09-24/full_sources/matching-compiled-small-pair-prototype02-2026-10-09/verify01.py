import os,sys,resource,signal,time,json,subprocess,hashlib,importlib.util,copy,ast
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT));os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,60),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.alarm(60);start=time.monotonic_ns();receipt={'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':60};(P/'LIMITER01.json').write_text(json.dumps(receipt,indent=2)+'\n');assert receipt['affinity']==[3]
cmd=['/usr/bin/cc','-std=c11','-O3','-fno-fast-math','-ffp-contract=off','-fPIC','-shared',str(P/'reduction.c'),'-lm','-o',str(P/'reduction.so')];r=subprocess.run(cmd,capture_output=True,text=True);(P/'COMPILE01.json').write_text(json.dumps({'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n');assert r.returncode==0
helper=P/'compiled_small_lse.py';text=helper.read_text();assert text.count('BUILD_HASH_PENDING')==1;helper.write_text(text.replace('BUILD_HASH_PENDING',hashlib.sha256((P/'reduction.so').read_bytes()).hexdigest()))
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as baseline
from tradingagents.research.onchain_replication.contracts import AttributedGraph
prefix='tradingagents.research.onchain_replication.'
def load(name,file):
 spec=importlib.util.spec_from_file_location(prefix+name,P/file);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
helper=load('compiled_small_lse','compiled_small_lse.py');candidate=load('_prototype_phase02','matching_annealing.py');assert helper._fn is not None
s=(P/'matching_annealing.py').read_text().replace('from .compiled_small_lse import lse as _compiled_lse\n','')
for arg in ['block,axis=1,keepdims=True','padded,axis=0,keepdims=True','block,axis=0,keepdims=True']:s=s.replace('_compiled_lse('+arg+',fallback=logsumexp)','logsumexp('+arg+')')
assert s==(ROOT/'tradingagents/research/onchain_replication/matching_annealing.py').read_text()
config=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching.json').read_text())
def graph(n,offset):
 ids=tuple('n'+str(i) for i in range(n));return AttributedGraph(ids,np.array([[.13*i+offset,.17*i-offset] for i in range(n)]),np.array([(i,(i+1)%n) for i in range(n)],dtype=np.int64).T.copy(),np.array([[.11*i+offset] for i in range(n)]),'a'*64,ids[0])
a,b=graph(2,.03),graph(3,.09);x=baseline.create(a,b,config,max_state_bytes=1048576,max_chunk_entries=4);y=candidate.create(a,b,config,max_state_bytes=1048576,max_chunk_entries=4)
steps=0;checkpoint=None;maxerror=0.;bits=True;counts={'compiled_calls':0}
# Observe actual executed Python call line, without altering functions/arguments.
def trace(frame,event,arg):
 if event=='line' and frame.f_code is helper.lse.__code__ and frame.f_lineno==nextline:counts['compiled_calls']+=1
 return trace
nextline=next(i for i,line in enumerate((P/'compiled_small_lse.py').read_text().splitlines(),1) if 'status=_fn(' in line)
sys.settrace(trace)
try:
 while x['phase']!='done':
  ux=baseline.advance(x,a,b,config,max_operations=1);uy=candidate.advance(y,a,b,config,max_operations=1);steps+=1;assert ux==uy
  for key in baseline.META:assert x[key]==y[key],key
  for key in baseline.NAMES:
   error=float(np.max(np.abs(x[key]-y[key])));maxerror=max(maxerror,error);bits &= x[key].tobytes()==y[key].tobytes();assert error<=1e-12
  if checkpoint is None and x['phase']=='normalize_columns':
   left=baseline.save(x,P/'checkpoint-baseline',a,b,config,max_checkpoint_bytes=1048576);right=candidate.save(y,P/'checkpoint-candidate',a,b,config,max_checkpoint_bytes=1048576)
   assert left==right;checkpoint=left
   x=baseline.load(P/'checkpoint-baseline',a,b,config,expected_sha256=left,max_state_bytes=1048576,max_chunk_entries=4)
   y=candidate.load(P/'checkpoint-candidate',a,b,config,expected_sha256=right,max_state_bytes=1048576,max_chunk_entries=4)
finally:sys.settrace(None)
assert counts['compiled_calls']>0
rx=baseline.result(x,a,b,config);ry=candidate.result(y,a,b,config);assert np.array_equal(rx.assignment,ry.assignment) and abs(rx.score-ry.score)<=1e-12
# Known underflow witness enters genuine normalize_rows; original partial state and error retained.
u=graph(2,.03);v=graph(2,.09);errors=[]
for module in (baseline,candidate):
 st=module.create(u,v,config,max_state_bytes=1048576,max_chunk_entries=4);st.update(phase='normalize_rows',cursor=0);st['M'][:]=[[0.,1000.],[1000.,0.]]
 with np.errstate(under='raise'):
  try:module.advance(st,u,v,config,max_operations=1)
  except FloatingPointError as e:errors.append({'type':type(e).__name__,'message':str(e),'safe':st['safe'],'cursor':st['cursor'],'bytes':st['M'].tobytes().hex()})
  else:raise AssertionError('underflow incorrectly suppressed')
assert errors[0]==errors[1] and errors[0]['safe'] is False
# Explicit unsupported errstate/magnitude/missing library/function ABI fallback.
fallbacks=[]
for mode in ('under_raise','magnitude','missing_library','abi'):
 block=np.array([[.1,.2],[.3,.4]]);oldpath=helper._PATH;oldargs=list(helper._fn.argtypes)
 try:
  if mode=='magnitude':block[0,0]=1000.
  if mode=='missing_library':helper._PATH=P/'absent.so'
  if mode=='abi':helper._fn.argtypes=[]
  with np.errstate(under='raise' if mode=='under_raise' else 'ignore'):
   expected=baseline.logsumexp(block,axis=1,keepdims=True);actual=helper.lse(block,axis=1,keepdims=True,fallback=baseline.logsumexp);assert expected.tobytes()==actual.tobytes()
  fallbacks.append(mode)
 finally:helper._PATH=oldpath;helper._fn.argtypes=oldargs
result={'status':'PASS_CONNECTED_FINITE_PROTOTYPE_ONLY','advances':steps,**counts,'all_soft_state_bits_equal':bits,'max_state_abs_difference':maxerror,'checkpoint_hash':checkpoint,'assignments_equal':True,'score_abs_difference':abs(rx.score-ry.score),'iterations':ry.iterations,'underflow_original_and_candidate':errors,'fallbacks':fallbacks,'elapsed_ns':time.monotonic_ns()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss};(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
