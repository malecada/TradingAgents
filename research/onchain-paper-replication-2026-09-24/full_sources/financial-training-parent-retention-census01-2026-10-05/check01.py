"""Mechanical metadata controls only. No authority class is instantiated."""
import ast,copy,importlib.util,json,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_observer',HERE/'training_batch_observer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
N=types.SimpleNamespace
p={'kind':'known-resident-parent-paths-v1','max_graphs':8,'max_arrays':32,'max_bytes':32768}
a=object();g=N(node_features=a,edge_index=a,edge_features=a,edge_aggregates=None)
training=N(_graphs=[g],_training=[g]);dictionary=N(_dictionary=N(representatives=[g]),_proof=N(_published=N(_draws=N(_training=training))))
mcm=N(_dictionary=dictionary,_graph=g,_matrix=a);closure=N(_dictionary=dictionary,_graphs=(N(_features=N(_mcm=mcm)),))
def metadata(v):return {'object_id':id(v),'shape':[2,3],'strides':[12,4],'dtype':'float32','nbytes':24}
def snapshot(**kw):return m._retained_snapshot(closure,kw.get('policy',p),array_reader=kw.get('reader',metadata))
x=snapshot();assert x['unique_graph_objects']==1 and x['unique_array_objects']==1 and x['array_metadata_entries']==4
assert x['training_populations']['_graphs']['object_ids']==[id(g)] and x['training_populations']['_training']['object_ids']==[id(g)]
assert x['dictionary_representatives']['object_ids']==[id(g)]
assert x['whole_heap_or_alias_census'] is False and x['unique_allocated_bytes'] is None
assert json.loads(m.encode(x))==x
# Output has only detached JSON values; removing the borrowed mechanical graph changes no event.
frozen=m.encode(x);training._graphs=[];assert m.encode(x)==frozen;training._graphs=[g]
def refuse(f):
 try:f()
 except ValueError:return
 raise AssertionError('expected refusal')
refuse(lambda:snapshot(policy={**p,'max_arrays':1}))
refuse(lambda:snapshot(policy={**p,'max_bytes':1}))
refuse(lambda:snapshot(policy={**p,'max_graphs':True}))
refuse(lambda:snapshot(policy={**p,'extra':True}))
refuse(lambda:snapshot(reader=lambda a:{**metadata(a),'values':[]}))
refuse(lambda:snapshot(reader=lambda a:{**metadata(a),'shape':[object()]}))
training._graphs=[g]*9;refuse(snapshot);training._graphs=[g]
mcm._dictionary=object();refuse(snapshot);mcm._dictionary=dictionary
refuse(lambda:m._resident_retention(N(_verify=lambda:None),p))
# Source-bound checks: original authority gates and default branches are retained.
root=next(v for v in HERE.parents if (v/'tradingagents/research/onchain_replication/training_batch_observer.py').is_file())
old=ast.parse((root/'tradingagents/research/onchain_replication/training_batch_observer.py').read_text());new=ast.parse((HERE/'training_batch_observer.py').read_text())
func=lambda tree,name:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
for name in ('snapshot','tensor_metadata','project','excluded'):
 assert ast.dump(func(old,name))==ast.dump(func(new,name))
aold=func(old,'authority');anew=copy.deepcopy(func(new,'authority'));anew.args=copy.deepcopy(aold.args)
# Only the resident return census expression may differ; detached return and every gate remain exact.
returns_old=[n for n in ast.walk(aold) if isinstance(n,ast.Return)];returns_new=[n for n in ast.walk(anew) if isinstance(n,ast.Return)]
detached=lambda values:next(n for n in values if isinstance(n.value,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='feature_route' for k in n.value.keys))
assert ast.dump(detached(returns_old))==ast.dump(detached(returns_new))
for o,n in zip(returns_old,returns_new):
 if isinstance(n.value,ast.Dict):
  for i,k in enumerate(n.value.keys):
   if isinstance(k,ast.Constant) and k.value=='parent_population_object_census':n.value.values[i]=copy.deepcopy(o.value.values[i])
assert ast.dump(aold)==ast.dump(anew)
assert not any(k in sys.modules for k in ('numpy','torch','scipy','pandas'))
print('PASS 11 focused mechanical/refusal controls; original authority/default detached return and selected-batch helpers AST preserved; no numerical imports or genuine authority objects.')
