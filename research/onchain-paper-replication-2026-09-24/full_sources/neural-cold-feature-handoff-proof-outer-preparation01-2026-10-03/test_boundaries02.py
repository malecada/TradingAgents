"""Stdlib tiny-file/source counterexamples; no genuine OS/scientific claims."""
import ast,copy,io,json,os,tempfile,unittest,zipfile
from pathlib import Path
import proof_raw01 as raw
import proof_outer01 as outer
import proof_release01 as release
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_source_compile_without_import(self):
  for f in P.glob('*.py'):compile(f.read_text(),str(f),'exec')
 def test_strict_json(self):
  for b in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":Infinity}'):
   with self.assertRaises(ValueError):raw.parse(b)
 def test_new_metadata_bound_original_document_distinction(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'original.json').write_text(json.dumps({'value':'x'*9000}))
   with self.assertRaises(ValueError):raw.metadata(p,'original.json')
   self.assertEqual(len(raw.document(p,'original.json')['value']),9000)
 def test_reference_mutation(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'x.json').write_text('{"v":1}');r=raw.ref(p,'x.json',kind='metadata');self.assertEqual(raw.deref(p,r),{'v':1})
   (p/'x.json').write_text('{"v":2}')
   with self.assertRaises(ValueError):raw.deref(p,r)
 def test_redirection_hardlink_and_size_refuse(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'file').write_bytes(b'abc');(p/'link').symlink_to(p/'file')
   with self.assertRaises(ValueError):raw.body(p,'link')
   with self.assertRaises(ValueError):raw.body(p,'file',2)
   os.link(p/'file',p/'hard')
   with self.assertRaises(ValueError):raw.body(p,'file')
 def test_deadline_precedes_read(self):
  raw.DEADLINE=0
  try:
   with self.assertRaisesRegex(ValueError,'deadline'):raw.body(Path('/nonexistent'),'x')
  finally:raw.DEADLINE=None
 def test_fatal_identity_survives_later_cleanup(self):
  for original in (MemoryError('original'),RecursionError('original'),KeyboardInterrupt()):
   self.assertIs(raw.preserve(original,OSError('close')),original);self.assertIs(outer.select(original,SystemExit()),original)
 def test_genuine_cleanup_type_selection(self):
  # Pure stand-in class exercises priority only; it is not native CleanupFailure.
  class Cleanup(BaseException):pass
  c=Cleanup();original=ValueError();self.assertIs(outer.select(original,c,Cleanup),c)
  fatal=MemoryError();self.assertIs(outer.select(fatal,c,Cleanup),fatal)
 def test_real_native_observation_body_preserved(self):
  t=ast.parse((P/'proof_raw01.py').read_text());n=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='positive_native_observations')
  old=ast.parse((P/'native_observations.baseline03.txt').read_text()).body[0]
  self.assertEqual(ast.dump(n,include_attributes=False),ast.dump(old,include_attributes=False))
 def test_compact_page_bounds_and_refs(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);d=root/'tiny-pages';d.mkdir()
   def save(n,v):
    b=(json.dumps(v,sort_keys=True)+'\n').encode();self.assertLessEqual(len(b),8192);(d/n).write_bytes(b)
   rows=[{'path':'synthetic-'+str(i),'sha256':'a'*64} for i in range(500)]
   result=outer.pages(root,d,'source',rows,save);self.assertGreater(result['page_count'],1)
   actual=[]
   for r in result['pages']:actual.extend(raw.deref(root,r)['rows'])
   self.assertEqual(actual,rows)
 def test_pages_refuse_single_giant_inline_map(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaisesRegex(ValueError,'row too large'):outer.pages(Path(td),Path(td),'x',[{'inline':'x'*7000}],lambda *a:None)
 def test_raw_archive_equality_does_not_unpickle(self):
  # Tiny opaque bytes only. They are deliberately not a Torch result or tensor.
  def archive(payload,description=b'opaque fixture'):
   f=io.BytesIO()
   with zipfile.ZipFile(f,'w',compression=zipfile.ZIP_STORED) as z:
    z.writestr('archive/data.pkl',description);z.writestr('archive/data/0',payload);z.writestr('archive/version',b'3\n')
   return f.getvalue()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);d=p/'fixtures';d.mkdir()
   for task in ('direction','regression'):
    for branch in ('resident','detached'):(d/(branch+'-'+task+'.pt')).write_bytes(archive(b'opaque storage'))
   result=raw.proof_archives(p,'fixtures');self.assertFalse(result['direction']['unpickled'])
   (d/'detached-direction.pt').write_bytes(archive(b'changed'))
   with self.assertRaisesRegex(ValueError,'storage differs'):raw.proof_archives(p,'fixtures')
 def test_archive_unknown_member_refused(self):
  f=io.BytesIO()
  with zipfile.ZipFile(f,'w') as z:z.writestr('../outside',b'x')
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   for branch in ('resident','detached'):(p/(branch+'-direction.pt')).write_bytes(f.getvalue())
   with self.assertRaisesRegex(ValueError,'unknown'):raw.proof_archives(p,'.')
 def test_unavailable_materialization_is_not_science(self):
  with self.assertRaises((KeyError,ValueError)):raw.materialization(Path('/nonexistent'),{}, {'status':'complete','program_id':raw.PROGRAM})
 def test_import_blocker_is_explicit(self):
  b=release.NoNumericalImports()
  for name in ('numpy','torch.nn','pandas','pyarrow.lib'):
   with self.assertRaises(ImportError):b.find_spec(name)
  self.assertIsNone(b.find_spec('json'))
 def test_old_resource_parser_not_reused(self):
  for n in ('proof_raw01.py','proof_release01.py','proof_outer01.py'):
   s=(P/n).read_text();self.assertNotIn('from raw_receipts01 import',s);self.assertNotIn('original-import-resource-terminal',s)
if __name__=='__main__':unittest.main(verbosity=2)
