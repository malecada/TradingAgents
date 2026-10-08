import ast,builtins,copy,hashlib,json,types
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'real-data-pilot-owner-policy-correction01-2026-10-08';H=Path(__file__).resolve().parent;MAIN=R/'tradingagents/research/onchain_replication'
evidence={};checks=[]
def read(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b.decode()
def check(n,v):
 assert v,n
 checks.append(n)
def need(v,msg):
 if not v:raise ValueError(msg)
new=read(C/'matching_owner.py');old=read(C/'baseline_matching_owner.py');check('exact_candidate_sha',hashlib.sha256(new.encode()).hexdigest()=='b7cb394c8c65a2d9688a9557c991a2e694b48fc0b3d2317f71a51c857680dfaa');check('baseline_exact_main',old==read(MAIN/'matching_owner.py'))
start=new.index('def _pair_limits(');end=new.index('def bind(',start);helpertext=new[start:end]
original="    require(isinstance(limits,dict) and set(limits)==matching_pair.POLICY_FIELDS and all(type(v) is int and v>0 for v in limits.values()),'pair limits differ')\n    require(limits['chunk_edges']<=65536,'pair edge chunk exceeds bound')\n"
inverse=(new[:start]+new[end:]).replace('    _pair_limits(limits, resource=_resource)\n',original)
check('exact_source_inverse',inverse==old);check('exact_ast_inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)))
# Exact pure validators extracted, including constants. Only relative imports of
# these exact extracted functions are allowed; numerical packages never load.
def selected(p,fnames,anames,env):
 tree=ast.parse(read(p));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in fnames or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in anames for t in n.targets)]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),env)
pair={};selected(MAIN/'matching_pair.py',set(),{'ENGINE_FIELDS','POLICY_FIELDS'},pair);pair=types.SimpleNamespace(**pair)
chunks={};selected(MAIN/'checkpoint_chunks.py',{'need','layout'},{'FORMAT','MAX_ENTRIES'},chunks);chunks=types.SimpleNamespace(**chunks)
compact={'pair':pair,'require':need,'copy':copy}
def importer(name,globals=None,locals=None,fromlist=(),level=0):
 if level==1 and name=='checkpoint_chunks':return chunks
 if level==1 and name=='compact_policy':return types.SimpleNamespace(pair_policy=compact['pair_policy'])
 raise AssertionError(('unexpected import',name,level))
compact['__builtins__']=dict(vars(builtins),__import__=importer)
selected(MAIN/'compact_policy.py',{'positive','pair_policy','effective_matching'},{'PAIR_CAPACITY_FIELD'},compact)
owner={'matching_pair':pair,'require':need,'__builtins__':dict(vars(builtins),__import__=importer)};exec(compile(helpertext,'<exact owner helper>','exec'),owner);validate=owner['_pair_limits']
oldcode=compile(original.strip().replace('\n    ','\n'),'<legacy guards>','exec')
policy=json.loads(read(F/'real-data-pilot-final20-2026-10-08/templates02/pair_policy01.json'))['limits'];other=json.loads(read(F/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json'))['stage_policy']['pair'];check('real_frozen_pair_compact_equal',policy==other)
before=copy.deepcopy(policy);validate(policy,resource=True);check('actual_optional_policy_preserved',policy==before)
legacy={k:v for k,v in policy.items() if k in pair.POLICY_FIELDS}
def result(fn,p):
 try:fn(p);return ('accepted',)
 except Exception as e:return (type(e).__name__,str(e))
def original_fn(p):exec(oldcode,{'require':need,'matching_pair':pair,'limits':p})
legacy_cases=[legacy,policy,legacy|{'chunk_edges':65537},legacy|{'max_state_bytes':0},legacy|{'max_state_bytes':True},{k:v for k,v in legacy.items() if k!='chunk_edges'},legacy|{'max_state_bytes':2**63}]
for i,p in enumerate(legacy_cases):check('legacy_outcome_identical_'+str(i),result(original_fn,p)==result(validate,p))
check('actual_legacy_optional_refusal',result(validate,policy)==('ValueError','pair limits differ'))
for k in ('checkpoint_layout','max_pair_entries_override'):
 p=legacy|{k:policy[k]};validate(p,resource=True);checks.append('single_optional_accepted_'+k)
for label,p in [('unknown',policy|{'other':1}),('missing',{k:v for k,v in policy.items() if k!='chunk_edges'}),('bool_override',policy|{'max_pair_entries_override':True}),('zero_override',policy|{'max_pair_entries_override':0}),('overflow_override',policy|{'max_pair_entries_override':2**63}),('negative_limit',policy|{'max_state_bytes':-1}),('edge_bound',policy|{'chunk_edges':65537}),('layout_extra',policy|{'checkpoint_layout':policy['checkpoint_layout']|{'other':1}}),('layout_bool',policy|{'checkpoint_layout':{'format':'sharded-npy-v1','chunk_entries':True}}),('layout_overflow',policy|{'checkpoint_layout':{'format':'sharded-npy-v1','chunk_entries':262145}})]:
 outcome=result(lambda p:validate(p,resource=True),p);check('resource_refusal_'+label,outcome[0]=='ValueError')
check('effective_capacity_preserved',compact['effective_matching']({'max_pair_entries':1024},policy)['max_pair_entries']==8402640)
check('downstream_decrease_still_refused',result(lambda p:compact['effective_matching']({'max_pair_entries':8402641},p),policy)[0]=='ValueError')
bind=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='bind');calls=[n for n in ast.walk(bind) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_pair_limits'];check('single_exact_bind_call',len(calls)==1 and ast.unparse(calls[0])=='_pair_limits(limits, resource=_resource)')
resource=read(MAIN/'resource_binding.py');check('resource_selector_true','_create=True,_first=True,_resource=True' in resource)
result={'schema_version':1,'decision':'accepted-source-only','candidate':{'path':str((C/'matching_owner.py').relative_to(R)),'sha256':evidence[str((C/'matching_owner.py').relative_to(R))]},'evidence':evidence,'checks':checks,'scope':'One resource-only schema adapter plus bind forwarding call. Exact frozen pair/compact policy accepted without mutation. Legacy guard behavior exactly preserved. Existing compact pair validator supplies optional schema/type/layout checks; downstream effective_matching still rejects decreasing capacity. No Binding, run, owner, graph, numerical package or job constructed. Not empirical admission, complete capacity proof or permission to retry failed20.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted-source-only','checks':len(checks),'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))
