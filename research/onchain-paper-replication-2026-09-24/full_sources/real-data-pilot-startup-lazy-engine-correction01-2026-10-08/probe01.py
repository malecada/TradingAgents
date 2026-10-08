"""Cold import-only experiment. Never evaluates real inputs or numerical arrays."""
import os,resource,sys
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
import ast,importlib.util,json,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R))
def audit(event,args):
 if event=='import' and args[0].split('.')[0]=='torch':raise RuntimeError('Torch import prohibited')
 if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('network prohibited')
 if event=='open' and isinstance(args[0],str):
  p=Path(args[0])
  if any(x in p.parts for x in ('keys','apis','research_artifacts','research_runs','data')) or p.name in ('.env','hf_token.txt'):raise RuntimeError('original data/credential reads prohibited')
sys.addaudithook(audit)
def memory():
 fields={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  if line.startswith(('Rss:','Pss:','Private_Clean:','Private_Dirty:')):
   k,v,*_=line.split();fields[k.rstrip(':')+'_bytes']=int(v)*1024
 fields['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
 return fields
mode=sys.argv[1];before=memory();start=time.monotonic()
import tradingagents.research.onchain_replication as package
full=package.__name__+'.matching_pair'
p=H/('matching_pair.py' if mode=='candidate' else 'baseline_matching_pair.py')
spec=importlib.util.spec_from_file_location(full,p);m=importlib.util.module_from_spec(spec);sys.modules[full]=m;setattr(package,'matching_pair',m)
if mode=='hypothesis':
 # Exploratory import-only ablation. Function bodies are never called here.
 tree=ast.parse(p.read_text());tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and any(a.asname=='engine' for a in n.names))]
 exec(compile(tree,str(p),'exec'),m.__dict__)
else:spec.loader.exec_module(m)
from tradingagents.research.onchain_replication import real_pilot_reservations
elapsed=time.monotonic()-start;after=memory()
value={'mode':mode,'import_only':True,'cpus':sorted(os.sched_getaffinity(0)),'rlimit_as':list(resource.getrlimit(resource.RLIMIT_AS)),'rlimit_fsize':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'elapsed_seconds':elapsed,'before':before,'after':after,'loaded_modules':sorted(sys.modules),'engine_loaded':package.__name__+'.matching_checkpoint' in sys.modules,'numpy_loaded':'numpy' in sys.modules,'scipy_special_loaded':'scipy.special' in sys.modules,'torch_loaded':'torch' in sys.modules}
print(json.dumps(value,sort_keys=True),flush=True)
if '--require-deferred' in sys.argv:
 assert not value['engine_loaded'],'metadata import eagerly loads matching_checkpoint'
 assert not value['scipy_special_loaded'],'metadata import eagerly loads scipy.special'
 assert value['numpy_loaded'],'remaining metadata NumPy import unexpectedly removed'
