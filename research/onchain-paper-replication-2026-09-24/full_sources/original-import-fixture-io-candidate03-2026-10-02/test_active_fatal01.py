"""Exact matcher method, qualified inert engine/retention operators, no numerics."""
import ast,copy,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEPENDENCY=HERE.parent/'original-import-fixture-io-candidate02-2026-10-02'

def helpers():
    tree=ast.parse((DEPENDENCY/'owned_io.py').read_text())
    names={'CleanupFailure','_require','_fatal','_flatten','_cleanup','_close_after_failure'}
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names or isinstance(n,ast.Assign)]
    ns={'sys':sys};exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-IO02-helper','exec'),ns)
    return types.SimpleNamespace(**ns,META_LIMIT=8192)

def method(path):
    tree=ast.parse(path.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CompactMatcher')
    return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__call__')

class ActiveFatal(unittest.TestCase):
    def run_case(self,retained_error,close_error):
        io=helpers();seen=[];body=ValueError('ordinary advance failure')
        class Engine:
            def create(self,*a,**k):return {'phase':'annealing'}
            def advance(self,*a,**k):seen.append('advance');raise body
            def close(self,state):seen.append('engine-close');raise close_error
        class Retained:
            def before_pair(self):pass
            def begin(self,*a):pass
            def fail(self,error):
                self.original=error;seen.append('retained-fail');raise retained_error
        retained=Retained()
        log=types.SimpleNamespace(events=0,start={'limits':{'max_events':10}},begin=lambda *a:None,complete=lambda *a:seen.append('forbidden-complete'))
        obj=types.SimpleNamespace(busy=False,poisoned=False,log=log,retention=retained,workload='w',checkpoints=0,reserved_bytes=0,config={},policy={'max_checkpoint_bytes':1},schedule={'max_checkpoints':1,'max_total_checkpoints':1,'max_total_checkpoint_bytes':10**6,'calls_per_checkpoint':1,'operations_per_call':1},_check=lambda:None,_expected_event=lambda *a,**k:None,_ack_check=lambda *a:None,pair_identity=lambda *a:{})
        ns={'io':io,'engine':Engine(),'require':io._require,'copy':copy,'cache_key':lambda x:'key','graph_identity':lambda x:x,'pair':types.SimpleNamespace(ENGINE_FIELDS=set(),policy_check=lambda *a:None,digest=lambda *a:'hash'),'_RETENTION':types.SimpleNamespace(get=lambda x:retained),'CheckpointStop':RuntimeError}
        node=method(HERE/'compact_matcher.py');exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-candidate-CompactMatcher.__call__','exec'),ns)
        with self.assertRaises(type(retained_error)) as caught:
            ns['__call__'](obj,{'schema_version':1,'kind':'mcm','workload_sha256':'w','typed_graphs':['a','b']},'a','b')
        self.assertIs(caught.exception,retained_error)
        self.assertIs(retained.original,body);self.assertIs(retained_error.__cause__,body)
        self.assertEqual(seen,['advance','retained-fail','engine-close']);self.assertTrue(obj.poisoned);self.assertFalse(obj.busy)
    def test_retained_memoryerror_before_ordinary_close(self):self.run_case(MemoryError('first actual fatal'),OSError('close'))
    def test_retained_systemexit_before_memoryerror_close(self):self.run_case(SystemExit(19),MemoryError('second actual fatal'))
    def test_retained_memoryerror_before_systemexit_close(self):self.run_case(MemoryError('first actual fatal'),SystemExit(23))

if __name__=='__main__':unittest.main()
