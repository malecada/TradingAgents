"""Finite stdlib source/file checks. Never imports the numerical package."""
import ast
import importlib.util
import pathlib
import tempfile
import unittest
import sys
HERE=pathlib.Path(__file__).resolve().parent
class Files(unittest.TestCase):
    def module(self):
        p=HERE/'cold_files.py'
        self.assertTrue(p.exists(),'detached file verifier is absent')
        s=importlib.util.spec_from_file_location('cold_files',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
    def setup_tree(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);r=pathlib.Path(t.name);(r/'a').mkdir();(r/'a'/'x').write_bytes(b'abcd');return r
    def bounds(self):return dict(max_files=3,max_directories=3,max_total_bytes=20,max_file_bytes=10,max_depth=3,chunk_bytes=2)
    def test_roundtrip_and_content_mutation(self):
        m=self.module();r=self.setup_tree();s=m.capture(r,('a',),self.bounds());s.check(full=True);(r/'a'/'x').write_bytes(b'zzzz')
        with self.assertRaises(ValueError):s.check(full=True)
    def test_extra_and_missing_members(self):
        m=self.module();r=self.setup_tree();s=m.capture(r,('a',),self.bounds());(r/'a'/'y').write_bytes(b'x')
        with self.assertRaises(ValueError):s.check(full=False)
        (r/'a'/'y').unlink();(r/'a'/'x').unlink()
        with self.assertRaises(ValueError):s.check(full=True)
    def test_symlink_hardlink_and_capacity(self):
        m=self.module();r=self.setup_tree();(r/'a'/'y').symlink_to('x')
        with self.assertRaises(ValueError):m.capture(r,('a',),self.bounds())
        (r/'a'/'y').unlink();(r/'a'/'y').hardlink_to(r/'a'/'x')
        with self.assertRaises(ValueError):m.capture(r,('a',),self.bounds())
        (r/'a'/'y').unlink();b=self.bounds();b['max_total_bytes']=3
        with self.assertRaises(ValueError):m.capture(r,('a',),b)
    def test_inode_swap_refused(self):
        m=self.module();r=self.setup_tree();s=m.capture(r,('a',),self.bounds());(r/'a'/'z').write_bytes(b'abcd');(r/'a'/'z').replace(r/'a'/'x')
        with self.assertRaises(ValueError):s.check(full=True)
    def test_duplicate_and_escape_roots(self):
        m=self.module();r=self.setup_tree()
        for roots in [('a','a'),('../a',),('a','a/x')]:
            with self.assertRaises(ValueError):m.capture(r,roots,self.bounds())
class Dispatch(unittest.TestCase):
    def test_candidate_has_explicit_dispatch_and_keeps_finalizations(self):
        p=HERE/'compact_native_producer.py';self.assertTrue(p.exists(),'detached dispatch absent')
        tree=ast.parse(p.read_text());source=ast.unparse(tree)
        self.assertIn('compact_cold_features.selected',source);self.assertIn('compact_cold_features.prepare',source);self.assertIn('compact_cold_features.finalize',source)
        job=ast.parse((HERE/'job_payload.py').read_text());calls=[n for n in ast.walk(job) if isinstance(n,ast.Call) and ast.unparse(n.func)=='compact_native_producer.finalize'];self.assertEqual(len(calls),2)
    def test_authority_has_no_producer_retention_fields(self):
        p=HERE/'compact_cold_features.py';self.assertTrue(p.exists(),'detached authority absent')
        t=ast.parse(p.read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Authority')
        fields=next(n.value for n in c.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='__slots__' for x in n.targets));slots=ast.literal_eval(fields)
        self.assertFalse(set(slots)&{'_terminal','_owner','_published','_closure','_training','_graphs','_callback','_binding'})
        text=ast.unparse(t);self.assertIn('type(terminal) is compact_terminal.Receipt',text);self.assertIn('owner.closed',text)
        self.assertIn('compact_cold_handoff_input',text)
if __name__=='__main__':unittest.main(verbosity=2)
