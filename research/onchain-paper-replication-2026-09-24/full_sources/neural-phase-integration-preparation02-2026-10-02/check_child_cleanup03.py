"""Pure injected stream/operator failures; no files, child, scope or guard."""
import ast
from pathlib import Path
import os
import sys
from types import SimpleNamespace
import unittest
HERE=Path(__file__).resolve().parent
TARGET=HERE/sys.argv.pop(1)

class Check(unittest.TestCase):
    def exercise(self,body,err_close=None,out_close=None,err_open=None):
        closed=[];calls=[]
        class Stream:
            def __init__(self,name,error):self.name=name;self.error=error
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
            def close(self):
                closed.append(self.name)
                if self.error is not None:raise self.error
        out=Stream('stdout',out_close);err=Stream('stderr',err_close)
        class File:
            def __init__(self,name):self.name=name
            def open(self,mode):
                assert mode=='xb'
                if self.name=='child.stderr' and err_open is not None:raise err_open
                return out if self.name=='child.stdout' else err
        class Root:
            def __truediv__(self,name):return File(name)
        def run(*args,**kw):calls.append((args,kw));raise body
        node=next(n for n in ast.parse(TARGET.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='child_bridge')
        globals_={'__file__':str(TARGET),'Path':Path,'sys':sys,'os':os,'SOURCE':'a'*40,'sha':lambda p:'b'*64,'immutable':lambda *a:None,'subprocess':SimpleNamespace(run=run)}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'injected-child-bridge','exec'),globals_)
        failure=None
        try:globals_['child_bridge'](SimpleNamespace(anchor={'experiment':'invented'},anchor_hash='c'*64),Root(),'/invented-cgroup')
        except BaseException as error:failure=error
        self.assertEqual(closed,['stdout'] if err_open is not None else ['stderr','stdout'])
        self.assertEqual(len(calls),0 if err_open is not None else 1)
        return failure
    def test_memoryerror_survives_all_close_errors(self):
        first=MemoryError('original');self.assertIs(self.exercise(first,OSError('stderr'),OSError('stdout')),first)
    def test_systemexit_survives_close_error(self):
        first=SystemExit('original');self.assertIs(self.exercise(first,OSError('stderr')),first)
    def test_first_cleanup_fatal_promoted_over_ordinary_and_preserved(self):
        ordinary=ValueError('body');fatal=MemoryError('stderr');later=SystemExit('stdout')
        result=self.exercise(ordinary,fatal,later);self.assertIs(result,fatal);self.assertIs(result.__cause__,ordinary)
    def test_stderr_open_fatal_closes_stdout_without_masking(self):
        first=MemoryError('stderr open');self.assertIs(self.exercise(ValueError('must not execute'),out_close=OSError('stdout'),err_open=first),first)
    def test_original_ordinary_error_retained_with_later_ordinary_closes(self):
        first=ValueError('body');self.assertIs(self.exercise(first,OSError('stderr'),OSError('stdout')),first)
    def test_later_systemexit_does_not_replace_primary_memoryerror(self):
        first=MemoryError('body');self.assertIs(self.exercise(first,SystemExit('stderr'),OSError('stdout')),first)

if __name__=='__main__':unittest.main(verbosity=2)
