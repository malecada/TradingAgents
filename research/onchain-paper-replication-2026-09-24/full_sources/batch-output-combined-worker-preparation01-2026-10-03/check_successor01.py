import ast,copy,unittest,importlib.util
from pathlib import Path
P=Path(__file__).parent
spec=importlib.util.spec_from_file_location('contract',P/'check_contract01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Checks(unittest.TestCase):
 def test_original201(self):
  c,r,p=m.closure();c['source_files'].pop('code/200.py');c['package_files'].pop('code/1.py');c.update(schema_version=1,kind='selected-held-transfer-source-closure-v1',implementation_source_count=201,package_count=150);r=c['source_files']|c['auxiliary_source_files']
  self.assertEqual(m.load()['_transfer_closure'](c,r,c['package_files']),c['source_files'])
 def test_join_refusals(self):
  for variant in range(6):
   c,r,p=m.closure()
   if variant==0:r['foreign']='a'*64
   if variant==1:r[next(iter(r))]='b'*64
   if variant==2:p=dict(p);p.pop(next(iter(p)))
   if variant==3:c['source_files']['../bad']=c['source_files'].pop('code/200.py');r=c['source_files']|c['auxiliary_source_files']
   if variant==4:c['auxiliary_source_files']['code/200.py']=c['auxiliary_source_files'].pop('aux/0.json');r=c['source_files']|c['auxiliary_source_files']
   if variant==5:c['package_files'].pop('tradingagents/research/onchain_replication/completed_f32.py')
   with self.assertRaises(ValueError):m.load()['_transfer_closure'](c,r,p)
 def test_original_policies(self):
  f=m.load()['_policy'];g=['a'*64,'b'*64];p=dict(schema_version=1,kind=m.load()['KIND'],targets={g[0]:{'output':'a.json'},g[1]:{'output':'b.json'}},part_bytes=512,max_read_bytes=768,max_members=2)
  self.assertIs(f(p,g,['a.json','b.json']),p)
  p=dict(p,schema_version=2,kind=m.load()['TRANSFER_KIND'],population_input='pop',source_closure_input='src',network_release_input='rel');self.assertIs(f(p,g,['a.json','b.json']),p)
 def test_raw_held_extent(self):
  f=m.load()['_combined_budget'];p={'targets':{'a':{},'b':{}},'max_read_bytes':768,'max_members':2};f(p,{'a':2,'b':3},64)
  for field,value in [('max_read_bytes',767),('max_members',1)]:
   q=dict(p);q[field]=value
   with self.assertRaises(ValueError):f(q,{'a':2,'b':3},64)
  for chunk in [0,True,64.0]:
   with self.assertRaises(ValueError):f(p,{'a':2,'b':3},chunk)
 def test_numerical_body_and_default_factory(self):
  for name,funcs in [('resource_fixture.py',['_execute_original','admitted','selection']),('held_score_consumer.py',['consume','_read_all','_TransferWorker','transfer_worker','_route'])]:
   def nodes(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
   old=nodes(P/(name+'.baseline'));new=nodes(P/name)
   for f in funcs:self.assertEqual(old[f],new[f])
  self.assertEqual((P/'completed_f32.py').read_bytes(),(P/'completed_f32.py.baseline').read_bytes())
 def test_actual_dispatch_structure(self):
  h=ast.parse((P/'held_score_consumer.py').read_bytes());r=ast.parse((P/'resource_fixture.py').read_bytes())
  methods={n.name:n for n in h.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  raw=ast.unparse(methods['_RawWorker']);self.assertIn('completed_f32.completed_worker',raw);self.assertIn('type(self.context) is archive_non_tail.Context',raw);self.assertIn('self.cm.__exit__',raw)
  pre=ast.unparse(methods['_combined_preflight']);self.assertIn('type(run) is ResearchRun',pre);self.assertIn('completed_f32._selected',pre);self.assertIn('matching_owner._guard',pre)
  worker=next(n for n in r.body if isinstance(n,ast.FunctionDef) and n.name=='execute');self.assertIn('held_score_consumer.raw_transfer_worker',ast.unparse(worker))
 def test_inverse_bytes(self):
  s=(P/'held_score_consumer.py').read_text();s=s[:s.index('\n\n\ndef _combined_closure')]+ '\n'
  s=s.replace("COMBINED_KIND='selected-combined-f64-f32-source-closure-v2'\nRAW_KIND='original-import-held-score-completed-f32-v3'\n",'')
  start=s.index("    if type(p) is dict and type(p.get('schema_version')) is int and p['schema_version']==3:");end=s.index("    if type(p) is dict",start+5);s=s[:start]+s[end:]
  s=s.replace("    if p['schema_version'] in (2,3):_worker_current(run,p)","    if p['schema_version']==2:_worker_current(run,p)")
  s=s.replace("    if type(value) is dict and value.get('kind')==COMBINED_KIND:return _combined_closure(value,registered,required)\n",'').replace('def _transfer_preflight_legacy(','def transfer_preflight(').replace("    if p['schema_version']==3:return _raw_current(run,p)\n",'')
  self.assertEqual(s,(P/'held_score_consumer.py.baseline').read_text())
  s=(P/'resource_fixture.py').read_text().replace("if policy['schema_version'] in (2,3):","if policy['schema_version']==2:")
  begin=s.index("    _,policy=held_score_consumer._transfer_json");end=s.index('    with held_score_consumer.transfer_worker',begin);s=s[:begin]+s[end:]
  self.assertEqual(s,(P/'resource_fixture.py.baseline').read_text())
if __name__=='__main__':unittest.main()
