import ast,types,json,hashlib,struct,os,resource,signal,time
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;P=F/'matching-adaptive-measurement-stack01-2026-10-09';V=F/'matching-adaptive-measurement-stack-review01-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)):resource.setrlimit(r,(v,v))
signal.alarm(30);start=time.monotonic_ns();(D/'LIMITER01.json').write_text(json.dumps({'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'wall_seconds':30},indent=2)+'\n')
def load(path,extra={}):
 t=ast.parse(path.read_text());t.body=[n for n in t.body if not isinstance(n,ast.ImportFrom) or not n.level];m=types.ModuleType(path.stem);m.__dict__.update(extra);exec(compile(t,str(path),'exec'),m.__dict__);return m
geometry=load(D/'geometry_summary.py');pub=load(D/'geometry_publication.py',{k:getattr(geometry,k) for k in ('BINS','NAMES','LIMIT','raw','require')});adaptive=load(D/'adaptive_edge_policy.py')
t=ast.parse((D/'matching_owner.py').read_text());nodes=[n for n in t.body if (isinstance(n,ast.FunctionDef) and n.name.startswith('binding_timing_')) or (isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and (x.id in ('_LEASE_TIMING_PHASES','_LEASE_TIMING_LIMIT','BINDING_TIMING_POLICY')) for x in n.targets))];mo=types.ModuleType('matching');mo.__dict__.update(json=json,require=geometry.require);exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_timing_validators','exec'),mo.__dict__)
extra={'geometry_publication':pub,'matching_owner':mo,'adaptive_edge_policy':adaptive};old=load(P/'batched_numeric_execution.py',extra);new=load(D/'batched_numeric_execution.py',extra)
for a,b in json.loads((D/'CHANGES01.json').read_text())['batched_numeric_execution.py']:
 text=(D/'batched_numeric_execution.py').read_text();assert text.count(b)==1 and text.replace(b,a)==(P/'batched_numeric_execution.py').read_text()
binding=json.loads((V/'ORIGINAL_BINDING01.json').read_text());root=V/'fixtures'/'combined'/'stream'
# Use existing actual producer fixture, no new numerical execution or authority.
if not root.exists():
 roots=list((V/'fixtures').glob('*/stream'));assert len(roots)==1;root=roots[0]
old.verify(root,binding);new.verify(root,binding)
bad=dict(binding);bad.pop('binding_timing');old.verify(root,bad)
try:new.verify(root,bad)
except ValueError as e:assert str(e)=='unselected binding timing counters'
else:raise AssertionError('downgrade accepted')
# Copy the original default producer bytes; rebuild only local storage pins.
r=D/'default';r.mkdir();bd=r/'numeric-batches';bd.mkdir();origin=(P/'fixtures/default/stream/numeric-origins.bin').read_bytes();body=(P/'fixtures/default/stream/numeric-batches/000000000000.json').read_bytes();(r/'numeric-origins.bin').write_bytes(origin);file=bd/'000000000000.json';file.write_bytes(body);s=json.loads(body);sig=new.sig
b=dict(binding)
for k in ('binding_timing','geometry','edge_cache_policy'):b.pop(k,None)
b.update(stream_inode=list(sig(r.stat())[:2]),batches_inode=list(sig(bd.stat())[:2]),batches_signature=list(sig(bd.stat())),origin_signature=list(sig((r/'numeric-origins.bin').stat())),origin_sha256=hashlib.sha256(origin).hexdigest(),summary_bytes=len(body),summary_sha256=hashlib.sha256(struct.pack('>Q',len(body))+body).hexdigest(),summary_inventory_sha256=hashlib.sha256(new.raw({'name':file.name,'signature':sig(file.stat())})).hexdigest(),counters=s['counters'],elapsed_seconds=s['elapsed_seconds'])
old.verify(r,b);new.verify(r,b)
for field in ('geometry','edge_cache_policy'):
 bad=dict(binding);bad.pop(field)
 try:new.verify(root,bad)
 except ValueError:pass
 else:raise AssertionError('other metadata join changed')
(D/'RESULT01.json').write_text(json.dumps({'status':'PASS_METADATA_ONLY','baseline_downgrade_accepted':True,'corrected_downgrade_refused':True,'selected_valid':True,'original_default_bytes_valid':True,'other_selection_joins_refuse':True,'elapsed_ns':time.monotonic_ns()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2)+'\n');print('PASS')
