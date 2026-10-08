import ast,copy,hashlib,json,types
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-index-capacity02-2026-10-08';O=F/'real-data-pilot-index-capacity01-2026-10-07';H=Path(__file__).resolve().parent
checks=[];evidence={}
def read(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def check(n,v):
 assert v,n
 checks.append(n)
old=read(O/'candidate/index_capacity.py').decode();new=read(N/'candidate/index_capacity.py').decode()
before="set(numeric) == {'schema_version', 'max_buffer_bytes', 'edge_chunk', 'max_output_bytes', 'max_numeric_bytes'}"
after="set(numeric) in ({'schema_version', 'max_buffer_bytes', 'edge_chunk', 'max_output_bytes', 'max_numeric_bytes'}, {'schema_version', 'max_buffer_bytes', 'edge_chunk', 'max_output_bytes', 'max_numeric_bytes', 'extraction_limit'})"
block="    original_limit = dictionary['maximum_neighborhood_nodes']\n    limit = numeric.get('extraction_limit', original_limit); chunk = numeric['edge_chunk']\n    require(type(original_limit) is int and 0 < original_limit <= limit < 2**63, 'capacity extraction limit must preserve original minimum')\n"
inverse=new.replace(after,before).replace(block,"    limit = dictionary['maximum_neighborhood_nodes']; chunk = numeric['edge_chunk']\n")
check('exact_source_inverse',inverse==old);check('exact_ast_inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)))
module=types.ModuleType('capacity');exec(compile(new,'capacity','exec'),module.__dict__)
oldmodule=types.ModuleType('oldcapacity');exec(compile(old,'oldcapacity','exec'),oldmodule.__dict__)
tree=ast.parse(new);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect');stop=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='rows' for x in n.targets));guard=compile(ast.Module(body=fn.body[1:stop],type_ignores=[]),'<actual inspect guards>','exec')
base={'schema_version':1,'max_buffer_bytes':458003060,'edge_chunk':4096,'max_output_bytes':289981568,'max_numeric_bytes':747984628}
dictionary={'maximum_neighborhood_nodes':512,'size':32,'hop_depth':1}
def run(n,d=dictionary):
 env={'root':R,'Path':Path,'graph_inputs':{str(i):str(i) for i in range(7)},'numeric':n,'dictionary':d,'require':module.require};exec(guard,env);return env['limit']
check('default_dictionary_limit',run(base)==512);check('equal_explicit_limit',run(base|{'extraction_limit':512})==512);check('nondecreasing_limit',run(base|{'extraction_limit':350110})==350110)
for bad in (True,False,0,-1,511,512.0,'512',None,2**63):
 try:run(base|{'extraction_limit':bad})
 except ValueError:checks.append('override_refused_'+repr(bad))
 else:raise AssertionError(bad)
for bad in (True,0,-1,512.0,2**63):
 try:run(base|{'extraction_limit':350110},dictionary|{'maximum_neighborhood_nodes':bad})
 except ValueError:checks.append('dictionary_refused_'+repr(bad))
 else:raise AssertionError(bad)
for n in (base|{'extra':1},{k:v for k,v in base.items() if k!='max_buffer_bytes'},base|{'schema_version':True}):
 try:run(n)
 except ValueError:checks.append('schema_refused')
 else:raise AssertionError(n)
record=json.loads(read(N/'ACTUAL_HEADER_INSPECTION01.json'));validation=json.loads(read(N/'ACTUAL_HEADER_VALIDATION01.json'));required=record['required'];num=record['numeric'];calculated=[]
for row in required['graphs']:
 n=row['nodes'];e=row['edges'];chunk=num['edge_chunk'];lim=num['extraction_limit']
 # Independent algebra for fixed authenticated feature widths 32/16.
 output=32*(min(n,lim)+e);additive=32*e+60*n+56+160*chunk
 independent={'retained_index_bytes':16*(e+n+1),'index_additive_bytes':additive,'maximum_single_neighborhood_array_bytes':output,'output_inclusive_buffer_bytes':96*e+60*n+56+160*chunk+64*min(n,lim),'mcm_output_bytes':128*n}
 check('recorded_scalar_demand_'+row['graph_hash'],all(row[k]==v for k,v in independent.items()))
 check('actual_demand_'+row['graph_hash'],module.demand(n,e,32,16,chunk,lim)==independent)
 check('default_demand_equal_'+row['graph_hash'],module.demand(n,e,32,16,chunk,512)==oldmodule.demand(n,e,32,16,chunk,512))
 calculated.append(independent)
maximum=max(x['output_inclusive_buffer_bytes'] for x in calculated);out=max(x['mcm_output_bytes'] for x in calculated)
check('minimum_buffer',maximum==461349748==required['max_buffer_required']==validation['max_buffer_required'])
check('unchanged_output',out==289981568==num['max_output_bytes'])
check('minimum_numeric',maximum+out==751331316)
check('equal_delta',maximum-num['max_buffer_bytes']==maximum+out-num['max_numeric_bytes']==3346688)
# Static dependency proof; no preparation/admission or scientific reads.
prefix=F/'real-data-pilot-fixed20-metadata-successor01-2026-10-08/candidate'
for file in ('prepare_builder04.py','residuals04.py','controls02.py'):
 text=read(prefix/file).decode();check('no_numeric_buffer_dependency_'+file,not any(x in text for x in ('max_buffer_bytes','max_numeric_bytes')))
read(prefix/'build_inputs04.py');read(R/'tradingagents/research/onchain_replication/real_pilot_reservations.py')
result={'decision':'accepted-source-only','evidence':evidence,'checks':checks,'required_selection':{'max_buffer_bytes':maximum,'max_numeric_bytes':maximum+out,'max_output_bytes':out,'increase_each':3346688},'implications':'Only the two MCM numeric declarations need a minimum3346688-byte increase. Compact pair/checkpoint/live/replay/control/selected-input reservations and prefix04 disk categories do not depend on these two memory values and require no increase from this correction alone. Graph dimensions, extraction_limit350110, edge_chunk4096, output limit, typed/archive/transport/native/storage caps remain unchanged. New exact policy pin and helper pin must propagate to preparation, gate, preflight and source closure. Not peak-RSS or total-memory feasibility proof.','qualification':'Actual saved scalar/header report reviewed without rereading scientific arrays or NPY headers. No numerical imports, admission, owner, claim, native job, budget adoption or failed scientific classification. Original preclaim refusal and source01 remain preserved.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))
