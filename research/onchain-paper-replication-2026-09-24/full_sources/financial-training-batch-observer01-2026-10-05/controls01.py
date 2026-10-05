"""Opaque stdlib mechanics only; no Owner/Run/Binding or tensor surrogate authority."""
import ast, copy, gc, hashlib, json, weakref
from pathlib import Path
from datetime import datetime,timedelta
import training_batch_observer as O
H=Path(__file__).resolve().parent;checks=[]
def check(name,v):
 if not v:raise AssertionError(name)
 checks.append(name)
def refuses(name,fn,kind=ValueError):
 try:fn()
 except kind:checks.append(name);return
 raise AssertionError(name+' accepted')
class Opaque:
 def __init__(self,pointer):self.pointer=pointer
class Row:
 def __init__(self,decision,graphs):
  self.decision_at=decision+'T00:00:00Z';d=datetime.fromisoformat(decision)
  self.input_dates=tuple((d-timedelta(days=i)).date().isoformat() for i in range(28,0,-1))
  self.graph_hashes=tuple(hashlib.sha256(O.week(day).encode()).hexdigest() for day in self.input_dates)
  self.graph_available_at=tuple(day+'T00:00:00Z' for day in self.input_dates)
  for h in self.graph_hashes:
   if h not in graphs:graphs[h]={'mcm':Opaque(17),'edge_index':Opaque(23)}
 @property
 def up(self):raise AssertionError('label access')
 @property
 def input_prices(self):raise AssertionError('price access')
 @property
 def target_price(self):raise AssertionError('target access')
def metadata(obj):return {'tensor_object_id':id(obj),'storage_pointer':obj.pointer,'storage_bytes':128,'dtype':'opaque','shape':[1,32],'device':'opaque','storage_offset':0,'stride':[32,1]}
graphs={};rows=[Row('2022-03-01',graphs),Row('2022-03-08',graphs)]
inputs={'prices':object(),'graph_sequences':[[graphs[h] for h in row.graph_hashes] for row in rows]}
event=O.snapshot([0,1],rows,inputs,tensor_reader=metadata)
check('56 original selected positions',len(event['uses'])==56)
check('consecutive eligible indices preserve calendar gap',event['eligible_row_calendar_gaps']==[{'after':'2022-03-01T00:00:00Z','before':'2022-03-08T00:00:00Z','calendar_days_missing':6}])
check('one graph object per actual hash',all(len(v)==1 for v in event['hash_to_object_ids'].values()))
check('unique graph object denominator',len(event['unique_graph_objects'])==len(graphs))
check('shared opaque storage separately recorded',len({v['mcm']['storage_pointer'] for v in event['unique_graph_objects']})==1 and len({v['mcm']['tensor_object_id'] for v in event['unique_graph_objects']})==len(graphs))
check('no fake epoch cursor',event['epoch_cursor'] is None)
check('no array or label values in whitelist',all(set(r)=={'eligible_index','decision_at','input_dates','graph_hashes','graph_available_at'} for r in event['training_rows']))
raw=O.encode(event);check('bounded opaque event',len(raw)<256*1024)
refs=[weakref.ref(v) for g in graphs.values() for v in g.values()]
del inputs,graphs;gc.collect()
check('event retains no graph tensor payload references',all(r() is None for r in refs))
# A later event can reuse scalar storage addresses; no cross-event identity claim.
graphs={};rows=[Row('2022-03-01',graphs),Row('2022-03-08',graphs)];inputs={'prices':object(),'graph_sequences':[[graphs[h] for h in row.graph_hashes] for row in rows]}
later=O.snapshot([0,1],rows,inputs,tensor_reader=metadata)
check('storage pointer reuse remains event-local',later['identity_scope']==event['identity_scope'] and later['unique_graph_objects'][0]['mcm']['storage_pointer']==17)
refuses('nonconsecutive eligible indices',lambda:O.snapshot([0,2],rows,inputs,tensor_reader=metadata))
refuses('oversize batch16',lambda:O.snapshot(list(range(17)),rows,inputs,tensor_reader=metadata))
refuses('mask extension unsupported',lambda:O.snapshot([0,1],rows,{**inputs,'mask':object()},tensor_reader=metadata))
bad=[list(x) for x in inputs['graph_sequences']];bad[0][0]=None
refuses('missing graph step refused',lambda:O.snapshot([0,1],rows,{'prices':object(),'graph_sequences':bad},tensor_reader=metadata))
old=rows[0].graph_available_at;rows[0].graph_available_at=('2030-01-01T00:00:00Z',)+old[1:]
refuses('late availability refused',lambda:O.snapshot([0,1],rows,inputs,tensor_reader=metadata));rows[0].graph_available_at=old
old=rows[0].input_dates;rows[0].input_dates=(old[1],)+old[1:]
refuses('lookback date gap refused',lambda:O.snapshot([0,1],rows,inputs,tensor_reader=metadata));rows[0].input_dates=old
primary=KeyboardInterrupt('opaque metadata reader failure')
def fail(_):raise primary
try:O.snapshot([0,1],rows,inputs,tensor_reader=fail)
except BaseException as error:check('original fatal preserved',error is primary)
else:raise AssertionError('fatal swallowed')
inverse=json.loads((H/'INVERSE01.json').read_bytes());back=(H/'evaluation.py').read_text()
for edit in reversed(inverse['edits']):check('literal inverse unique',back.count(edit['new'])==1);back=back.replace(edit['new'],edit['old'])
check('exact byte inverse',back.encode()==(H/'original_evaluation.py').read_bytes())
check('full scientific AST inverse',ast.dump(ast.parse(back))==ast.dump(ast.parse((H/'original_evaluation.py').read_bytes())))
oldtree=ast.parse((H/'original_evaluation.py').read_bytes());newtree=ast.parse((H/'evaluation.py').read_bytes())
oldf={n.name:ast.dump(n) for n in oldtree.body if isinstance(n,ast.FunctionDef)};newf={n.name:ast.dump(n) for n in newtree.body if isinstance(n,ast.FunctionDef)}
for name in oldf:
 if name not in ('batch_factory','evaluate_cell'):check('unchanged function '+name,oldf[name]==newf[name])
import sys
check('no numerical modules imported',not any(x in sys.modules for x in ('numpy','torch','pandas','scipy')))
result={'schema_version':1,'checks':checks,'count':len(checks),'genuine_native_path_executed':False,'actual_population_observed':False,'numerical_authority':False,'opaque_pointer_values_are_synthetic':True}
with (H/'CONTROLS01.json').open('xb') as f:f.write(O.encode(result))
print(json.dumps({'passed':len(checks),'native_observation':False}))
