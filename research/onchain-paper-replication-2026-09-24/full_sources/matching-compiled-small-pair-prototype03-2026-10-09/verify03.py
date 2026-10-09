import os,sys,resource,signal,time,json,subprocess,hashlib,importlib.util,ast,statistics,fcntl,errno
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];OLD=P.parent/'matching-compiled-small-pair-prototype02-2026-10-09';sys.path.insert(0,str(ROOT))
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.alarm(30);started=time.monotonic_ns();receipt={'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':30};(P/'LIMITER03.json').write_text(json.dumps(receipt,indent=2)+'\n');assert receipt['affinity']==[3]
cmd=['/usr/bin/cc','-std=c11','-O3','-fno-fast-math','-ffp-contract=off',str(P/'probe03.c'),'-o',str(P/'probe03')]
t=time.monotonic_ns();r=subprocess.run(cmd,capture_output=True,text=True);compile_ns=time.monotonic_ns()-t
(P/'PROBE_COMPILE03.json').write_text(json.dumps({'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'elapsed_ns':compile_ns},indent=2)+'\n');assert r.returncode==0
probe=subprocess.run([str(P/'probe03')],capture_output=True,text=True);(P/'PROBE03.json').write_text(probe.stdout);assert probe.returncode==0
constants=json.loads(probe.stdout)
assert constants=={'F_ADD_SEALS':1033,'F_GET_SEALS':1034,'F_SEAL_WRITE':8,'F_SEAL_GROW':4,'F_SEAL_SHRINK':2,'F_SEAL_SEAL':1,'MFD_CLOEXEC':1,'MFD_ALLOW_SEALING':2}
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as base
from tradingagents.research.onchain_replication.contracts import AttributedGraph
PREFIX='tradingagents.research.onchain_replication.'
def load(name,path):
 spec=importlib.util.spec_from_file_location(PREFIX+name,path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;
 diagnostics=[]
 def trace(frame,event,arg):
  if frame.f_code.co_name=='_load_sealed':
   if event=='exception':diagnostics.append({'line':frame.f_lineno,'type':arg[0].__name__,'message':str(arg[1])})
   if event=='return' and arg is None:diagnostics.append({'return_none_line':frame.f_lineno})
  return trace
 sys.settrace(trace)
 try:spec.loader.exec_module(m)
 finally:sys.settrace(None)
 if diagnostics:
  print('LOADER_DIAGNOSTICS',name,diagnostics,flush=True)
  (P/(name+'-diagnostic03.json')).write_text(json.dumps(diagnostics,indent=2)+'\n')
 return m
setup={}
for label,directory in [('02',OLD),('03',P)]:
 t=time.perf_counter_ns();h=load('compiled_small_lse',directory/'compiled_small_lse.py');a=load('_phase_'+label,directory/'matching_annealing.py');setup[label]={'elapsed_ns':time.perf_counter_ns()-t}
 if label=='02':h2,a2=h,a
 else:h3,a3=h,a
assert h3._live() and h3._fn is not None
setup['03'].update(fd=h3._fd,pin=h3._pin,seals=fcntl.fcntl(h3._fd,h3._F_GET_SEALS),required_seals=h3._SEALS,body_sha256=hashlib.sha256(os.pread(h3._fd,65536,0)).hexdigest())
assert (P/'matching_annealing.py').read_bytes()==(OLD/'matching_annealing.py').read_bytes();assert (P/'reduction.c').read_bytes()==(OLD/'reduction.c').read_bytes()
config=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching.json').read_text())
def graph(n,off):
 ids=tuple('n'+str(i) for i in range(n));return AttributedGraph(ids,np.array([[.13*i+off,.17*i-off] for i in range(n)]),np.array([(i,(i+1)%n) for i in range(n)],dtype=np.int64).T.copy(),np.array([[.11*i+off] for i in range(n)]),'a'*64,ids[0])
g1,g2=graph(2,.03),graph(3,.09)
def create(module):return module.create(g1,g2,config,max_state_bytes=1048576,max_chunk_entries=4)
# Count the exact invocation statement once by inserting one test-only AST increment.
# This avoids the old multi-line tracer overcount; pristine functions restored before timings.
def instrument(h):
 tree=ast.parse(Path(h.__file__).read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='lse');new=[]
 for n in f.body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='status' for t in n.targets):new.extend(ast.parse("_test_calls[0]+=1").body)
  new.append(n)
 f.body=new;ns=h.__dict__;ns['_test_calls']=[0];original=h.lse;exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'test-only-call-counter','exec'),ns);return original
orig2=instrument(h2);orig3=instrument(h3);a2._compiled_lse=h2.lse;a3._compiled_lse=h3.lse
states=[create(m) for m in (base,a2,a3)];steps=0;checkpoint=None;maxdiff=0.;bits=True
while states[0]['phase']!='done':
 used=[m.advance(st,g1,g2,config,max_operations=1) for m,st in zip((base,a2,a3),states)];assert len(set(used))==1;steps+=1
 for st in states[1:]:
  for k in base.META:assert st[k]==states[0][k]
  for k in base.NAMES:
   err=float(np.max(np.abs(st[k]-states[0][k])));maxdiff=max(maxdiff,err);assert err<=1e-12;bits &= st[k].tobytes()==states[0][k].tobytes()
 if checkpoint is None and states[0]['phase']=='normalize_columns':
  hashes=[]
  for label,m,st in zip(('original','02','03'),(base,a2,a3),states):hashes.append(m.save(st,P/('checkpoint-'+label),g1,g2,config,max_checkpoint_bytes=1048576))
  assert len(set(hashes))==1;checkpoint=hashes[0]
  states=[m.load(P/('checkpoint-'+label),g1,g2,config,expected_sha256=checkpoint,max_state_bytes=1048576,max_chunk_entries=4) for label,m in zip(('original','02','03'),(base,a2,a3))]
results=[m.result(st,g1,g2,config) for m,st in zip((base,a2,a3),states)];assert all(np.array_equal(results[0].assignment,r.assignment) and abs(results[0].score-r.score)<=1e-12 for r in results)
counts={'02':h2._test_calls[0],'03':h3._test_calls[0]};assert counts['02']==counts['03']>0
h2.lse=orig2;h3.lse=orig3;a2._compiled_lse=orig2;a3._compiled_lse=orig3
# Connected timing includes normal create/check/advance/result; excludes checkpoint filesystem I/O.
def match(m):
 st=create(m)
 while st['phase']!='done':m.advance(st,g1,g2,config,max_operations=100000)
 return m.result(st,g1,g2,config)
timings={}
for label,m in [('original',base),('02',a2),('03',a3)]:
 samples=[]
 for _ in range(5):
  t=time.perf_counter_ns()
  for __ in range(5):match(m)
  samples.append((time.perf_counter_ns()-t)/5)
 timings[label]={'ns_per_match':samples,'median_ns':statistics.median(samples)}
# Kernel blocks writes and extent mutation; source pathname replacement cannot change sealed body.
refusals=[]
for name,op in [('write',lambda:os.pwrite(h3._fd,b'X',0)),('truncate',lambda:os.ftruncate(h3._fd,0)),('grow',lambda:os.ftruncate(h3._fd,h3._pin[2]+1))]:
 try:op()
 except OSError as e:assert e.errno==errno.EPERM;refusals.append(name)
 else:raise AssertionError('seal failed '+name)
q=np.array([[.1,.2],[.3,.4]]);expected=h3.lse(q,axis=1,keepdims=True,fallback=base.logsumexp)
os.rename(P/'reduction.so',P/'reduction-original.so');(P/'reduction.so').write_bytes(b'not a library')
try:
 assert h3._live();assert h3.lse(q,axis=1,keepdims=True,fallback=base.logsumexp).tobytes()==expected.tobytes()
 bad=load('_bad_body03',P/'compiled_small_lse.py');assert bad._fn is None
finally:os.rename(P/'reduction.so',P/'reduction-tampered.fixture');os.rename(P/'reduction-original.so',P/'reduction.so')
# Unsupported kernel API closes its opened source fd and retains fallback.
old=h3._new_memfd;before=set(os.listdir('/proc/self/fd'))
def unsupported(*a,**k):raise OSError(errno.ENOSYS,'synthetic unavailable memfd')
h3._new_memfd=unsupported
try:assert h3._load_sealed() is None
finally:h3._new_memfd=old
assert before==set(os.listdir('/proc/self/fd'))
owned=h3._fd;h3.close();assert not h3._live();assert h3.lse(q,axis=1,keepdims=True,fallback=base.logsumexp).tobytes()==base.logsumexp(q,axis=1,keepdims=True).tobytes()
try:os.fstat(owned)
except OSError as e:assert e.errno==errno.EBADF
else:raise AssertionError('owned descriptor leaked')
result={'status':'PASS_FINITE_LIFETIME_PROTOTYPE_ONLY','setup':setup,'compile_ns':compile_ns,'advances':steps,'true_C_invocation_statement_counts':counts,'checkpoint_sha256':checkpoint,'all_state_bits_equal':bits,'max_abs_difference':maxdiff,'score_abs_difference':abs(results[0].score-results[2].score),'assignment_equal':True,'timings':timings,'original_over_03':timings['original']['median_ns']/timings['03']['median_ns'],'02_over_03':timings['02']['median_ns']/timings['03']['median_ns'],'kernel_seal_refusals':refusals,'source_replacement_existing_lifetime_unchanged':True,'new_load_wrong_hash_fallback':True,'unsupported_memfd_no_fd_leak':True,'close_fallback_fd_reaped':True,'elapsed_ns':time.monotonic_ns()-started,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss};(P/'RESULT03.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
