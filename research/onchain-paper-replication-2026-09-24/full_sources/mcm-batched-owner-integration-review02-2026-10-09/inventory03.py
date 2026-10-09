import ast,hashlib,json,os,stat,types,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;R=H.parents[3];C=H.parent/'mcm-batched-owner-integration02-2026-10-09'
def extract(path,names,ns):
 nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
ns={'json':json,'hashlib':hashlib,'META_LIMIT':8192};extract(R/'tradingagents/research/onchain_replication/score_batches.py',{'_signature','_json','_require'},ns);io=types.SimpleNamespace(**{k:ns[k] for k in ('_signature','_json','_require')})
fds=[];primary=OSError('synthetic fdopen failure')
def opening(*a,**kw):
 fd=os.open(*a,**kw);fds.append(fd);return fd
def fdopen(*a,**kw):raise primary
proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.open=opening;proxy.fdopen=fdopen
ns={'os':proxy,'io':io,'require':io._require,'hashlib':hashlib,'stat':stat};extract(C/'compact_mcm_batched.py',{'_checkpoint_inventory'},ns)
p=H/'fdopen-fixture';p.mkdir();(p/'tiny').write_bytes(b'fixture')
try:ns['_checkpoint_inventory'](p)
except OSError as e:assert e is primary
else:raise AssertionError('no failure')
assert len(fds)==1;os.fstat(fds[0]);os.close(fds[0]);out={'fault':'inventory fdopen failure','primary_preserved':True,'file_descriptor_leaked':True,'reviewer_closed_synthetic_fd':True};(H/'INVENTORY03.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
