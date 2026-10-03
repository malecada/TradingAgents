"""Exact scalar reducer plus genuine stdlib cleanup; no authority construction.
Break caught: unguarded add_note replaces an already selected fatal exception.
"""
import ast,copy,hashlib,json,pathlib,sys,unittest
HERE=pathlib.Path(__file__).resolve().parent
BASE=HERE.parent
OLD=BASE/'held-consumer-canonical-successor-preparation01-2026-10-03/original_dictionary.py'
IO=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source/tradingagents/research/onchain_replication/owned_io.py')
def reducer(path):
 tree=ast.parse(path.read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ImportedOriginal');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='with_evidence')
 branch=next(n for n in ast.walk(method) if isinstance(n,ast.If) and ast.unparse(n.test)=='primary is None')
 frame=ast.parse('def reduce(primary,error):\n return primary\n');fn=frame.body[0];fn.body.insert(0,copy.deepcopy(branch));ast.fix_missing_locations(frame)
 env={'fatal':io['_fatal']};exec(compile(frame,'<exact-with_evidence-reducer>','exec'),env);return env['reduce']
raw=IO.read_bytes();assert hashlib.sha256(raw).hexdigest()=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'
# Entire utility is stdlib-only, with no top-level execution beyond definitions.
io={'__name__':'bounded_owned_io_source'};exec(compile(raw,str(IO),'exec'),io)
records=[]
def raising_note(base,diagnostic,trace):
 class Selected(base):
  def add_note(self,note):trace.append('note');raise diagnostic
 return Selected('first')
class Cases(unittest.TestCase):
 def test_original_fatal_identity_after_note_raises(self):
  trace=[];p=raising_note(MemoryError,RuntimeError('note failed'),trace)
  try:actual=reduce(p,ValueError('later recheck'))
  except BaseException as escaped:actual=escaped
  self.assertIs(actual,p);self.assertEqual(trace,['note'])
 def test_first_fatal_survives_every_note_failure(self):
  for first in (MemoryError,SystemExit,KeyboardInterrupt):
   for evidence in (ValueError,MemoryError,SystemExit,KeyboardInterrupt,io['CleanupFailure']):
    for diagnostic in (ValueError,MemoryError,SystemExit,KeyboardInterrupt,BaseException,io['CleanupFailure']):
     with self.subTest(first=first.__name__,evidence=evidence.__name__,diagnostic=diagnostic.__name__):
      trace=[];d=diagnostic('note failed');p=raising_note(first,d,trace)
      selected=reduce(p,evidence('recheck'));self.assertIs(selected,p);self.assertEqual(trace,['note'])
      records.append({'case':'original_fatal','first':first.__name__,'later':evidence.__name__,'diagnostic':diagnostic.__name__,'selected':'original','notes':len(trace)})
 def test_ordinary_primary_keeps_ordinary_diagnostic(self):
  for diagnostic in (ValueError,RuntimeError,io['CleanupFailure']):
   trace=[];p=raising_note(ValueError,diagnostic('note failed'),trace)
   self.assertIs(reduce(p,ValueError('recheck')),p);self.assertEqual(trace,['note'])
 def test_first_diagnostic_fatal_promoted(self):
  for diagnostic in (MemoryError,SystemExit,KeyboardInterrupt,BaseException):
   trace=[];d=diagnostic('note failed');p=raising_note(ValueError,d,trace)
   self.assertIs(reduce(p,ValueError('recheck')),d);self.assertEqual(trace,['note'])
 def test_later_fatal_promoted_without_note(self):
  for second in (MemoryError,SystemExit,KeyboardInterrupt):
   trace=[];p=raising_note(ValueError,RuntimeError('note must not run'),trace);e=second('recheck')
   self.assertIs(reduce(p,e),e);self.assertIs(e.__cause__,p);self.assertEqual(trace,[])
 def test_no_primary_retains_recheck(self):
  for kind in (ValueError,MemoryError,SystemExit,io['CleanupFailure']):
   e=kind('recheck');self.assertIs(reduce(None,e),e)
 def test_successful_notes_and_ordinary_primary(self):
  for kind in (ValueError,MemoryError,SystemExit):
   p=kind('first');self.assertIs(reduce(p,ValueError('later')),p)
   self.assertEqual(p.__notes__,['post-callback evidence/authority check failed: ValueError'])
 def test_cleanup_runs_once_after_selected_fatal(self):
  for first in (MemoryError,SystemExit):
   for closing in (ValueError,MemoryError,SystemExit):
    trace=[];p=raising_note(first,RuntimeError('note'),trace);e=ValueError('later');c=closing('cleanup')
    def close():trace.append('close');raise c
    try:
     try:raise reduce(p,e)
     finally:io['_release'](close)
    except BaseException as actual:self.assertIs(actual,p)
    else:self.fail('selected fatal lost')
    self.assertEqual(trace,['note','close'])
 def test_first_diagnostic_fatal_survives_later_cleanup(self):
  trace=[];d=MemoryError('first actual fatal');p=raising_note(ValueError,d,trace)
  def close():trace.append('close');raise SystemExit('later cleanup fatal')
  try:
   try:raise reduce(p,ValueError('recheck'))
   finally:io['_release'](close)
  except BaseException as actual:self.assertIs(actual,d)
  else:self.fail('first diagnostic fatal lost')
  self.assertEqual(trace,['note','close'])
 def test_cleanup_fatal_promoted_after_ordinary(self):
  trace=[];p=ValueError('first');c=MemoryError('cleanup first fatal')
  def close():trace.append('close');raise c
  try:
   try:raise reduce(p,ValueError('recheck'))
   finally:io['_release'](close)
  except BaseException as actual:self.assertIs(actual,c)
  else:self.fail('cleanup fatal lost')
  self.assertEqual(trace,['close'])
if __name__=='__main__':
 source=OLD if sys.argv[1]=='red' else HERE/'original_dictionary.py'
 reduce=reducer(source)
 # RED is intentionally one decisive failed assertion, not a manufactured success.
 suite=unittest.TestSuite([Cases('test_original_fatal_identity_after_note_raises')]) if sys.argv[1]=='red' else unittest.defaultTestLoader.loadTestsFromTestCase(Cases)
 with (HERE/(sys.argv[1].upper()+'01.log')).open('x') as log:
  result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
 report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'scalar_cases':records,'utility_sha256':hashlib.sha256(raw).hexdigest(),'genuine_authority_executed':False,'numerical_imports':False}
 with (HERE/(sys.argv[1].upper()+'01.json')).open('x') as out:json.dump(report,out,indent=2,sort_keys=True);out.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='scalar_cases'}));sys.exit(0 if result.wasSuccessful() else 1)
