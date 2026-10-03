import ast,hashlib,importlib.util,json,os,pathlib,tempfile,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent;s=importlib.util.spec_from_file_location('launcher',P/'launcher02.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_original_release_reference_four_fields(self):
  # Execute the actual candidate join expression with the genuine frozen ref
  # schema. These synthetic dictionaries are shape tests, not authority.
  fn=next(n for n in ast.parse((P/'launcher02.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
  call=next(n.value for n in ast.walk(fn) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require' and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value=='original release/outer acceptance differs')
  ref={'path':'release.json','sha256':'a'*64,'bytes':42,'kind':'metadata'};wait={'release':ref};accepted={'release':ref,'status':'accepted','source':'b'*40,'identity':'i'}
  ns={'wait':wait,'accepted':accepted,'relative_release':'release.json','q':{'release':{'path':'/x/release.json','sha256':'a'*64},'source':'b'*40},'identity':'i','release_reference':ref}
  self.assertTrue(eval(compile(ast.Expression(call.args[0]),'actual-join','eval'),ns))
 def test_paths_refs(self):
  for x in ['.','../x','/absolute','a//b','a/./b','x\\y']:
   with self.assertRaises(ValueError):m.relative(x)
  for x in [{},{'path':'/x','sha256':'0'*64},{'path':'../x','sha256':'a'*64}]:
   with self.assertRaises(ValueError):m.refshape(x)
 def test_one_use_retained_reservation(self):
  with tempfile.TemporaryDirectory() as d:
   out=m.reserve(d,'synthetic-test-only',{'x':1});original=(out/'intent.json').read_bytes()
   with self.assertRaises(FileExistsError):m.reserve(d,'synthetic-test-only',{'x':2})
   self.assertEqual((out/'intent.json').read_bytes(),original)
 def test_read_hash_and_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'a';p.write_bytes(b'x');v={'path':str(p),'sha256':hashlib.sha256(b'x').hexdigest()};self.assertEqual(m.reference(v),b'x');p.write_bytes(b'y')
   with self.assertRaises(ValueError):m.reference(v)
   link=pathlib.Path(d)/'link';link.symlink_to(p)
   with self.assertRaises(ValueError):m.read(link)
 def test_first_fatal_all_closures(self):
  for fatal in [MemoryError(),KeyboardInterrupt(),SystemExit(7)]:
   seen=[]
   def close():seen.append(1);raise OSError()
   m.actions((close,lambda:seen.append(2)),fatal);self.assertEqual(seen,[1,2])
   with self.assertRaises(type(fatal)) as got:m.actions((lambda:(_ for _ in ()).throw(fatal),close),ValueError())
   self.assertIs(got.exception,fatal)
 def test_schema_no_missing_reviews(self):
  with self.assertRaises(ValueError):m.request_shape({'schema_version':1})
 def test_actual_read_close_fatal_identity(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'a';p.write_bytes(b'x');real=os.close;closed=[];fatal=MemoryError('first')
   def close(fd):closed.append(fd);real(fd);raise OSError('later')
   with patch.object(os,'read',side_effect=fatal),patch.object(os,'close',side_effect=close):
    with self.assertRaises(MemoryError) as got:m.read(p)
   self.assertIs(got.exception,fatal);self.assertEqual(len(closed),1)
if __name__=='__main__':unittest.main(verbosity=2)
