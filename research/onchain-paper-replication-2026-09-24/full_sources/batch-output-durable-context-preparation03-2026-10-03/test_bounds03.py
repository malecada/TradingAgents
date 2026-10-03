"""Bounded source-only DNT3 and NTC4 verification; no numerical authority."""
import ast,hashlib,importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).parent
spec=importlib.util.spec_from_file_location('prior_source_controls',H/'test_corrections02.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
class Tests(unittest.TestCase):
 def setUp(self):self.m=prior.load()
 def test_document_and_publication_limits_separate(self):
  v={'job':'x'*12000};self.assertGreater(len(self.m['job_document'](v)),8192)
  with self.assertRaises(ValueError):self.m['encode'](v)
  self.assertEqual(len(self.m['job_document']('x'*(2*1024**2-3))),2*1024**2)
  with self.assertRaises(ValueError):self.m['job_document']('x'*(2*1024**2-2))
 def test_complete_equality_not_projection(self):
  a={'all':{'fields':[1,2,{'value':'a'}]},'other':'x'*12000};b=json.loads(json.dumps(a));self.assertEqual(self.m['job_document'](a),self.m['job_document'](b));b['all']['fields'][2]['value']='b';self.assertNotEqual(self.m['job_document'](a),self.m['job_document'](b))
  with self.assertRaises(ValueError):self.m['job_document']({'x':float('nan')})
 def test_parent_rename_symlink_refused_closes_both(self):
  with tempfile.TemporaryDirectory(dir=H) as d:
   root=Path(d).resolve();parent=root/'parent';parent.mkdir();source=parent/'source.py';source.write_bytes(b'original');moved=root/'moved';realread=os.read;realclose=os.close;changed=[];closed=[]
   def redirect(fd,count):
    if not changed:parent.rename(moved);parent.symlink_to(moved,target_is_directory=True);changed.append(1)
    return realread(fd,count)
   def close(fd):closed.append(fd);return realclose(fd)
   with patch.object(os,'read',side_effect=redirect),patch.object(os,'close',side_effect=close):
    with self.assertRaises(ValueError):self.m['_source_body'](source)
   self.assertTrue(changed);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2);self.assertNotEqual(source.resolve(),source)
 def test_initial_control_and_job_preflight_order(self):
  t=ast.parse((H/'archive_non_tail.py').read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Context');init=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
  txt=ast.unparse(init);birth=txt.index('self.root.mkdir()')
  for call in ('job_document(self.execution)','encode(intent)','encode(receipt)'):self.assertLess(txt.index(call),birth)
  self.assertLess(txt.index('len(self.job_raw) <= 2 * 1024 ** 2'),txt.index('self.execution = json.loads(self.job_raw)'))
 def test_inverse_complete02bytes_and_AST(self):
  old=(H/'archive_non_tail.py.baseline02').read_text();new=(H/'archive_non_tail.py').read_text()
  def methods(s):
   tree=ast.parse(s);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Context');return tree,{n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
  ot,om=methods(old);nt,nm=methods(new);lines=new.splitlines(keepends=True);changes=[]
  for name in ('__init__','check'):
   a=om[name];b=nm[name];changes.append((b.lineno-1,b.end_lineno,old.splitlines(keepends=True)[a.lineno-1:a.end_lineno]))
  helper=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='job_document');changes.append((helper.lineno-1,helper.end_lineno,[]))
  for start,end,body in sorted(changes,reverse=True):lines[start:end]=body
  self.assertEqual(''.join(lines),old);self.assertEqual(ast.dump(ast.parse(''.join(lines))),ast.dump(ot))
  oldsrc=next(n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name=='_source_body');newsrc=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='_source_body');self.assertEqual(ast.dump(oldsrc),ast.dump(newsrc))
  for n in ('archive_dispatch.py','archive_transport.py'):self.assertEqual((H/n).read_bytes(),(H/(n+'.baseline02')).read_bytes())
if __name__=='__main__':unittest.main(verbosity=2)
