import ast,builtins,copy,difflib,hashlib,json,resource,signal,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(20)
R=Path.cwd();P=Path(__file__).resolve().parent;F=P.parent;S=R/'tradingagents/research/onchain_replication';A=F/'authority-current-pins-serialization02-2026-10-11';G=F/'graph-hash-current-serialization-candidate01-2026-10-11';checks=[];refs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();assert len(b)<2097152;refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b.decode()
def ck(v,n):assert v,n;checks.append(n)
for directory in [A,G]:
 m=json.loads(read(directory/'MANIFEST01.json'))
 for name,pin in m['files'].items():
  if name in ['imported_mcm_identity.py','provenance.py','neighborhoods.py']:ck(sha(read(directory/name).encode())==pin['sha256'],'candidate dependency '+name)
read(F/'authority-current-pins-serialization-review02-2026-10-11/REPORT.md')
accepted=read(A/'imported_mcm_identity.py');tree=ast.parse(accepted);helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_current_bytes');segment=ast.get_source_segment(accepted,helper)
# Remove the local duplicate; select the existing shared provenance helper explicitly.
combined=accepted.replace(segment+'\n\n\n','',1).replace('from .provenance import canonical_bytes,thaw,file_hash','from .provenance import canonical_bytes,thaw,file_hash,current_canonical_bytes',1).replace('_current_bytes(', 'current_canonical_bytes(')
base={name:read(S/name) for name in ['provenance.py','neighborhoods.py','imported_mcm_identity.py']};candidate={'provenance.py':read(G/'provenance.py'),'neighborhoods.py':read(G/'neighborhoods.py'),'imported_mcm_identity.py':combined}
# Exact baseline imported adapter is recovered from accepted independent candidate.
restored=combined.replace(',current_canonical_bytes\n','\n',1).replace('current_canonical_bytes(', 'canonical_bytes(')
ck(restored==base['imported_mcm_identity.py'],'identity exact baseline literal inverse')
for name in candidate:
 (P/name).write_text(candidate[name])
 for suffix,a,b,pa,pb in [('patch',base[name],candidate[name],S/name,P/name),('inverse.patch',candidate[name],base[name],P/name,S/name)]:
  (P/(name+'.'+suffix)).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(pa.relative_to(R)),tofile=str(pb.relative_to(R)))))
ck(candidate['provenance.py']==read(G/'provenance.py') and candidate['neighborhoods.py']==read(G/'neighborhoods.py'),'graph/provenance candidate bytes unchanged')
# Exact accepted adapter AST after deleting its helper and renaming three references/import.
ta=ast.parse(accepted);ta.body=[n for n in ta.body if not (isinstance(n,ast.FunctionDef) and n.name=='_current_bytes')]
for n in ast.walk(ta):
 if isinstance(n,ast.Name) and n.id=='_current_bytes':n.id='current_canonical_bytes'
for n in ta.body:
 if isinstance(n,ast.ImportFrom) and n.module=='provenance':n.names.append(ast.alias(name='current_canonical_bytes'))
ck(ast.dump(ta,include_attributes=False)==ast.dump(ast.parse(combined),include_attributes=False),'entire accepted identity adapter AST relocation only')
ck(combined.count('current_canonical_bytes(')==3 and 'def _current_bytes' not in combined,'one shared helper three pin calls no duplicate')
# Source-only import/export join, no package or graph engine import.
pt=ast.parse(candidate['provenance.py']);shared=next(n for n in pt.body if isinstance(n,ast.FunctionDef) and n.name=='current_canonical_bytes');same=copy.deepcopy(shared);same.name='_current_bytes';ck(ast.dump(same,include_attributes=False)==ast.dump(helper,include_attributes=False),'shared helper exact accepted02 AST')
ns={'json':json};nodes=[n for n in pt.body if isinstance(n,ast.FunctionDef) and n.name in ['canonical_bytes','thaw','current_canonical_bytes']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'extracted-canonical-functions','exec'),ns)
oldns=dict(ns);exec(compile(ast.Module(body=[helper],type_ignores=[]),'accepted-private-helper','exec'),oldns)
def require(v,msg):
 if not v:raise ValueError(msg)
def extracted_pins(source,env):
 klass=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='Target');fn=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='_pins');scope={**env,'require':require};exec(compile(ast.Module(body=[fn],type_ignores=[]),'extracted-pins-no-authority','exec'),scope);return scope['_pins']
a=extracted_pins(accepted,oldns);b=extracted_pins(combined,ns)
def fixture():
 n=types.SimpleNamespace;owner=object();dictionary=object();graph=object();mapping={'g':'input'};stage=n(reference='receipt',prepared=n(_selection={'selected':{'descriptor':{'resource_graph_inputs':mapping}}}));execution=n(_owner=owner,_materialized=n(_dictionary=dictionary),_stage=stage)
 t=n(execution=execution,graph=graph,owner=owner,dictionary=dictionary,receipt_sha256='receipt',key='g',_input='input',_execution={'nested':[1,2]},scope={'g':'scope'},_arrays=lambda:('scalar-placeholder',))
 t._objects=(id(execution),id(graph),id(owner),id(dictionary),t._arrays());t._mapping=ns['canonical_bytes'](mapping);t._execution_pin=ns['canonical_bytes'](t._execution);t._scope_pin=ns['canonical_bytes'](t.scope);return t
mutations=[lambda t:None,lambda t:t._execution['nested'].append(3),lambda t:t.scope.update(g='changed'),lambda t:t.execution._stage.prepared._selection['selected']['descriptor']['resource_graph_inputs'].update(g='other'),lambda t:setattr(t,'graph',object())]
def outcome(f,t):
 try:return f(t)
 except Exception as e:return type(e).__name__,str(e)
for i,mutation in enumerate(mutations):
 x=fixture();y=fixture();mutation(x);mutation(y);ck(outcome(a,x)==outcome(b,y),'accepted vs shared _pins byte/refusal '+str(i))
t=fixture();b(t);t._execution['nested'].append(3);ck(outcome(b,t)==('ValueError','target execution/workload changed'),'fresh mutation refusal');t._execution['nested'].pop();ck(b(t) is None,'fresh restoration passes')
values=[[[1,-0.0,None],[2.5,True,'雪']],types.MappingProxyType({'x':(1,2)}),{1:'key'},[object()],[float('nan')]]
for i,v in enumerate(values):
 ck(outcome(oldns['_current_bytes'],v)==outcome(ns['current_canonical_bytes'],v),'shared helper bytes/error same accepted '+str(i))
result={'status':'PASS_FOCUSED_SHARED_IMPORT_CALLSITE_INTEGRATION','checks':checks,'references':refs,'candidate_sources':{k:sha(v.encode()) for k,v in candidate.items()},'classification':'STDLIB_EXTRACTED_FUNCTIONS_AND_SYNTHETIC_SCALAR_PIN_OBJECTS_ONLY','actual_authority_instantiated':False,'actual_graph_native_proof':False,'performance_claim':None,'installed':False}
(P/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(checks),'candidate_sources':result['candidate_sources']}))
