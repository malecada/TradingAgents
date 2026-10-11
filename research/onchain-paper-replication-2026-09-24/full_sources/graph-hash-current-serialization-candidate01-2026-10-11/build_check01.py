import ast,copy,difflib,hashlib,json,resource,signal,types,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(20)
R=Path.cwd();P=Path(__file__).resolve().parent;S=R/'tradingagents/research/onchain_replication';F=P.parent;refs={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();assert len(b)<2097152;refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b.decode()
def ck(v,n):assert v,n;checks.append(n)
accepted=read(F/'authority-current-pins-serialization02-2026-10-11/imported_mcm_identity.py');tree=ast.parse(accepted);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_current_bytes');helper=ast.get_source_segment(accepted,fn).replace('def _current_bytes(value):','def current_canonical_bytes(value):',1)
read(F/'authority-current-pins-serialization-review02-2026-10-11/REPORT.md')
oldp=read(S/'provenance.py');oldn=read(S/'neighborhoods.py')
newp=oldp.replace('\n\ndef digest(value: bytes)', '\n\n'+helper+'\n\n\ndef digest(value: bytes)',1)
start=oldn.index('def graph_hash(graph):');end=oldn.index('\n\nclass NeighborhoodIndex:',start);block=oldn[start:end];newblock=block.replace('    from .provenance import canonical_bytes\n','    from .provenance import current_canonical_bytes as canonical_bytes\n',1);ck(newblock!=block,'single graph hash serializer selection')
newn=oldn[:start]+newblock+oldn[end:]
for name,old,new in [('provenance.py',oldp,newp),('neighborhoods.py',oldn,newn)]:
 (P/name).write_text(new)
 for suffix,a,b,pa,pb in [('patch',old,new,S/name,P/name),('inverse.patch',new,old,P/name,S/name)]:
  (P/(name+'.'+suffix)).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(pa.relative_to(R)),tofile=str(pb.relative_to(R)))))
ck(newp.replace('\n\n'+helper+'\n','',1)==oldp,'provenance exact literal inverse')
ck(newn.replace('    from .provenance import current_canonical_bytes as canonical_bytes\n','    from .provenance import canonical_bytes\n',1)==oldn,'graph route exact literal inverse')
# Exact accepted helper reuse, name change only.
nf=next(n for n in ast.parse(newp).body if isinstance(n,ast.FunctionDef) and n.name=='current_canonical_bytes');nf.name='_current_bytes';ck(ast.dump(nf,include_attributes=False)==ast.dump(fn,include_attributes=False),'accepted02 helper AST identical except public shared name')
# Unchanged graph body except local imported symbol; validation/traversal/h.update call order is identical.
nt=ast.parse(newn);ot=ast.parse(oldn);gf=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='graph_hash');og=next(n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name=='graph_hash')
imp=next(n for n in gf.body if isinstance(n,ast.ImportFrom) and n.module=='provenance');imp.names=[ast.alias(name='canonical_bytes')];ck(ast.dump(nt,include_attributes=False)==ast.dump(ot,include_attributes=False),'entire neighborhoods AST inverse including validate and sorting unchanged')
# Extract only canonical/thaw/fresh helper: never import graph engine or scientific modules.
ns={'json':json};nodes=[n for n in ast.parse(newp).body if isinstance(n,ast.FunctionDef) and n.name in {'canonical_bytes','thaw','current_canonical_bytes'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-provenance-functions','exec'),ns);old=ns['canonical_bytes'];new=ns['current_canonical_bytes']
# Emitted graph chunks: narrow row blocks, flat IDs, keys/scalars, including unicode and signed zero.
chunks=[[[float(i)/8,-0.0,int(i)] for i in range(341)],['α','雪','quote"','slash\\','\n'],tuple(range(1024)),[],[[],[]],{'z':(1,True,None),'α':[2.5]},'edge_index',None]
for i,v in enumerate(chunks):ck(new(v)==old(v),'exact fresh chunk bytes '+str(i))
# Graph feed list framing reuses exactly [1:-1] chunks; verify full emitted bytes+digest.
for value,width in [(list(range(2050)),1024),([[i,-0.0] for i in range(1025)],512)]:
 def emit(encoder):return b'['+b','.join(encoder(value[i:i+width])[1:-1] for i in range(0,len(value),width))+b']'
 ck(emit(new)==emit(old)==old(value) and sha(emit(new))==sha(emit(old)),'exact multichunk framing/hash '+str(width))
from collections.abc import Mapping
class Custom(Mapping):
 def __iter__(self):return iter(['k'])
 def __len__(self):return 1
 def __getitem__(self,k):return [1,2]
class String(str):pass
fallback=[types.MappingProxyType({'x':[1]}),Custom(),[String('abc')],{1:'numeric-key'},[object()],[float('nan')],[float('inf')]]
def outcome(f,v):
 try:return ('bytes',f(v))
 except Exception as e:return (type(e).__name__,str(e))
for i,v in enumerate(fallback):ck(outcome(new,v)==outcome(old,v),'original unsupported/frozen/error bytes or refusal '+str(i))
# Verify unsupported delegates the original object, not copied or silently coerced.
real=ns['canonical_bytes'];seen=[]
def spy(v):seen.append(v);return real(v)
ns['canonical_bytes']=spy;v=Custom();ck(new(v)==old(v) and seen==[v] and seen[0] is v,'unsupported original object fallback');seen.clear();new([[1,2],[3,4]]);ck(not seen,'plain emitted lists avoid thaw copy');ns['canonical_bytes']=real
v=[[1,2],[3,4]];pin=new(v);v[1][0]=9;ck(new(v)==old(v)!=pin,'fresh nested mutation observed');v[1][0]=3;ck(new(v)==pin,'restoration exact')
# Very small bounded component timing; no graph/native/performance inference.
value=[[float(i)/8,-0.0,i] for i in range(341)];samples={k:[] for k in ['original','candidate']}
for rep in range(3):
 for name,f in [('original',old),('candidate',new)]:
  begin=time.perf_counter_ns()
  for _ in range(30):f(value)
  samples[name].append(time.perf_counter_ns()-begin)
result={'status':'PASS_FOCUSED_STDLIB_CHUNK_DIFFERENTIAL','checks':checks,'references':refs,'candidate_sources':{name:sha((P/name).read_bytes()) for name in ['provenance.py','neighborhoods.py']},'component_measurement':{'classification':'SYNTHETIC_EMITTED_PLAIN_CHUNK_ONLY','calls_per_sample':30,'scalars_per_chunk':1023,'wall_ns_samples':samples},'full_graph_native_proof':False,'actual_pilot_speed_or_memory_savings':None,'source_installation':False}
(P/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(checks),'candidate_sources':result['candidate_sources'],'component_measurement':result['component_measurement']}))
