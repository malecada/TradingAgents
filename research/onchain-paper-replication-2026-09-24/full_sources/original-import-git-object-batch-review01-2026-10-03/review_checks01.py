"""Independent bounded source testing; tiny disposable Git objects, no research authority."""
import ast,hashlib,json,os,selectors,subprocess,sys,tempfile,time,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;ROOT=BASE.parents[2];A=BASE/'original-import-git-object-batch-candidate01-2026-10-03'
OWNED=BASE/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py'
ns={};exec(compile(ast.parse(OWNED.read_bytes()),str(OWNED),'exec'),ns)
def require(ok,msg):
 if not ok:raise ValueError(msg)
def extract(name,env):
 f=next(n for n in ast.parse((A/'candidate01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name==name)
 # Bind original imports explicitly to stdlib and the exact pinned cleanup source.
 f.body=[n for n in f.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
 exec(compile(ast.Module(body=[f],type_ignores=[]),'actual '+name,'exec'),env);return env[name]
class Review(unittest.TestCase):
 def test_manifest_origins_and_module_parity(self):
  for x in json.loads((A/'MANIFEST01.json').read_text())['files']:
   b=(A/x['path']).read_bytes();self.assertEqual(len(b),x['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),x['sha256'])
  for x in json.loads((A/'origins01.json').read_text())['references']:
   b=(ROOT/x['path']).read_bytes();self.assertEqual(len(b),x['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),x['sha256'])
  old=ast.parse((A/'baseline.py').read_text());new=ast.parse((A/'candidate01.py').read_text());orig=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='original_source_blobs')
  new.body=[orig if isinstance(n,ast.FunctionDef) and n.name=='original_source_blobs' else n for n in new.body if not(isinstance(n,ast.FunctionDef) and n.name in {'_original_git_batch','_original_batch_rows'})]
  self.assertEqual(ast.dump(new),ast.dump(old))
 def test_real_tiny_local_git_batch_fresh_binary_order_and_missing(self):
  env={'require':require,'subprocess':subprocess,'os':os,'selectors':selectors,'time':time,'_cleanup':ns['_cleanup'],'hashlib':hashlib}
  batch=extract('_original_git_batch',env);parse=extract('_original_batch_rows',env)
  with tempfile.TemporaryDirectory(prefix='synthetic-source-git-review-') as name:
   root=Path(name);subprocess.run(['git','init','--bare','--quiet',str(root)],check=True,timeout=5)
   bodies=[('synthetic-'+str(i)+'\n\x00blob\n').encode() for i in range(26)]
   ids=[subprocess.check_output(['git','hash-object','-w','--stdin'],input=b,cwd=root,timeout=5).strip() for b in bodies]
   requests=b'\n'.join(ids)+b'\n';items=[('p%02d'%i,hashlib.sha256(b).hexdigest()) for i,b in enumerate(bodies)]
   for _ in range(2):
    raw=batch(root,requests);rows=parse(raw,items);self.assertEqual(rows,[{'path':n,'sha256':h,'bytes':len(b)} for (n,h),b in zip(items,bodies)])
   raw=batch(root,b'0'*40+b'\n')
   with self.assertRaises(ValueError):parse(raw,[('missing',hashlib.sha256(b'x').hexdigest())])
   with self.assertRaises(ValueError):batch(root,b'x'*65537)
  print('Actual tiny local Git transport only:26 new synthetic blobs,2 fresh batch invocations plus missing-object refusal; no commits or research authority')
 def test_parser_aggregate_and_order_refusal(self):
  parse=extract('_original_batch_rows',{'require':require,'hashlib':hashlib})
  def frame(b):return b'a'*40+b' blob '+str(len(b)).encode()+b'\n'+b+b'\n'
  items=[('a',hashlib.sha256(b'a').hexdigest()),('b',hashlib.sha256(b'b').hexdigest())]
  with self.assertRaises(ValueError):parse(frame(b'b')+frame(b'a'),items)
  # Header proves aggregate refusal without allocating source-sized bodies.
  raw=b'a'*40+b' blob 4194305\n'
  with self.assertRaises(ValueError):parse(raw,[('p','f'*64)])
 def test_cleanup_recursion_qualification_is_explicit(self):
  primary=RecursionError('first');later=OSError('close')
  def close():raise later
  with self.assertRaises(ns['CleanupFailure']) as caught:ns['_cleanup']((close,),primary=primary)
  self.assertIn(primary,caught.exception.failures);self.assertIn(later,caught.exception.failures)
 def test_no_numerical_imports(self):self.assertFalse(any(k.split('.')[0] in {'numpy','torch','scipy','tradingagents','pandas','pyarrow'} for k in sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
