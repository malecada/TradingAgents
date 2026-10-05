"""Independent source/pure metadata checks; no scientific objects or numerical imports."""
import ast,copy,difflib,hashlib,importlib.util,json,subprocess,sys,types,weakref
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parents[2]
P=BASE/'financial-training-parent-retention-census01-2026-10-05';S=ROOT/'tradingagents/research/onchain_replication'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(n):return ast.dump(n,include_attributes=False)
raw=(P/'MANIFEST01.json').read_bytes();assert sha(raw)=='d048a9028231f18848c0a34d59db8bd62f058b5a7a60c41e08c1c3e7e0fc4e5d'
for name,r in json.loads(raw)['files'].items():
 body=(P/name).read_bytes();assert len(body)==r['bytes'] and sha(body)==r['sha256']
for name,pin in json.loads((P/'SOURCE_PINS01.json').read_text()).items():assert sha((S/name).read_bytes())==pin
old=(S/'training_batch_observer.py').read_text();new=(P/'training_batch_observer.py').read_text();assert sha(new.encode())=='2a498466909e35849318d8256f40d47f20b7e356dfc1f9ca47757e2f54cca057'
name='tradingagents/research/onchain_replication/training_batch_observer.py'
assert ''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name))==(P/'CHANGE01.patch').read_text()
assert ''.join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile='b/'+name,tofile='a/'+name))==(P/'INVERSE01.patch').read_text()
# Compile only, do not execute source imports, to verify the actual closure slot.
code=compile((S/'compact_terminal.py').read_text(),str(S/'compact_terminal.py'),'exec')
def codes(c):
 yield c
 for x in c.co_consts:
  if isinstance(x,types.CodeType):yield from codes(x)
verify=next(c for c in codes(code) if c.co_qualname=='finish.<locals>.verify')
assert verify.co_freevars.count('published')==1 and len(verify.co_freevars)<=64
spec=importlib.util.spec_from_file_location('reviewed_retention',P/'training_batch_observer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
policy=dict(kind='known-resident-parent-paths-v1',max_graphs=8,max_arrays=32,max_bytes=32768)
# Ordinary mechanical containers only. No Receipt/Owner/Binding/Run is constructed.
class Record:
 def __init__(self,**kw):self.__dict__.update(kw)
def detached_result():
 a=Record();g=Record(node_features=a,edge_index=a,edge_features=a,edge_aggregates=None)
 train=Record(_graphs=[g],_training=[g]);dictionary=Record(_dictionary=Record(representatives=[g]),_proof=Record(_published=Record(_draws=Record(_training=train))))
 mcm=Record(_dictionary=dictionary,_graph=g,_matrix=a);closure=Record(_dictionary=dictionary,_graphs=(Record(_features=Record(_mcm=mcm)),))
 watches=[weakref.ref(x) for x in (a,g,train,dictionary,mcm,closure)]
 reader=lambda a:dict(object_id=id(a),shape=[2,3],strides=[12,4],dtype='float32',nbytes=24)
 result=m._retained_snapshot(closure,policy,array_reader=reader)
 return result,watches
result,watches=detached_result();assert all(w() is None for w in watches)
assert json.loads(m.encode(result))==result and result['unique_array_objects']==result['unique_graph_objects']==1
assert result['array_metadata_entries']==4 and result['whole_heap_or_alias_census'] is False and result['unique_allocated_bytes'] is None and result['capacity_or_saving_claim'] is False
# Extract only prepare's actual schema predicates, never invoke native authority.
functions={n.name:n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
statements=[]
for n in functions['prepare'].body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='retention' for t in n.targets):statements.append(copy.deepcopy(n))
 elif statements:
  if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[-1],ast.Constant) and n.value.args[-1].value=='observer policy schema':statements.append(copy.deepcopy(n))
  elif isinstance(n,ast.If) and ast.unparse(n.test)=='retention':statements.append(copy.deepcopy(n));break
assert len(statements)==3
module=ast.fix_missing_locations(ast.Module(body=statements,type_ignores=[]));schema=compile(module,'<actual-schema-predicates>','exec')
def accepts(p):
 try:exec(schema,{'p':p,'require':m.require,'_retention_policy':m._retention_policy});return True
 except (ValueError,KeyError,TypeError):return False
fields=['cell_id','source_commit','train_hash','fold_hash','metadata_input','call_ordinals','outputs','max_event_bytes','max_total_bytes']
legacy={k:None for k in fields}|{'schema_version':1};extended=legacy|{'schema_version':2,'parent_retention':policy}
assert accepts(legacy) and accepts(extended)
assert not accepts(legacy|{'parent_retention':policy}) and not accepts(legacy|{'schema_version':2}) and not accepts(extended|{'schema_version':3})
for key,value in [('max_graphs',True),('max_arrays',8193),('max_bytes',131073),('max_graphs',0)]:assert not accepts(extended|{'parent_retention':policy|{key:value}})
# Single execution of the candidate's bounded existing control set, no historical matrix.
run=subprocess.run([sys.executable,'-B',str(P/'check01.py')],text=True,capture_output=True,check=True)
assert not {'numpy','torch','scipy','pandas'}&set(sys.modules)
print(json.dumps({'schema_version':1,'decision':'ACCEPTED_SOURCE_AND_BOUNDED_MECHANICS_ONLY','candidate_sha256':sha(new.encode()),'manifest_sha256':sha(raw),'patch_inverse_exact':True,'source_pins_verified':True,'actual_verifier_freevar_count':len(verify.co_freevars),'published_freevar_present':True,'schema_selection_checks':9,'weakref_success_output_releases_original_mechanical_objects':True,'detached_json_output':True,'control_stdout':run.stdout,'control_stderr':run.stderr,'numerical_imports':False,'genuine_authority_objects_constructed':False,'genuine_runtime_integration_executed':False,'whole_population_capacity':False},sort_keys=True,indent=2))
