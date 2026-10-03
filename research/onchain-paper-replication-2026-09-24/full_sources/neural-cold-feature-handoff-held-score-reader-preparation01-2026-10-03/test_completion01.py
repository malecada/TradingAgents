"""Actual stream finish AST; scalar substitutes, never numerical/Owner proof."""
import ast,json,hashlib,unittest,weakref,types
from pathlib import Path
HERE=Path(__file__).parent

def require(v,m):
 if not v:raise ValueError(m)
def load():
 t=ast.parse((HERE/'mcm_score_stream.py').read_text());c=next(x for x in t.body if isinstance(x,ast.ClassDef) and x.name=='MCMScoreStream');finish=next(x for x in c.body if isinstance(x,ast.FunctionDef) and x.name=='finish')
 helpers=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in ('_completion_identity','completed_evidence')]
 class FakeBatch:
  @staticmethod
  def _json(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
  @staticmethod
  def _write(fd,n,raw):raws[n]=raw;return hashlib.sha256(raw).hexdigest()
  @staticmethod
  def _read(fd,n,limit):return raws[n]
  @staticmethod
  def _close_after_failure(close,primary):close()
  META_LIMIT=8192
 raws={};ns={'require':require,'batch':FakeBatch,'_COMPLETED':weakref.WeakKeyDictionary(),'_directory_identity':lambda s:('qualified-directories',),'_directory_rejoin':lambda *a:None}
 exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='MCMScoreStream',bases=[],keywords=[],body=[finish],decorator_list=[])]+helpers,type_ignores=[])),'<actual-stream-finish>','exec'),ns)
 s=ns['MCMScoreStream']();s.n=1;s.k=32;s.cells=32;s.active=None;s.closed=False;s.root=Path('/synthetic/stream');s.owner='1'*64;s._imported=s._imported_pin=object();s.start_sha='2'*64;s.head='3'*64;s.fd=111
 s.batches=types.SimpleNamespace(closed=False,chunks=1,chunk_cells=32,start_sha='4'*64,finish=lambda:'5'*64)
 s._check=lambda:None;s._history_check=lambda *a:None
 def close():s.closed=True;s.batches.closed=True
 s.close=close
 return s,ns
class CompletionTests(unittest.TestCase):
 def test_success_has_noncaller_completion_evidence(self):
  s,ns=load();s.finish();self.assertIn('completed_evidence',ns,'actual successful completion capability missing')
  record=ns['completed_evidence'](s);self.assertIs(record[0][0],s._imported);self.assertEqual(record[1][-1:],b'\n')
 def test_history_failure_never_creates_success(self):
  s,ns=load();error=MemoryError('history');s._history_check=lambda *a:(_ for _ in ()).throw(error)
  with self.assertRaises(MemoryError):s.finish()
  self.assertNotIn(s,ns['_COMPLETED'])
 def test_close_failure_never_creates_success(self):
  s,ns=load();s.close=lambda:(_ for _ in ()).throw(OSError('close'))
  with self.assertRaises(OSError):s.finish()
  self.assertNotIn(s,ns['_COMPLETED'])
 def test_mutated_completed_stream_refuses(self):
  s,ns=load();s.finish();self.assertIn('completed_evidence',ns,'completed stream integrity check missing');s.cells=31
  with self.assertRaises(ValueError):ns['completed_evidence'](s)
if __name__=='__main__':unittest.main()
