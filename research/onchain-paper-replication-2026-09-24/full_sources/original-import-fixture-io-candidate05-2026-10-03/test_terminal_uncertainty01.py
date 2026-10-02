"""Extracted actual reducer/source class, stdlib only. No numeric/job execution."""
import argparse,ast,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'resource_fixture.py'

def load():
    ns={}
    tree=ast.parse((HERE.parent/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py').read_text())
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('CleanupFailure','_fatal')]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-uncertainty-class','exec'),ns)
    tree=ast.parse(SOURCE.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_preserve_terminal']
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-terminal-reducer','exec'),ns)
    return ns

class Tests(unittest.TestCase):
    def test_synthetic_uncertainty_does_not_run_fallible_cause_attachment(self):
        ns=load();seen=[];allocation=MemoryError('firstactualfatalifinvoked')
        class Uncertain(ns['CleanupFailure']):
            def __setattr__(self,name,value):
                if name=='__cause__':seen.append('cause');raise allocation
                return super().__setattr__(name,value)
        ordinary=ValueError('body');uncertain=Uncertain('close')
        self.assertIs(ns['_preserve_terminal'](ordinary,uncertain),uncertain)
        self.assertEqual(seen,[],'Synthetic uncertainty must not introduce then discard first actual fatal')
    def test_actual_fatal_retains_precedence_if_optional_attachment_fails(self):
        ns=load();seen=[];later=MemoryError('laterallocation')
        class First(SystemExit):
            def __setattr__(self,name,value):
                if name=='__cause__':seen.append('cause');raise later
                return super().__setattr__(name,value)
        first=First(8)
        self.assertIs(ns['_preserve_terminal'](ValueError('body'),first),first)
        self.assertEqual(seen,['cause'])
    def test_original_selected_fatal_and_ordinary_precedence_unchanged(self):
        ns=load();first=MemoryError('first');ordinary=ValueError('body');later=OSError('ordinarylater')
        self.assertIs(ns['_preserve_terminal'](first,SystemExit(9)),first)
        self.assertIs(ns['_preserve_terminal'](ordinary,later),ordinary)
        self.assertIs(ns['_preserve_terminal'](None,first),first)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path);args,rest=parser.parse_known_args()
    if args.source:SOURCE=args.source
    unittest.main(argv=[__file__,*rest])
