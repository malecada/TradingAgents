from pathlib import Path
from datetime import datetime,timedelta
import ast,copy,hashlib,json,stat,sys,weakref
D=Path(__file__).resolve().parent;P=D.parent/'financial-training-batch-observer01-2026-10-05';sys.path.insert(0,str(P));import training_batch_observer as O
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def ck(n,v):assert v,n;checks.append(n)
def refuses(n,f):
 try:f()
 except ValueError:checks.append(n);return
 raise AssertionError(n)
m=json.loads((P/'MANIFEST01.json').read_bytes());ck('manifest',h(P/'MANIFEST01.json').startswith('765720b7'))
for r in m['members']:
 p=P/r['path'];s=p.lstat();ck('mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
 if r['kind']=='file':ck('body '+r['path'],stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and h(p)==r['sha256'])
ck('whole membership',{r['path'] for r in m['members']}=={str(p.relative_to(P)) for p in P.rglob('*') if p.name!='MANIFEST01.json'})
s=(P/'evaluation.py').read_text();old=(P/'original_evaluation.py').read_text();back=s
inv=json.loads((P/'INVERSE01.json').read_bytes());ck('three edits',len(inv['edits'])==3)
for e in reversed(inv['edits']):ck('unique inverse',back.count(e['new'])==1);back=back.replace(e['new'],e['old'])
ck('literal inverse',back==old);ck('AST inverse',ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
ck('test hook unchanged',"test=batch_factory(arm,task,examples.test,scaler,features)" in s)
contract=json.loads((P/'CONTRACT01.json').read_bytes())
for n,r in contract['config_pins'].items():ck('actual config '+n,h(Path(r['path']))==r['sha256'])
class Opaque:pass
class Row:
 def __init__(self,day):
  d=datetime.fromisoformat(day);self.decision_at=day+'T00:00:00Z';self.input_dates=[(d-timedelta(days=i)).date().isoformat() for i in range(28,0,-1)];self.graph_hashes=['a'*64]*28;self.graph_available_at=[x+'T00:00:00Z' for x in self.input_dates]
 @property
 def targets(self):raise AssertionError('labels touched')
 @property
 def input_prices(self):raise AssertionError('price touched')
def scalar(o):return {'tensor_object_id':id(o),'storage_pointer':7,'storage_bytes':16,'shape':[1,32],'dtype':'opaque','stride':[32,1],'storage_offset':0}
rows=[Row('2022-03-01'),Row('2022-03-04')];a,b=Opaque(),Opaque();refs=[weakref.ref(a),weakref.ref(b)];g={'mcm':a,'edge_index':b};g2={'mcm':a,'edge_index':b};inputs={'prices':object(),'graph_sequences':[[g]*28,[g2]*28]}
event=O.snapshot([0,1],rows,inputs,tensor_reader=scalar);ck('2 dictionaries vs shared tensor',len(event['unique_graph_objects'])==2 and len({x['mcm']['tensor_object_id'] for x in event['unique_graph_objects']})==1);ck('56 positions',len(event['uses'])==56);ck('calendar gap',event['eligible_row_calendar_gaps'][0]['calendar_days_missing']==2);ck('epoch unknown',event['epoch_cursor'] is None)
for idx in ([True],[0,2],list(range(17))):refuses('invalid indices '+str(idx),lambda idx=idx:O.snapshot(idx,rows,inputs,tensor_reader=scalar))
refuses('mask unsupported',lambda:O.snapshot([0,1],rows,{**inputs,'mask':object()},tensor_reader=scalar))
prior=rows[0].graph_available_at;rows[0].graph_available_at=['2030-01-01T00:00:00Z']*28;refuses('late availability',lambda:O.snapshot([0,1],rows,inputs,tensor_reader=scalar));rows[0].graph_available_at=prior
fatal=KeyboardInterrupt('owned scalar callback')
def fail(x):raise fatal
try:O.snapshot([0,1],rows,inputs,tensor_reader=fail)
except BaseException as exc:ck('fatal identity',exc is fatal)
# Release retained exception traceback before object-lifetime assertion; no intrusive GC.
fatal.__traceback__=None;del inputs,g,g2,a,b
ck('event nonretention',all(r() is None for r in refs));O.encode(event)
source=(P/'training_batch_observer.py').read_text();t=ast.parse(source);funcs={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
for needle in ('type(features)is _Features','type(terminal)is Receipt','type(owner)is Owner','type(bound)is Binding','bound._run is run','terminal.check();bound._guard();run._active();run._check_source()',"'parent_population_object_census':None","resident_originals_retained'] is True"):
 ck('genuine resident predicate '+needle,needle in ast.get_source_segment(source,funcs['authority']))
ck('actual writer and length',"raw=_encode(event)" in source and "run.write_json(" in source);ck('state poisoned',"state['poisoned']=True" in source);ck('no inference flags',"complete_population_census=False,capacity_or_saving_claim=False" in source)
ck('production has no gc',not any(isinstance(n,ast.Import) and any(a.name=='gc' for a in n.names) for n in ast.walk(t)))
ck('no numerical import',not set(('torch','numpy','pandas')).intersection(sys.modules))
(D/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'genuine_authority_constructed':False,'public_observe_or_prepare':False,'numerical_observation':False},indent=2)+'\n');print(len(checks))
