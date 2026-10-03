"""Stdlib AST and opaque control checks only. No authority stand-ins or numerics."""
import ast,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('financial_fixture_source',P/'financial_wrapper_fixture.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Checks(unittest.TestCase):
 def test_no_numerical_imports(self):
  self.assertFalse({'torch','numpy','scipy'}&set(sys.modules))
  tree=ast.parse((P/'financial_wrapper_fixture.py').read_text())
  for node in tree.body:
   if isinstance(node,ast.Import):self.assertFalse({'torch','numpy','scipy'}&{x.name for x in node.names})
   if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith(('torch','numpy','scipy')))
 def test_all_python_parses_without_import(self):
  for p in P.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
 def test_original_source_config_pins(self):
  self.assertEqual(hashlib.sha256((P/'model.json').read_bytes()).hexdigest(),m.MODEL)
  self.assertEqual(hashlib.sha256((P/'training.json').read_bytes()).hexdigest(),m.TRAINING)
  self.assertEqual(hashlib.sha256((P/'candidate02/financial_execution.py').read_bytes()).hexdigest(),m.CANDIDATE)
  t=json.loads((P/'training.json').read_bytes());self.assertEqual((t['epochs'],t['batch_size']),(100,16));self.assertEqual(json.loads((P/'model.json').read_bytes())['lookback_days'],28)
  self.assertEqual(m.F32,{'atol':1e-6,'rtol':1e-5})
 def test_full_conditional_inverse(self):
  for name,steps in json.loads((P/'adaptations.json').read_bytes()).items():
   source=(P/name).read_text()
   for step in reversed(steps):self.assertEqual(source.count(step['after']),step.get('count',1));source=source.replace(step['after'],step['before'])
   self.assertEqual(source,(P/('job.baseline.py' if name=='job.py' else 'candidate02/replay.py')).read_text())
 def test_every_unfilled_phase_refuses(self):
  values=json.loads((P/'PHASE_TEMPLATES01.json').read_bytes())['templates'];self.assertEqual(len(values),18)
  for value in values:
   with self.subTest(phase=value['phase'],task=value['task'],execution=value['execution']),self.assertRaises(m.Unavailable):m.validate_plan(value)
 def test_phase_shape_controls_are_only_metadata(self):
  # These are scalar parser inputs only, never Run/Owner/Binding objects.
  for template in json.loads((P/'PHASE_TEMPLATES01.json').read_bytes())['templates']:
   value={**template,'experiment':'opaque-unregistered','cell_id':'opaque-unregistered','namespace':'opaque-unregistered'}
   self.assertEqual(m.validate_plan(value),value)
   for key,bad in [('phase','reopen'),('task','other'),('execution','automatic'),('namespace','../foreign'),('cell_id',None)]:
    with self.subTest(key=key),self.assertRaises(m.Unavailable):m.validate_plan({**value,key:bad})
   if value['phase']=='continue100':
    with self.assertRaises(m.Unavailable):m.validate_plan({**value,'reference_input':None})
 def test_job_resource_schema(self):
  job=json.loads((P/'JOB_TEMPLATE01.json').read_bytes());m.schema(job)
  for key,value in [('wall_seconds',1801),('memory_max_bytes',4*1024**3),('disk_floor_bytes',9*1024**3),('native_unit_limits',{'file_size_bytes':m.FILE+1})]:
   bad=copy.deepcopy(job);bad['resources'][key]=value
   with self.subTest(key=key),self.assertRaises(m.Unavailable):m.schema(bad)
 def test_real_gates_precede_tensor_import(self):
  tree=ast.parse((P/'financial_wrapper_fixture.py').read_text());execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
  self.assertIsInstance(execute.body[0],ast.Assign);self.assertEqual(execute.body[0].value.func.id,'authorize')
  code=ast.get_source_segment((P/'financial_wrapper_fixture.py').read_text(),execute)
  self.assertIn('training.fit_cell(',code);self.assertIn('evaluation.recover_completed_model(',code);self.assertIn("raise PlannedInterruption",code)
  self.assertNotIn("'epochs':1",code);self.assertNotIn('._reserve(',code)
  auth=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='authorize');text=ast.unparse(auth)
  for part in ('type(run) is ResearchRun','job._command(args, \'worker\')','run._check_source()','run._check_inputs()','resources.assert_guarded_worker','live[\'owner_identity\'] == owner'):self.assertIn(part,text)
 def test_no_mutable_authority_or_attach_route(self):
  tree=ast.parse((P/'financial_wrapper_fixture.py').read_text());names=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
  self.assertFalse({'Owner','Binding','ResearchRun','attach','rebaseline'}&set(names))
  for n in ast.walk(tree):
   if isinstance(n,ast.Call):self.assertNotIn(ast.unparse(n.func),('ResearchRun.start','os.system','subprocess.run','shutil.rmtree','patch','mock'))
 def test_exact_candidate_copies_and_selected_no_attach(self):
  original=P.parent/'financial-streamed-execution-candidate02-2026-10-02'
  for p in (P/'candidate02').glob('*.py'):self.assertEqual(p.read_bytes(),(original/p.name).read_bytes())
  self.assertNotIn('def attach(', (P/'candidate02/financial_execution.py').read_text())
 def test_source_map_bytes_without_source_import(self):
  root=P.parents[3];installation=json.loads((P/'INSTALLATION01.json').read_bytes());closure=json.loads((P/'SOURCE_CLOSURE01.json').read_bytes());self.assertEqual(set(installation['sources']),set(closure['installed']))
  for target,record in installation['sources'].items():self.assertEqual(hashlib.sha256((root/record['source']).read_bytes()).hexdigest(),record['sha256']);self.assertEqual(record['sha256'],closure['installed'][target])
 def test_new_replay_branch_keeps_fixed_tolerance(self):
  source=(P/'replay.py').read_text();self.assertIn("task=manifest.get('task','classification')",source);self.assertIn("task not in ('classification','regression')",source);self.assertIn('atol=1e-5,rtol=1e-4',source)
 def test_genuine_runtime_template_refuses(self):
  with self.assertRaises(m.Unavailable):m.runtime_check(P,json.loads((P/'RUNTIME_TEMPLATE01.json').read_bytes()))
if __name__=='__main__':unittest.main(verbosity=2)
