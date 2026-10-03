"""Actual publishing logic with qualified external ResearchRun/runtime substitutes.
No admission/claim/Owner/native test is asserted. Real tiny metadata files used.
"""
import copy,hashlib,json,tempfile,types,unittest,sys
from pathlib import Path
from test_projection01 import load,fixture,sha,canonical,HERE

def encoded(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
class SyntheticRun:
 def _active(self):
  if self.dead:raise ValueError('synthetic terminal')
 def _check_source(self):
  if self.bad_source:raise ValueError('synthetic changed source')
 def _check_inputs(self):
  for n,v in self.admission.inputs.items():
   if sha((self.admission.root/v['path']).read_bytes())!=v['sha256']:raise ValueError('synthetic input changed')
 def read_input(self,n):self._active();self._check_source();return (self.admission.root/self.admission.inputs[n]['path']).read_bytes()
 def write_json(self,n,v):
  if self.fail:raise self.fail
  raw=encoded(v);(self.directory/'outputs'/n).write_bytes(raw);self._published_outputs[n]=sha(raw)
  if self.after:self.after(self)

class BoundaryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);root=Path(self.tmp.name);self.m=load();self.m._run_class=lambda:SyntheticRun;self.m._runtime=lambda root:{'python':'qualified','cpu_count':2,'packages':{},'lock_sha256':'7'*64}
  pkg=root/'tradingagents/research/onchain_replication';pkg.mkdir(parents=True)
  for name in ('population_batch_projection.py','population_assembly.py'):(pkg/name).write_bytes((HERE/name).read_bytes())
  (pkg/'environment.py').write_bytes(Path('tradingagents/research/onchain_replication/environment.py').read_bytes())
  self.m.__file__=str(pkg/'population_batch_projection.py');self.m.__package__='qualified_boundary'
  asm=types.ModuleType('qualified_boundary.population_assembly');asm.__file__=str(pkg/'population_assembly.py');sys.modules[asm.__name__]=asm;self.addCleanup(sys.modules.pop,asm.__name__,None)
  r=self.r=SyntheticRun();r.directory=root/'research_runs/synthetic';(r.directory/'outputs').mkdir(parents=True);r._published_outputs={};r._claim_sha256='8'*64;r.dead=False;r.bad_source=False;r.fail=None;r.after=None
  r.admission=types.SimpleNamespace(root=root,source='a'*40,registration_sha256='9'*64,experiment_id='synthetic',inputs={},experiment={'outputs':['pop','bind','assembly','projection'],'source_files':{str((pkg/n).relative_to(root)):sha((pkg/n).read_bytes()) for n in ('population_batch_projection.py','population_assembly.py','environment.py')},'runtime_hashes':{'locked':'f'*64}})
  p,b,a=fixture();self.result={'population':p,'binding':b,**a};self.plan={'schema_version':2,'projection_input':'policy','outputs':{'population':'pop','binding':'bind','assembly':'assembly','projection':'projection'}}
  for k,n in [('population','pop'),('binding','bind'),('assembly','assembly')]:r.write_json(n,self.result[k] if k!='assembly' else a)
  self.add('plan',self.plan);self.add('env',self.m._runtime(root));self.add('model',{'lookback_days':28,'mcm_input':32});self.add('training',{'batch_size':16});self.add('components',{'schema_version':1,'graphs':{}})
  self.add('policy',{'schema_version':1,'kind':'population-batch-projection-v1','environment_input':'env','model_input':'model','training_input':'training','components_input':'components'})
 def add(self,n,v):
  p=self.r.admission.root/(n+'.json');raw=encoded(v);p.write_bytes(raw);self.r.admission.inputs[n]={'path':p.name,'sha256':sha(raw)}
 def test_actual_boundary_joins_three_outputs_and_emits_fourth(self):
  self.m.publish_projection(self.r,'plan',self.plan,self.result)
  v=json.loads((self.r.directory/'outputs/projection').read_bytes())
  self.assertEqual(v['provenance']['source'],'a'*40);self.assertEqual(v['provenance']['original_outputs']['population']['sha256'],self.r._published_outputs['pop']);self.assertFalse(v['scientific_feature_admission'])
 def test_output_bytes_and_registry_drift_refused(self):
  for mutate in (lambda:(self.r.directory/'outputs/pop').write_bytes(b'{}'),lambda:self.r._published_outputs.__setitem__('bind','e'*64)):
   with self.subTest(mutation=mutate):
    old=(self.r.directory/'outputs/pop').read_bytes();saved=dict(self.r._published_outputs);mutate()
    with self.assertRaises(ValueError):self.m.publish_projection(self.r,'plan',self.plan,self.result)
    (self.r.directory/'outputs/pop').write_bytes(old);self.r._published_outputs=saved
  self.assertFalse((self.r.directory/'outputs/projection').exists())
 def test_source_runtime_config_and_wrong_type_refuse_before_write(self):
  with self.assertRaises(ValueError):self.m.publish_projection(object(),'plan',self.plan,self.result)
  for name,bad in [('env',{}),('training',{'batch_size':8}),('model',{'lookback_days':28,'mcm_input':31})]:
   old=(self.r.admission.root/(name+'.json')).read_bytes();self.add(name,bad)
   with self.assertRaises(ValueError):self.m.publish_projection(self.r,'plan',self.plan,self.result)
   self.add(name,json.loads(old))
  self.r.bad_source=True
  with self.assertRaises(ValueError):self.m.publish_projection(self.r,'plan',self.plan,self.result)
  self.assertFalse((self.r.directory/'outputs/projection').exists())
 def test_publication_failure_is_same_object_and_prefix_retained(self):
  error=MemoryError('test publication');self.r.fail=error
  try:self.m.publish_projection(self.r,'plan',self.plan,self.result)
  except BaseException as actual:self.assertIs(actual,error)
  else:self.fail('publication failure suppressed')
  self.assertEqual(set(self.r._published_outputs),{'pop','bind','assembly'})
 def test_postpublication_original_mutation_refuses_return(self):
  self.r.after=lambda r:(r.directory/'outputs/pop').write_bytes(b'{}')
  with self.assertRaises(ValueError):self.m.publish_projection(self.r,'plan',self.plan,self.result)
  self.assertTrue((self.r.directory/'outputs/projection').exists())
 def test_source_module_hash_missing_refuses(self):
  self.r.admission.experiment['source_files'].clear()
  with self.assertRaises(ValueError):self.m.publish_projection(self.r,'plan',self.plan,self.result)
if __name__=='__main__':unittest.main()
