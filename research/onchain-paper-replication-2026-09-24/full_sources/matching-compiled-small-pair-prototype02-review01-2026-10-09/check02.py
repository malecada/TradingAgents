import os,resource,signal,sys,json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.parent/'matching-compiled-small-pair-prototype02-2026-10-09';ROOT=Path.cwd()
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)):resource.setrlimit(k,(v,v))
signal.alarm(30)
(R/'LIMITS02.json').write_text(json.dumps({'affinity':list(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'threads':{k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}})+'\n')
sys.path.insert(0,str(ROOT))
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as old
from tradingagents.research.onchain_replication.contracts import AttributedGraph
prefix='tradingagents.research.onchain_replication.'
def load(name,filename):
 spec=importlib.util.spec_from_file_location(prefix+name,P/filename);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
helper=load('compiled_small_lse','compiled_small_lse.py');new=load('_review_compiled02','matching_annealing.py');native=helper._fn;assert native is not None
# Transparent counting proxy carries exact ABI attributes and forwards every native call.
# Both identity pins are deliberately rebound in this isolated observer fixture.
class Counter:
 def __init__(self):self.argtypes=native.argtypes;self.restype=native.restype;self.count=0;self.errstates=[]
 def __call__(self,*args):self.count+=1;self.errstates.append(np.geterr());return native(*args)
counter=Counter();helper._fn=helper._ORIGINAL_FN=counter
config=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching.json').read_bytes())
def graph(n,offset):
 ids=tuple('r'+str(i) for i in range(n));return AttributedGraph(ids,np.array([[offset+.21*i,.09*i] for i in range(n)]),np.array([(i,(i+1)%n) for i in range(n)],dtype=np.int64).T.copy(),np.array([[offset+.14*i] for i in range(n)]),'b'*64,ids[0])
a,b=graph(3,.04),graph(4,.11);x=old.create(a,b,config,max_state_bytes=1048576,max_chunk_entries=8);y=new.create(a,b,config,max_state_bytes=1048576,max_chunk_entries=8);steps=0;err=0.;bits=True
while x['phase']!='done':
 assert old.advance(x,a,b,config,max_operations=1)==new.advance(y,a,b,config,max_operations=1);steps+=1
 for key in old.META:assert x[key]==y[key]
 for key in old.NAMES:
  err=max(err,float(np.max(np.abs(x[key]-y[key]))));bits &= x[key].tobytes()==y[key].tobytes();assert err<=1e-12
rx=old.result(x,a,b,config);ry=new.result(y,a,b,config);assert np.array_equal(rx.assignment,ry.assignment) and abs(rx.score-ry.score)<=1e-12 and rx.iterations==ry.iterations and rx.convergence==ry.convergence
fullcalls=counter.count;assert fullcalls>0
block=np.array([[.1,.2],[.3,.4]])
with np.errstate(under='raise'):
 before=counter.count;got=helper.lse(block,axis=1,keepdims=True,fallback=old.logsumexp);assert counter.count==before and got.tobytes()==old.logsumexp(block,axis=1,keepdims=True).tobytes()
(R/'RESULT02.json').write_text(json.dumps({'shape':[3,4],'chunk':8,'max_operations':1,'advances':steps,'actual_native_invocations':fullcalls,'native_entry_errstate':counter.errstates[0],'all_native_errstates_equal':all(e==counter.errstates[0] for e in counter.errstates),'all_state_bits_equal':bits,'max_state_abs':err,'iterations':ry.iterations,'score_abs':abs(rx.score-ry.score),'under_raise_fallback_no_native_call':True,'instrumentation_qualification':'Counting proxy replaces both local function identity pins only in isolated synthetic process; native ABI arguments and call behavior forwarded unchanged. No line-event inference.'},indent=2)+'\n')
