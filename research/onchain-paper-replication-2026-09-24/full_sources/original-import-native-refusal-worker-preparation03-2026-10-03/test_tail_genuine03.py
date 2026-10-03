"""Extracted actual outer finalization; synthetic stdlib receipts only."""
import ast,os,pathlib,types,unittest
D=pathlib.Path(__file__).resolve().parent;OLD=D.parent/'original-import-native-refusal-worker-preparation01-2026-10-03'
SOURCE=pathlib.Path(os.environ.get('OUTER_SOURCE',D/'refusal_outer01.py'))
import hashlib,importlib.util,json
rows=json.loads((OLD/'source_inventory01.json').read_text())['source_inventory'];row=next(r for r in rows if r['target']=='tradingagents/research/onchain_replication/owned_io.py');path=D.parents[3]/row['origin'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
spec=importlib.util.spec_from_file_location('genuine_source_only_owned_io',path);owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned);CleanupFailure=owned.CleanupFailure

def exercise(*,primary=None,post_error=None,restore_errors=(),save_error=None):
 tree=ast.parse(SOURCE.read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');guard=next(n for n in run.body if isinstance(n,ast.Try) and any(isinstance(v,ast.For) and 'signal_handlers.items' in ast.unparse(v) for v in n.finalbody));start=next(i for i,v in enumerate(guard.finalbody) if isinstance(v,ast.Try) and 'publish_post_tail(root, watch, save)' in ast.unparse(v));tail=guard.finalbody[start:]
 selector=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='select');ns={};exec(compile(ast.Module(body=[selector],type_ignores=[]),'actual select','exec'),ns)
 receipts={'terminal.json':{'status':'passed'}};events=[];state={'primary':primary};errors=list(restore_errors)
 def retain(error):state['primary']=ns['select'](state['primary'],error,CleanupFailure);env['primary']=state['primary']
 def publish(*args):
  events.append('post-tail')
  if post_error is not None:raise post_error
 def restore(*args):
  events.append('restore')
  error=errors.pop(0) if errors else None
  if error is not None:raise error
 def save(name,value):
  events.append('save:'+name)
  if save_error is not None:raise save_error
  if name in receipts:raise FileExistsError(name)
  receipts[name]=value
 env={'root':None,'watch':None,'save':save,'publish_post_tail':publish,'primary':primary,'result':{},'authenticate_post_tail':lambda *a:{'synthetic':True},'identity':'synthetic-unclaimed','entry':{'job_resources':{}},'source':'s'*40,'retain':retain,'signal_handlers':{2:None,15:None},'signal':types.SimpleNamespace(signal=restore)}
 exec(compile(ast.Module(body=tail,type_ignores=[]),'actual final tail','exec'),env)
 return state['primary'],receipts,events
class Tests(unittest.TestCase):
 def test_ordinary_restore_marker_after_all_attempts(self):
  error=OSError('restore');actual,receipts,events=exercise(restore_errors=(error,None));self.assertIs(actual,error);self.assertEqual(receipts['terminal.json'],{'status':'passed'});self.assertEqual(receipts['post-terminal-failure.json']['error_type'],'OSError');self.assertEqual(events,['post-tail','restore','restore','save:post-terminal-failure.json'])
 def test_first_fatal_preserved_in_marker_and_raise_selection(self):
  first=MemoryError('first');actual,r,e=exercise(primary=first,restore_errors=(OSError('later'),KeyboardInterrupt('last')));self.assertIs(actual,first);self.assertEqual(r['post-terminal-failure.json']['error_type'],'MemoryError');self.assertEqual(e.count('restore'),2)
 def test_restore_fatal_supersedes_ordinary_posttail(self):
  fatal=KeyboardInterrupt('first fatal');actual,r,e=exercise(post_error=ValueError('post'),restore_errors=(fatal,MemoryError('later fatal')));self.assertIs(actual,fatal);self.assertEqual(r['post-terminal-failure.json']['error_type'],'KeyboardInterrupt');self.assertEqual(e.count('save:post-terminal-failure.json'),1)
 def test_failed_marker_does_not_mask_first_fatal(self):
  fatal=MemoryError('restore');actual,r,e=exercise(restore_errors=(fatal,None),save_error=CleanupFailure('write'));self.assertIs(actual,fatal);self.assertNotIn('post-terminal-failure.json',r);self.assertEqual(e.count('restore'),2);self.assertEqual(e.count('save:post-terminal-failure.json'),1)
 def test_marker_cleanup_failure_replaces_ordinary(self):
  cleanup=CleanupFailure('write');actual,r,e=exercise(restore_errors=(OSError('restore'),None),save_error=cleanup);self.assertIs(actual,cleanup)
 def test_success_retains_original_receipt_and_no_failure_marker(self):
  actual,r,e=exercise();self.assertIsNone(actual);self.assertEqual(r,{'terminal.json':{'status':'passed'}});self.assertEqual(e,['post-tail','restore','restore'])
 def test_posttail_failure_one_marker(self):
  error=ValueError('post');actual,r,e=exercise(post_error=error);self.assertIs(actual,error);self.assertEqual(r['post-terminal-failure.json']['error_type'],'ValueError');self.assertEqual(e,['post-tail','restore','restore','save:post-terminal-failure.json'])
if __name__=='__main__':unittest.main(verbosity=2)
