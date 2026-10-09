import ast,types,json,hashlib,struct,os,resource,signal
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;C=F/'matching-adaptive-measurement-stack02-2026-10-09';P=F/'matching-adaptive-measurement-stack01-2026-10-09';V=F/'matching-adaptive-measurement-stack-review01-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(k,(v,v))
signal.alarm(30)
(D/'LIMITER01.json').write_text(json.dumps({'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'file':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'alarm':30},indent=2)+'\n')
def load(path,extra=None):
 tree=ast.parse(path.read_text());tree.body=[n for n in tree.body if not isinstance(n,ast.ImportFrom) or not n.level];ns={} if extra is None else dict(extra);exec(compile(tree,str(path),'exec'),ns);return types.SimpleNamespace(**ns)
g=load(C/'geometry_summary.py');pub=load(C/'geometry_publication.py',{k:getattr(g,k) for k in ('BINS','NAMES','LIMIT','raw','require')});ap=load(C/'adaptive_edge_policy.py')
t=ast.parse((C/'matching_owner.py').read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name.startswith('binding_timing_') or isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id in ('_LEASE_TIMING_PHASES','_LEASE_TIMING_LIMIT','BINDING_TIMING_POLICY') for a in n.targets)];ns={'json':json,'require':g.require};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_validators','exec'),ns)
extra={'matching_owner':types.SimpleNamespace(**ns),'geometry_publication':pub,'adaptive_edge_policy':ap};old=load(P/'batched_numeric_execution.py',extra);new=load(C/'batched_numeric_execution.py',extra)
b=json.loads((V/'ORIGINAL_BINDING01.json').read_text());root=V/'fixtures/combined/stream';old.verify(root,b);new.verify(root,b)
results=[]
for mode in ('missing','None','False'):
 bad=dict(b)
 if mode=='missing':bad.pop('binding_timing')
 else:bad['binding_timing']=None if mode=='None' else False
 old.verify(root,bad)
 try:new.verify(root,bad)
 except ValueError as e:assert str(e)=='unselected binding timing counters';results.append(mode)
 else:raise AssertionError('downgrade accepted')
# Original default bytes relocated only to review directory with accurate fresh filesystem pins.
r=D/'default';r.mkdir();bd=r/'numeric-batches';bd.mkdir();source=P/'fixtures/default/stream';origin=(source/'numeric-origins.bin').read_bytes();body=(source/'numeric-batches/000000000000.json').read_bytes();o=r/'numeric-origins.bin';s=bd/'000000000000.json';o.write_bytes(origin);s.write_bytes(body);o.chmod(0o600);s.chmod(0o600);row=json.loads(body)
bb=dict(b)
for field in ('binding_timing','geometry','edge_cache_policy'):bb.pop(field)
bb.update(stream_inode=list(new.sig(r.stat())[:2]),batches_inode=list(new.sig(bd.stat())[:2]),batches_signature=list(new.sig(bd.stat())),origin_signature=list(new.sig(o.stat())),origin_sha256=hashlib.sha256(origin).hexdigest(),summary_bytes=len(body),summary_sha256=hashlib.sha256(struct.pack('>Q',len(body))+body).hexdigest(),summary_inventory_sha256=hashlib.sha256(new.raw({'name':s.name,'signature':new.sig(s.stat())})).hexdigest(),counters=row['counters'],elapsed_seconds=row['elapsed_seconds'])
old.verify(r,bb);new.verify(r,bb)
(D/'RESULT01.json').write_text(json.dumps({'status':'PASS_METADATA_ONLY','selected_original_files_valid':True,'actual_old_accepts_new_refuses':results,'default_original_bytes_valid':True,'numerical_imports_or_recomputation':False},indent=2)+'\n');print('PASS',results)
