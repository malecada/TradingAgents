"""Tiny synthetic scalars; actual producer AST, no numerical imports/authority."""
import ast,copy,hashlib,importlib.util,json,os,sys,types,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
HERE=Path(__file__).parent

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def load():
 p=HERE/'population_batch_projection.py';s=importlib.util.spec_from_file_location('projection_candidate',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def fixture():
 hashes=['1'*64,'2'*64];rows=[]
 for i in range(17):
  d=datetime(2024,2,1,tzinfo=timezone.utc)+timedelta(days=i+(i>=8))
  dates=[(d-timedelta(days=28-j)).date().isoformat() for j in range(28)]
  rows.append(dict(decision_at=d.isoformat(),label_start=d.isoformat(),label_end=(d+timedelta(days=1)).isoformat(),max_input_available_at=d.isoformat(),input_dates=dates,input_prices=[1]*28,graph_hashes=hashes*14,graph_available_at=['2023-12-01T00:00:00Z']*28,target_price=2,up=1))
 exc=[{'decision_at':'2024-02-09T00:00:00+00:00','reason':'missing_expected_graph','partition':'train'}]
 examples=dict(train=rows,test=[],exclusions=exc,train_hash=sha(canonical(rows)),test_mask_hash=sha(canonical([])),source_hashes=['3'*64],fold_hash='4'*64)
 scaler=dict(mean=1,std=1,dates=[],train_hash=examples['train_hash'])
 pop=dict(schema_version=1,examples=examples,scaler=scaler)
 binding=dict(train_hash=examples['train_hash'],test_mask_hash=examples['test_mask_hash'],test_examples_hash=sha(canonical([])),source_hashes=['3'*64],fold_hash='4'*64,scaler=scaler)
 assembly=dict(schema_version=1,weeks={},decision_count=18,provenance={'source_admission':{'source_hashes':['3'*64],'price_source_hash':'3'*64},'source_admission_hash':sha(canonical({'source_hashes':['3'*64],'price_source_hash':'3'*64})),'calendar':{'lookback_days':28},'fold':{'member_hash':'4'*64}})
 return pop,binding,assembly

def producer():
 path=Path(os.environ.get('ASSEMBLY_SOURCE',HERE/'population_assembly.py'))
 tree=ast.parse(path.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='produce_registered_population')
 # Actual function; only its lazy imports route to qualified scalar stand-ins.
 contracts=types.ModuleType('qualified.contracts');contracts.Fold=lambda **v:v;contracts.PricePanel=lambda **v:v
 pkg=types.ModuleType('qualified');pkg.__path__=[];sys.modules['qualified']=pkg;sys.modules['qualified.contracts']=contracts
 module=types.ModuleType('qualified.population_batch_projection');module.publish_projection=lambda run,*a:run.write_json('projection.json',{'selected':True});sys.modules[module.__name__]=module
 result={'population':{'original':'population'},'binding':{'original':'binding'},'schema_version':1}
 ns={'__name__':'qualified.assembly','__package__':'qualified','json':json,'digest':sha,'assemble_population':lambda *a:copy.deepcopy(result)}
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
 return ns['produce_registered_population'],result

class FakeRun:
 def __init__(self,version=2,fail=None):
  self._published_outputs={};self.writes=[];self.fail=fail
  self.plan={'schema_version':version,'graphs':{},'price_input':'prices','fold':{},'calendar_input':'calendar','expected_weeks':[],'admission_input':'admission','outputs':{'population':'population.json','binding':'binding.json','assembly':'assembly.json'}}
  if version==2:self.plan['projection_input']='projection_policy';self.plan['outputs']['projection']='projection.json'
  self.admission=types.SimpleNamespace(experiment={'outputs':list(self.plan['outputs'].values())})
 def read_input(self,n):return json.dumps(self.plan if n=='plan' else {}).encode()
 def write_json(self,n,v):
  if n==self.fail:raise MemoryError('retained synthetic publication failure')
  self.writes.append((n,v));self._published_outputs[n]=sha(canonical(v))

class ProducerTests(unittest.TestCase):
 def test_new_registered_projection_branch(self):
  f,result=producer();r=FakeRun();
  try:out=f(r,'plan')
  except ValueError as e:self.fail('selected schema2 incorrectly refused: '+str(e))
  self.assertEqual(out,result);self.assertEqual([x[0] for x in r.writes],['population.json','binding.json','assembly.json','projection.json'])
 def test_legacy_three_outputs_unchanged(self):
  f,result=producer();r=FakeRun(1);self.assertEqual(f(r,'plan'),result);self.assertEqual([x[0] for x in r.writes],['population.json','binding.json','assembly.json'])
 def test_publication_fatal_propagates_retains_prefix(self):
  f,_=producer();r=FakeRun(fail='projection.json')
  with self.assertRaises(MemoryError):f(r,'plan')
  self.assertEqual([x[0] for x in r.writes],['population.json','binding.json','assembly.json'])

class ProjectionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=load()
 def test_gap_short_reuse_and_no_labels(self):
  p,b,a=fixture();v=self.m.project(p,b,a,{})
  self.assertEqual([x['ordinals'] for x in v['batches']], [list(range(16)),[16]])
  self.assertEqual(v['batches'][0]['graph_hashes'],['1'*64,'2'*64]);self.assertEqual(v['batches'][0]['multiplicity'],[224,224])
  self.assertEqual(v['batches'][1]['multiplicity'],[14,14]);self.assertEqual(len(v['rows'][8]['graph_hashes']),28)
  self.assertEqual(v['rows'][8]['decision_at'],'2024-02-10T00:00:00+00:00');self.assertEqual(v['exclusions'],p['examples']['exclusions'])
  self.assertEqual(v['components']['1'*64]['status'],'missing_registered_component')
  text=json.dumps(v)
  for label in ['input_prices','target_price','label_start','label_end','"up"','"mean"']:self.assertNotIn(label,text)
 def test_order_hash_late_length_and_unknown_row_field_refuse(self):
  for mutate in [lambda p:p['examples']['train'].reverse(),lambda p:p['examples'].__setitem__('train_hash','f'*64),lambda p:p['examples']['train'][0]['graph_available_at'].__setitem__(0,'2024-02-01T00:00:00Z'),lambda p:p['examples']['train'][0]['graph_hashes'].pop(),lambda p:p['examples']['train'][0].__setitem__('prediction',0)]:
   p,b,a=fixture();mutate(p)
   # Rebind content hash for semantic counterexamples, never an authority claim.
   if p['examples']['train_hash']!='f'*64:p['examples']['train_hash']=b['train_hash']=p['scaler']['train_hash']=sha(canonical(p['examples']['train']))
   with self.assertRaises(ValueError):self.m.project(p,b,a,{})
 def test_source_and_binding_corruption(self):
  for key in ['source_hashes','fold_hash','test_examples_hash']:
   p,b,a=fixture();b[key]=['e'*64] if key=='source_hashes' else 'e'*64
   with self.assertRaises(ValueError):self.m.project(p,b,a,{})
 def test_unavailable_and_unexpected_component(self):
  p,b,a=fixture();v=self.m.project(p,b,a,{'1'*64:{'status':'unavailable','reason':'MCM not completed','evidence_hashes':['9'*64]}})
  self.assertEqual(v['components']['1'*64]['status'],'unavailable')
  with self.assertRaises(ValueError):self.m.project(p,b,a,{'8'*64:{'status':'unavailable','reason':'extra','evidence_hashes':['9'*64]}})
 def test_fixed_shape_metadata_only(self):
  h='1'*64;sc=lambda v:{'kind':'scalar','value':v}
  tree={'kind':'dict','items':[[sc('feature'),{'kind':'dict','items':[[sc('mcm'),{'kind':'array','member':'array-000000.npy'}],[sc('edge_index'),{'kind':'array','member':'array-000001.npy'}]]}],[sc('aligned_vectors'),sc(None)]]}
  m={'schema_version':1,'context':{'graph_hash':h},'tree':tree,'arrays':{'array-000000.npy':{'shape':[3,32],'dtype':'float32','bytes':512,'sha256':'5'*64},'array-000001.npy':{'shape':[2,2],'dtype':'int64','bytes':160,'sha256':'6'*64}}}
  v=self.m.component(m,h);self.assertEqual(v['status'],'declared_metadata_only');self.assertEqual(v['fixed_tensor_bytes'],416)
  for change in [('array-000000.npy','shape',[3,31]),('array-000001.npy','dtype','float32'),('array-000000.npy','bytes',100)]:
   bad=copy.deepcopy(m);bad['arrays'][change[0]][change[1]]=change[2]
   with self.assertRaises(ValueError):self.m.component(bad,h)
 def test_bounded_parser_and_row_overflow(self):
  with self.assertRaises(ValueError):self.m.parse(b'{"x":1,"x":2}')
  with self.assertRaises(ValueError):self.m.parse(b' '* (self.m.DOC_LIMIT+1))
  p,b,a=fixture();p['examples']['train']*=242
  with self.assertRaises(ValueError):self.m.project(p,b,a,{})

if __name__=='__main__':unittest.main()
