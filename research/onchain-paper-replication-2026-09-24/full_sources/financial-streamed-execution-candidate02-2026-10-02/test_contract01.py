"""Pure exact source metadata/forwarding checks. No tensor/runtime imports."""
import ast,copy,hashlib,json,unittest,weakref
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent

def load():
 p=HERE/'financial_execution.py'
 if not p.exists():raise AssertionError('financial execution identity adapter absent')
 tree=ast.parse(p.read_text());names={'identity','policy','canonical','validate_state','plan_selection'}
 nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in names]
 ns={'json':json,'hashlib':hashlib,'weakref':weakref};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);return ns

def selected():
 policy={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536};sha='e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f'
 return {'policy':policy,'policy_sha256':hashlib.sha256(json.dumps(policy,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'source_path':'tradingagents/research/onchain_replication/streamed_gat.py','source_sha256':sha,'candidate_sha256':sha}

class Contract(unittest.TestCase):
 def test_identity_detached_and_strict(self):
  ns=load();value=selected();saved=ns['identity'](value);value['policy']['block_edges']=1;self.assertEqual(saved,selected());self.assertIsNone(ns['identity'](None))
  for key,val in [('policy_sha256','0'*64),('source_path','other'),('source_sha256','0'*64),('candidate_sha256','0'*64),('extra',0)]:
   value=selected();value[key]=val
   with self.assertRaises(ValueError):ns['identity'](value)
  for key,val in [('schema_version',True),('block_edges',True),('block_edges',1),('backend','eager')]:
   value=selected();value['policy'][key]=val
   with self.assertRaises(ValueError):ns['identity'](value)
 def test_checkpoint_execution_absent_or_mutated_refused(self):
  ns=load();value=selected();ns['validate_state']({},{});ns['validate_state']({'model_execution':value,'model_contract':{}},{'model_execution':value})
  for state,pro in [({}, {'model_execution':value}),({'model_execution':value},{}),({'model_execution':None},{'model_execution':value})]:
   with self.assertRaises(ValueError):ns['validate_state'](state,pro)
 def test_selected_registry_forwards_policy_and_default_unchanged(self):
  ns=load();calls=[]
  def constructor(config,task,**kw):calls.append((config,task,kw));return SimpleNamespace(execution=kw.get('execution'))
  ns.update(ReplicationModel=constructor,financial=SimpleNamespace(identity=ns['identity'],authenticate=lambda value:ns['identity'](value),construct=lambda config,task,value:constructor(config,task,execution=value['policy'])),PRICE_ARMS=set(),GRAPH_ARMS=set(),VECTOR_WIDTHS={})
  node=next(n for n in ast.parse((HERE/'model_registry.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='build_model')
  exec(compile(ast.Module(body=[node],type_ignores=[]),'registry','exec'),ns)
  ns['build_model']('proposed','direction',{});self.assertEqual(calls[-1],({},'classification',{}))
  ns['build_model']('proposed','direction',{},execution=selected());self.assertEqual(calls[-1][2],{'execution':selected()['policy']})
  with self.assertRaises(ValueError):ns['build_model']('lstm','direction',{},execution=selected())
 def test_plan_selection_explicit_and_legacy(self):
  ns=load();plan={key:None for key in ns['PLAN_KEYS']};plan.update(schema_version=1,cells=[{'cell':{'arm':'proposed'}}],model={})
  self.assertEqual(ns['plan_selection'](plan),{})
  plan.update(schema_version=2,model_execution={'proposed':selected()});self.assertEqual(ns['plan_selection'](plan),{'proposed':selected()})
  for mapping in ({},{'proposed':None},{'lstm':selected()},{'training_label_permutation':selected()}):
   bad=copy.deepcopy(plan);bad['model_execution']=mapping
   with self.assertRaises(ValueError):ns['plan_selection'](bad)
  bad=copy.deepcopy(plan);bad['model']['graph_activation_checkpointing']=True
  with self.assertRaises(ValueError):ns['plan_selection'](bad)
 def test_actual_checkpoint_provenance_schema(self):
  ns=load();functions=[n for n in ast.parse((HERE/'checkpoints.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_provenance']
  def require_hash(value):
   if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('hash')
  space={'financial':SimpleNamespace(identity=ns['identity']),'require_hash':require_hash}
  exec(compile(ast.Module(body=functions,type_ignores=[]),'checkpoint_schema','exec'),space)
  base={'source_hashes':['a'*64],'config_hash':'b'*64,'input_hash':'c'*64,'dictionary_hash':'d'*64,'fold_id':'f','cell_id':'c','source_commit':'e'*40}
  space['_provenance'](base);space['_provenance']({**base,'model_execution':selected()})
  for value in (None,{}, {'bad':True}):
   with self.assertRaises(ValueError):space['_provenance']({**base,'model_execution':value})
  with self.assertRaises(ValueError):space['_provenance']({**base,'unregistered':1})
 def test_real_call_path_has_bindings(self):
  required={'run.py':['financial.plan_selection','financial.for_run','model_execution=execution'], 'evaluation.py':['execution=None','execution=execution','financial.check_model','financial.validate_state'], 'checkpoints.py':['financial.check_model','financial.check_state_model'], 'training.py':['financial.check_model'], 'replay.py':['financial.validate_state','execution=execution']}
  for name,fragments in required.items():
   source=(HERE/name).read_text();ast.parse(source)
   for fragment in fragments:self.assertIn(fragment,source,name)

if __name__=='__main__':unittest.main()
