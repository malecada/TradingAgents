"""Actual functions under bounded stdlib error injection; no numeric imports."""
import ast,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load():
    tree=ast.parse((HERE/'owned_io.py').read_text());ns={'sys':sys}
    names={'CleanupFailure','_require','_fatal','_flatten','_cleanup'}
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names or isinstance(n,ast.Assign)]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-owned-io','exec'),ns)
    tree=ast.parse((HERE/'resource_fixture.py').read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_preserve_terminal']
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-terminal-reducer','exec'),ns)
    return ns

class AnnotationTests(unittest.TestCase):
    def test_cleanup_does_not_invoke_overridden_note(self):
        ns=load();calls=[];later=MemoryError('later annotation failure')
        class First(SystemExit):
            def add_note(self,note):calls.append('note');raise later
        first=First(8);seen=[]
        def close1():seen.append(1);raise OSError('uncertain')
        def close2():seen.append(2)
        try:
            try:raise first
            finally:ns['_cleanup']((close1,close2))
        except BaseException as result:self.assertIs(result,first)
        else:self.fail('fatal suppressed')
        self.assertEqual(seen,[1,2]);self.assertEqual(calls,[])
    def test_cleanup_no_exception_formatting(self):
        ns=load();calls=[]
        class Hostile(OSError):
            def __repr__(self):calls.append('repr');raise MemoryError('repr')
            def __str__(self):calls.append('str');raise SystemExit(9)
        original=ValueError('ordinary');first=MemoryError('first');seen=[]
        def close1():seen.append(1);raise Hostile()
        def close2():seen.append(2);raise first
        with self.assertRaises(MemoryError) as caught:ns['_cleanup']((close1,close2),primary=original)
        self.assertIs(caught.exception,first);self.assertEqual(seen,[1,2]);self.assertEqual(calls,[])
    def test_terminal_does_not_attempt_fallible_annotation_on_ordinary(self):
        ns=load();calls=[];fatal=MemoryError('simulated annotation allocation')
        class AnnotationProbe(BaseException):
            @staticmethod
            def add_note(*args):calls.append('note');raise fatal
        ns['BaseException']=AnnotationProbe
        original=ValueError('primary');later=OSError('later')
        self.assertIs(ns['_preserve_terminal'](original,later),original)
        self.assertEqual(calls,[],'Nonessential annotation must not run; a true fatal cannot be suppressed if invoked')
    def test_cleanup_fatal_survives_optional_cause_assignment_failure(self):
        ns=load();seen=[];later=MemoryError('cause allocation')
        class First(SystemExit):
            def __setattr__(self,name,value):
                if name=='__cause__':raise later
                super().__setattr__(name,value)
        first=First(8)
        def close1():seen.append(1);raise first
        def close2():seen.append(2);raise OSError('close')
        with self.assertRaises(First) as caught:ns['_cleanup']((close1,close2),primary=ValueError('body'))
        self.assertIs(caught.exception,first);self.assertEqual(seen,[1,2])
    def test_terminal_actual_fatal_promotes_ordinary(self):
        ns=load();original=ValueError('ordinary');fatal=MemoryError('actual')
        self.assertIs(ns['_preserve_terminal'](original,fatal),fatal)
        self.assertIs(fatal.__cause__,original)
    def test_terminal_existing_fatal_preserved_without_formatting(self):
        ns=load();calls=[]
        class Hostile(SystemExit):
            def __str__(self):calls.append('str');raise MemoryError('format')
            def __repr__(self):calls.append('repr');raise MemoryError('format')
            def add_note(self,note):calls.append('note');raise MemoryError('note')
        first=Hostile(8)
        self.assertIs(ns['_preserve_terminal'](first,MemoryError('later')),first)
        self.assertEqual(calls,[])

if __name__=='__main__':unittest.main()
