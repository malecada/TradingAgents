"""Exact boundary code; qualified scalar fake module/parameter tree, not Torch."""
import ast,copy,hashlib,json,unittest,weakref
from pathlib import Path
from types import SimpleNamespace
import test_contract01 as prior
HERE=Path(__file__).resolve().parent

class Parameter:
 def __init__(self,shape):self.shape=shape;self.requires_grad=True;self.dtype='torch.float32';self.device=SimpleNamespace(type='cpu',index=None)
class Module:
 def forward(self):pass
 def modules(self):return [m for n,m in self.named_modules()]
 def named_modules(self):return [('',self)]
 def named_parameters(self):return []
 def named_buffers(self):return []
class GraphAttention(Module):
 def __init__(self):
  self.block_edges=65536;self.concat=True;self.activation='elu';self.dropout=0.;self.slope=.2;self.weight=Parameter((2,4,3))
 def named_parameters(self):return [('weight',self.weight)]
class EagerLayer(Module):pass
class Linear(Module):
 def __init__(self):self.in_features=32;self.out_features=4
class Graph(Module):
 def __init__(self,config,execution):self.config=copy.deepcopy(config);self.execution=execution;self.gat=[GraphAttention()];self.mlp=Linear()
class ReplicationModel(Module):
 def __init__(self,config,task,*,execution=None):
  self.config=copy.deepcopy(config);self.task=task;self.execution=execution;self.graph_activation_checkpointing=False;self.graph=Graph(config,execution);self.training=True
 def named_modules(self):return [('',self),('graph',self.graph),('graph.mlp.0',self.graph.mlp),('graph.gat.0',self.graph.gat[0])]
 def named_parameters(self):return [('graph.gat.0.weight',self.graph.gat[0].weight)]
 def parameters(self):return [p for n,p in self.named_parameters()]
 def train(self,mode=True):self.training=mode;return self
 def eval(self):return self.train(False)

CONFIG={'gat_heads':[2],'mlp_widths':[4],'mcm_input':32,'gat_widths':[3],'gat_concatenate':[True],'gat_activation':['elu'],'gat_dropout':0.,'leaky_relu_slope':.2,'graph_activation_checkpointing':False}

def load_boundary():
 tree=ast.parse((HERE/'financial_execution.py').read_text())
 class Strip(ast.NodeTransformer):
  def visit_ImportFrom(self,node):return ast.Pass()
  def visit_Import(self,node):return ast.Pass()
 tree=Strip().visit(tree);tree.body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name not in ('authenticate','_classes')]
 ns={'hashlib':hashlib,'json':json,'Path':Path,'weakref':weakref,'ReplicationModel':ReplicationModel,'GraphAttention':GraphAttention}
 exec(compile(ast.fix_missing_locations(tree),'actual_boundary','exec'),ns)
 ns['authenticate']=ns['identity'];ns['_classes']=lambda:(ReplicationModel,GraphAttention)
 return ns

def model(ns):
 value=prior.selected()
 if 'construct' in ns:return ns['construct'](copy.deepcopy(CONFIG),'classification',value)
 return ns['attach'](ReplicationModel(copy.deepcopy(CONFIG),'classification',execution=value['policy']),value)

class Boundary(unittest.TestCase):
 def test_hidden_selected_labels_and_nested_wrapper_refused(self):
  ns=load_boundary();obj=model(ns);obj.execution=None;del obj._financial_execution
  with self.assertRaises(ValueError):ns['check_model'](obj,None)
  class Wrapper(Module):
   def named_modules(self):return [('',self),('hidden',GraphAttention())]
  with self.assertRaises(ValueError):ns['check_model'](Wrapper(),None)
  ns['check_model'](EagerLayer(),None)
 def test_scientific_and_trainability_changes_refused(self):
  mutations=[lambda x:setattr(x.graph.gat[0].weight,'requires_grad',False),lambda x:setattr(x.graph.gat[0],'slope',.9),lambda x:setattr(x.graph.gat[0],'dropout',.5),lambda x:setattr(x.graph.gat[0],'concat',False),lambda x:setattr(x.graph.gat[0],'activation','identity'),lambda x:setattr(x,'task','regression'),lambda x:x.config['mlp_widths'].append(8),lambda x:setattr(x.graph.gat[0].weight,'shape',(2,4,4)),lambda x:setattr(x,'_financial_pin','forged'),lambda x:setattr(x.graph.mlp,'in_features',64),lambda x:setattr(x.graph.gat[0],'forward',lambda:None),lambda x:setattr(x.graph.gat[0],'weight',Parameter((2,4,3)))]
  for mutate in mutations:
   ns=load_boundary();obj=model(ns);mutate(obj)
   with self.subTest(mutate=mutate),self.assertRaises(ValueError):ns['check_model'](obj,prior.selected())
 def test_train_eval_and_parameter_values_do_not_change_pin(self):
  ns=load_boundary();obj=model(ns);ns['check_model'](obj,prior.selected());obj.eval();ns['check_model'](obj,prior.selected());obj.train();ns['check_model'](obj,prior.selected())
 def test_rebaseline_cannot_use_mutable_model_metadata(self):
  ns=load_boundary();obj=model(ns);obj.graph.gat[0].slope=.7
  if 'attach' in ns:
   with self.assertRaises(ValueError):ns['attach'](obj,prior.selected())
  else:
   self.assertIn('_PINS',ns)
   with self.assertRaises(ValueError):ns['check_model'](obj,prior.selected())
 def test_checkpoint_contract_refuses_after_decode_before_restore(self):
  import io
  ns=load_boundary();obj=model(ns);value=prior.selected();contract=ns['model_contract'](obj,value);contract['task']='regression';calls=[]
  state={'model_execution':value,'model_contract':contract}
  node=next(n for n in ast.parse((HERE/'checkpoints.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='load_checkpoint')
  space={'_provenance':lambda p:None,'financial':SimpleNamespace(check_model=ns['check_model'],check_state_model=ns['check_state_model']),'read_artifact':lambda *a:{'state.pt':b'synthetic metadata stand-in'},'io':io,'torch':SimpleNamespace(load=lambda *a,**k:(calls.append('decode') or state))}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_load_checkpoint','exec'),space)
  with self.assertRaises(ValueError):space['load_checkpoint']('unused',obj,None,None,{'model_execution':value})
  self.assertEqual(calls,['decode'])
 def test_config_and_retained_contract_are_detached(self):
  ns=load_boundary();config=copy.deepcopy(CONFIG);value=prior.selected();obj=ns['construct'](config,'classification',value)
  config['mlp_widths'].append(16);value['policy']['block_edges']=1
  ns['check_model'](obj,prior.selected());record=ns['model_contract'](obj,prior.selected());record['task']='regression'
  ns['check_model'](obj,prior.selected());self.assertEqual(ns['model_contract'](obj,prior.selected())['task'],'classification')
 def test_checkpoint_refuses_before_rng_or_restore(self):
  ns=load_boundary();obj=model(ns);obj.graph.gat[0].weight.requires_grad=False;calls=[]
  node=next(n for n in ast.parse((HERE/'checkpoints.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='load_checkpoint')
  space={'_provenance':lambda p:None,'financial':SimpleNamespace(check_model=ns['check_model']),'read_artifact':lambda *a:calls.append('read')}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_load_checkpoint','exec'),space)
  with self.assertRaises(ValueError):space['load_checkpoint']('unused',obj,None,None,{'model_execution':prior.selected()})
  self.assertEqual(calls,[])

if __name__=='__main__':unittest.main()
