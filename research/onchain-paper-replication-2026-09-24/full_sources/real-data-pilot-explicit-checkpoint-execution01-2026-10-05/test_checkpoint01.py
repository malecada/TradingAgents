"""Fresh synthetic engineering comparison; no historical/data/Run/Owner execution."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,types,unittest
import torch
D=Path(__file__).resolve().parent;M=D.parents[3];P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P
pkg=types.ModuleType('checkpoint_candidate');pkg.__path__=[str(T),str(M/P)];sys.modules[pkg.__name__]=pkg

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
model=load('checkpoint_candidate.model',T/'model.py');helper=load('checkpoint_candidate.real_pilot_training',T/'real_pilot_training.py')
legacy={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':4}
selected={**legacy,'schema_version':2,'graph_activation_checkpointing':True}
source=M/'tests/research/onchain_replication/test_real_pilot_training.py'
tree=ast.parse(source.read_text());example_ast=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='example')
env={'__file__':str(source),'Path':Path,'torch':torch,'json':json,'hashlib':hashlib,'ReplicationModel':model.ReplicationModel}
exec(compile(ast.Module(body=[example_ast],type_ignores=[]),str(source),'exec'),env)

def config():return json.loads((M/'research/onchain-paper-replication-2026-09-24/config/model.json').read_text())

class Checks(unittest.TestCase):
 def test_01_inverse_and_unchanged_graph_algorithm(self):
  record=json.loads((D/'SOURCE_DELTA01.json').read_text())
  for r in record['files']:
   raw=(D/'candidate'/r['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),r['candidate_sha256']);lines=raw.decode().splitlines(True)
   for e in reversed(r['edits']):self.assertEqual(lines[e['new_start']:e['new_end']],e['new']);lines[e['new_start']:e['new_end']]=e['old']
   self.assertEqual(''.join(lines).encode(),(D/'baseline'/Path(r['path']).name).read_bytes())
   self.assertEqual(hashlib.sha256((M/r['path']).read_bytes()).hexdigest(),r['baseline_sha256'])
  def cls(path,name):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name==name)
  self.assertEqual(ast.dump(cls(D/'baseline/model.py','GraphEncoder')),ast.dump(cls(T/'model.py','GraphEncoder')))
  a=cls(D/'baseline/model.py','ReplicationModel');b=cls(T/'model.py','ReplicationModel')
  for n in a.body:
   if isinstance(n,ast.FunctionDef) and n.name!='__init__':self.assertEqual(ast.dump(n),ast.dump(next(k for k in b.body if isinstance(k,ast.FunctionDef) and k.name==n.name)))
 def test_02_explicit_schema_and_config_refusals(self):
  self.assertIsNone(model.validate_execution(None));self.assertEqual(dict(model.validate_execution(legacy)),legacy)
  self.assertEqual(dict(model.validate_execution(selected)),selected)
  for field,value in [('graph_activation_checkpointing',False),('graph_activation_checkpointing',1),('backend','eager'),('block_edges',0),('schema_version',True)]:
   p=dict(selected);p[field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):model.validate_execution(p)
  p=dict(legacy,graph_activation_checkpointing=True)
  with self.assertRaises(ValueError):model.validate_execution(p)
  for c in [dict(config(),gat_dropout=.1),dict(config(),graph_activation_checkpointing=True)]:
   with self.assertRaises(ValueError):model.ReplicationModel(c,'classification',execution=selected)
  # Legacy scientific-config behavior remains available outside the frozen helper.
  m=model.ReplicationModel(dict(config(),graph_activation_checkpointing=True),'classification')
  self.assertTrue(m.graph_activation_checkpointing)
  self.assertFalse(model.ReplicationModel(config(),'classification').graph_activation_checkpointing)
 def test_03_one_fresh_paired_update_and_recomputation(self):
  records=[];holders=[];states=[];logits=[];calls=[]
  for name,policy in [('streamed-baseline',legacy),('checkpointed',selected)]:
   parent=D/name;parent.mkdir();args=env['example'](parent);holder={};count=[];out=[]
   def factory(args=args,policy=policy,holder=holder,count=count,out=out):
    m=model.ReplicationModel(args['model_config'],'classification',execution=policy)
    m.graph.register_forward_pre_hook(lambda *unused:count.append(1))
    m.register_forward_hook(lambda module,inputs,value:out.append(value.detach().clone()))
    holder['model']=m;return m
   args.update(model_factory=factory,model_execution=copy.deepcopy(policy),provenance={'scope':'fresh synthetic checkpoint algorithm comparison only'})
   result=helper.run_one_update(**args);state=torch.load(args['directory']/'checkpoint.pt',weights_only=True)
   self.assertEqual(result['model_execution'],policy);self.assertEqual(state['model_execution'],policy)
   self.assertTrue(result['checkpoint_exact_readback']);self.assertEqual(result['optimizer_steps'],1);self.assertFalse(result['financial_fit_complete'])
   self.assertTrue(all(result['gradients'][k]['nonzero_elements']>0 for k in ['gat','lstm','attention']))
   records.append(result);holders.append(holder['model']);states.append(state);logits.append(out[0]);calls.append(len(count))
  self.assertTrue(torch.equal(*logits));self.assertEqual(states[0]['loss'],states[1]['loss'])
  self.assertTrue(helper._same(states[0]['model'],states[1]['model'],torch));self.assertTrue(helper._same(states[0]['optimizer'],states[1]['optimizer'],torch));self.assertTrue(helper._same(states[0]['rng'],states[1]['rng'],torch))
  gradients=0
  for (n,a),(m,b) in zip(holders[0].named_parameters(),holders[1].named_parameters(),strict=True):
   self.assertEqual(n,m);self.assertIsNotNone(a.grad);self.assertIsNotNone(b.grad);self.assertTrue(torch.equal(a.grad,b.grad),n);gradients+=1
  self.assertEqual(calls,[7,14])
  record={'schema_version':1,'scope':'one fresh synthetic paired CPU update, not empirical capacity','bitwise_equal':{'logits':True,'loss':True,'model':True,'optimizer':True,'rng':True,'gradient_tensors':gradients},'graph_forward_entries':calls,'rows':16,'lookback':28,'graphs':7,'nodes_per_graph':3,'edges_per_graph':3,'source_original_configs_unchanged':True,'policies':[legacy,selected],'paper_financial_fits':0,'memory_savings_measured':False}
  (D/'COMPARISON01.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
 def test_04_factory_cannot_enable_checkpointing_implicitly(self):
  parent=D/'implicit-refusal';parent.mkdir();args=env['example'](parent)
  args['model_factory']=lambda:model.ReplicationModel(args['model_config'],'classification',execution=selected)
  with self.assertRaisesRegex(ValueError,'checkpoint execution'):helper.run_one_update(**args)
  self.assertFalse((args['directory']/'checkpoint.pt').exists());self.assertTrue((args['directory']/'failed.json').exists())

if __name__=='__main__':unittest.main(verbosity=2)
