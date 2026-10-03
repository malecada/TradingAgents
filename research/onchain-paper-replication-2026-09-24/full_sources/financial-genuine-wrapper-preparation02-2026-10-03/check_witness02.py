"""Exact prior/current handlers and scalar cursor predicates, no authority doubles."""
import ast,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'financial-genuine-wrapper-preparation01-2026-10-03'
spec=importlib.util.spec_from_file_location('financial_wrapper02',P/'financial_wrapper_fixture.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RESULTS={'qualification':'stdlib actual-source handlers and scalar metadata only; no Run/Owner/Binding/model/tensor/checkpoint/native fixture','fatal':[],'cursor':[]}
def handler(path):
 tree=ast.parse(path.read_text());execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');outer=next(n for n in execute.body if isinstance(n,ast.Try))
 test=ast.FunctionDef(name='exact_handler',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='primary'),ast.arg(arg='writer'),ast.arg(arg='directory')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[ast.Assign(targets=[ast.Name(id='_immutable',ctx=ast.Store())],value=ast.Name(id='writer',ctx=ast.Load())),ast.Try(body=[ast.Raise(exc=ast.Name(id='primary',ctx=ast.Load()),cause=None)],handlers=[copy.deepcopy(outer.handlers[0])],orelse=[],finalbody=[])],decorator_list=[])
 ns={'_select_failure':m._select_failure};exec(compile(ast.fix_missing_locations(ast.Module([test],[])),str(path)+':exact_failure_handler','exec'),ns);return ns['exact_handler']
class Checks(unittest.TestCase):
 def test_actual_review_fatal_witness_red_green(self):
  versions={'prior':handler(OLD/'financial_wrapper_fixture.py'),'successor':handler(P/'financial_wrapper_fixture.py')}
  red=0
  for version,call in versions.items():
   for first,last in [(MemoryError('first'),SystemExit('later')),(SystemExit('first'),MemoryError('later')),(MemoryError('first'),OSError('ordinary')),(ValueError('ordinary'),MemoryError('later fatal'))]:
    calls=[]
    def writer(*args):calls.append(args[0]);raise last
    try:call(first,writer,P/'opaque-control')
    except BaseException as actual:
     expected=first if isinstance(first,MemoryError) or not isinstance(first,Exception) else last if isinstance(last,MemoryError) or not isinstance(last,Exception) else first
     ok=actual is expected;RESULTS['fatal'].append({'version':version,'first':type(first).__name__,'later':type(last).__name__,'observed':type(actual).__name__,'expected_identity':ok,'writer_calls':len(calls)})
     if version=='successor':self.assertTrue(ok)
     else:red+=not ok
    else:self.fail('exception swallowed')
    self.assertEqual(len(calls),1)
  self.assertEqual(red,2)
 def test_first_fatal_through_notes_repr_and_reporting(self):
  call=handler(P/'financial_wrapper_fixture.py')
  class FatalNote(MemoryError):
   def add_note(self,n):raise SystemExit('diagnostic later fatal')
  class OrdinaryNote(ValueError):
   def add_note(self,n):raise MemoryError('diagnostic first fatal')
  class BrokenRepr(OSError):
   def __repr__(self):raise SystemExit('repr fatal')
  class BrokenStr(MemoryError):
   def __str__(self):raise SystemExit('render later fatal')
  for first,last,expected_type,identity in [(FatalNote('original'),SystemExit('publication'),FatalNote,True),(MemoryError('original'),BrokenRepr(),MemoryError,True),(OrdinaryNote('original'),OSError('ordinary write'),MemoryError,False),(ValueError('ordinary'),BrokenRepr(),SystemExit,False),(BrokenStr(),OSError('unused writer'),BrokenStr,True)]:
   calls=[]
   def writer(*a):calls.append(1);raise last
   with self.subTest(first=type(first).__name__,last=type(last).__name__):
    try:call(first,writer,P/'opaque-control')
    except BaseException as actual:self.assertIsInstance(actual,expected_type);self.assertEqual(actual is first,identity)
    else:self.fail('exception swallowed')
    self.assertLessEqual(len(calls),1)
 def test_actual_review_cursor_red_green(self):
  tree=ast.parse((P/'candidate02/training.py').read_text());fit=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fit_cell');body=next(n for n in fit.body if isinstance(n,ast.Try)).body
  predicate=next(n for n in body if isinstance(n,ast.If) and 'checkpoint cursor outside registered fit' in ast.unparse(n));loop=next(n for n in body if isinstance(n,ast.While))
  code=compile(ast.Expression(predicate.test),'original_cursor','eval');condition=compile(ast.Expression(loop.test),'original_loop','eval')
  for epoch in (0,1,2,99,100,101):
   scope={'epoch':epoch,'batch':0,'epochs':100,'batches':1};old_reject=eval(code,scope);enters=eval(condition,scope)
   state={'epoch':epoch,'batch':0,'epoch_loss':0.,'epoch_count':0,'logs':[{'epoch':0,'loss':.25,'examples':16,'seed':11}]}
   try:m._one_epoch_state(state);new_reject=False
   except m.Unavailable:new_reject=True
   self.assertEqual(new_reject,epoch!=1);RESULTS['cursor'].append({'epoch':epoch,'old_reject':old_reject,'old_loop':enters,'new_reject':new_reject})
  self.assertFalse(RESULTS['cursor'][-2]['old_reject']);self.assertFalse(RESULTS['cursor'][-2]['old_loop']);self.assertTrue(RESULTS['cursor'][-2]['new_reject'])
 def test_scalar_cursor_finite_controls(self):
  valid={'epoch':1,'batch':0,'epoch_loss':0.,'epoch_count':0,'logs':[{'epoch':0,'loss':.25,'examples':16,'seed':11}]};m._one_epoch_state(valid)
  for key,value in [('epoch',True),('batch',True),('batch',1),('epoch_count',1),('epoch_loss',1),('logs',[]),('logs',[{'epoch':0,'loss':float('nan'),'examples':16,'seed':11}]),('logs',[{'epoch':0,'loss':.25,'examples':15,'seed':11}])]:
   with self.subTest(key=key),self.assertRaises(m.Unavailable):m._one_epoch_state({**valid,key:value})
 def test_scalar_phase_controls(self):
  old=json.loads((P/'PHASE_TEMPLATES01.json').read_bytes())['templates'][1];old={**old,'phase':'interrupt1','experiment':'opaque-parent','cell_id':'opaque-cell','namespace':'opaque-scope'}
  current={**old,'phase':'continue100','experiment':'opaque-current','prior_input':'opaque-prior','reference_input':'opaque-reference'}
  m._interrupt_case(current,old,'opaque-parent')
  for key,value in [('phase','complete100'),('phase','agreement'),('task','regression' if old['task']=='classification' else 'classification'),('execution','selected' if old['execution']=='eager' else 'eager'),('cell_id','other'),('experiment','other')]:
   with self.subTest(key=key),self.assertRaises(m.Unavailable):m._interrupt_case(current,{**old,key:value},'opaque-parent')
 def test_real_boundary_order_and_parent_joins(self):
  text=(P/'financial_wrapper_fixture.py').read_text();tree=ast.parse(text);functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)};execute=ast.get_source_segment(text,functions['execute'])
  self.assertLess(execute.index('loaded=checkpoints.load_checkpoint'),execute.index('_one_epoch_state(loaded)'));self.assertLess(execute.index('_one_epoch_state(loaded)'),execute.index('training.fit_cell('));self.assertLess(execute.index('reference_state=_reference_state'),execute.index('training.fit_cell('))
  parent=ast.get_source_segment(text,functions['_interrupt_parent'])
  for part in ("inputs['execution_job']","schema(job)","_interrupt_case(p,old,parent)","fit/'claim.json'","fit/'failed.json'","fit/'schedule.json'","'interrupted-checkpoint.json'","claim_info['sha256']==sha(raw)"):
   self.assertIn(part,parent)
  self.assertIn("state=reference_state",execute)
 def test_complete_text_inverse_and_closure(self):
  s=(P/'financial_wrapper_fixture.py').read_text()
  for step in reversed(json.loads((P/'fixture_adaptations02.json').read_bytes())):
   self.assertEqual(s.count(step['after']),1);s=s.replace(step['after'],step['before'])
  self.assertEqual(s,(OLD/'financial_wrapper_fixture.py').read_text())
  before=json.loads((OLD/'SOURCE_CLOSURE01.json').read_bytes())['installed'];after=json.loads((P/'SOURCE_CLOSURE01.json').read_bytes())['installed'];self.assertEqual(len(after),194);self.assertEqual(set(before),set(after));self.assertEqual([k for k in before if before[k]!=after[k]],['tradingagents/research/onchain_replication/financial_wrapper_fixture.py'])
  for p in (P/'candidate02').glob('*.py'):self.assertEqual(p.read_bytes(),(OLD/'candidate02'/p.name).read_bytes())
 def test_no_numerics_or_authority_class(self):
  self.assertFalse(set(sys.modules)&{'torch','numpy','scipy','pandas'})
  tree=ast.parse((P/'financial_wrapper_fixture.py').read_text());self.assertFalse({n.name for n in ast.walk(tree) if isinstance(n,ast.ClassDef)}&{'Run','ResearchRun','Binding','Owner'})
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks));RESULTS['tests_run']=result.testsRun;RESULTS['success']=result.wasSuccessful();(P/'WITNESS_RESULTS02.json').write_text(json.dumps(RESULTS,sort_keys=True,indent=2)+'\n');raise SystemExit(not result.wasSuccessful())
