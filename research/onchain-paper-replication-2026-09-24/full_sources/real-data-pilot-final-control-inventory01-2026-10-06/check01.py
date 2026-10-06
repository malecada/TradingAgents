"""Focused stdlib-only offline checks; no native/numeric/imported data execution."""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def audit(event,args):
    if event.startswith(('socket.','subprocess.')):raise RuntimeError('offline checks forbid network/subprocess')
    if event=='import' and args[0].split('.')[0] in {'numpy','torch','pandas','scipy'}:raise RuntimeError('numerical imports forbidden')
sys.addaudithook(audit)
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=module('prepare01');candidate=module('native_receipt_candidate01')

class Stream:
    def __init__(self,short=False):self.body=bytearray();self.short=short
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def write(self,b):
        n=len(b)-1 if self.short else len(b);self.body.extend(b[:n]);return n
    def flush(self):pass
    def fileno(self):return 1
class IO:
    def __init__(self,short=False):self.stream=Stream(short);self.births=0
    def _opened(self,path,mode):self.births+=1;return self.stream

class Check(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(p.INPUT.read_text());cls.s=p.load();cls.a=p.derive(cls.d,cls.s)
    def test_authentic_counts_and_scalar_proof(self):
        self.assertEqual(sum(v['cells'] for v in self.a['by_week'].values()),415968128)
        self.assertEqual(self.a['typed_max_control_bytes'],8192*(3*self.a['typed_operations']+self.a['typed_chunk_credits']))
        self.assertEqual(self.a['typed_max_control_bytes'],627941376)
    def test_changed_count_metadata_refused(self):
        bad=copy.deepcopy(self.d);next(iter(bad['graphs'].values()))['node_count']['sha256']='0'*64
        with self.assertRaises(ValueError):p.derive(bad,self.s)
    def test_undersized_allocation_refused(self):
        bad=copy.deepcopy(self.d);next(iter(bad['protocol']['typed_allocations']['by_week'].values()))['score-tail-f64']['max_chunks']-=1
        with self.assertRaises(ValueError):p.derive(bad,self.s)
    def test_baseline_still_refused(self):
        with self.assertRaises(ValueError):self.s.prepare(p.ROOT,self.d)
    def test_residual_unknowns_and_budget_conflict(self):
        doc=json.loads((HERE/'DECLARATION_DRAFT01.json').read_text())
        for name in ('runtime_temp_cache','training_and_lifecycle'):
            self.assertIsNone(doc['residual_domains'][name]['logical_bytes'])
            self.assertIsNone(doc['residual_domains'][name]['additional_scratch_bytes'])
        a=self.a
        lower=a['typed_max_control_bytes']+a['archive_policy']['max_workflow_metadata_bytes']+a['history_bounds']['control_bytes']+a['history_bounds']['diagnostic_bytes']+sum(x['retained_matrix_logical_bytes']+x['typed_attempt_metadata_allowance_bytes'] for x in a['by_week'].values())
        self.assertGreater(lower,16*1024**3)
    def test_receipt_exact_boundary_and_parity(self):
        value={'error':'真实 failure\nline','status':'failed','values':[1,True,None,1.25]}
        expected=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode();io=IO()
        with patch.object(candidate.os,'fsync'):
            candidate._native_write(Path('synthetic'),value,io,max_bytes=len(expected))
        self.assertEqual(bytes(io.stream.body),expected)
        small=IO()
        with self.assertRaisesRegex(ValueError,'limit exceeded'):candidate._native_write(Path('synthetic'),value,small,max_bytes=len(expected)-1)
        self.assertEqual(small.births,0)
    def test_candidate_requires_explicit_limit(self):
        for n in (None,True,0,-1,2**63):
            with self.assertRaises(ValueError):candidate._native_write(Path('synthetic'),{},IO(),max_bytes=n)
    def test_encoding_failure_and_short_write_not_coerced(self):
        io=IO()
        with self.assertRaises(TypeError):candidate._native_write(Path('synthetic'),{'invalid':object()},io,max_bytes=1000)
        self.assertEqual(io.births,0)
        io=IO(short=True)
        with self.assertRaisesRegex(OSError,'partial retained'):candidate._native_write(Path('synthetic'),{'status':'failed'},io,max_bytes=1000)
        self.assertGreater(len(io.stream.body),0)
    def test_candidate_single_function_source_seam(self):
        source=(p.ROOT/(p.PREFIX+'resources.py')).read_text()
        self.assertIn("def _native_write(path,state,io):",source)
        self.assertIn("raw=json.dumps(state,indent=2,sort_keys=True).encode()+b'\\n'",source)
        self.assertNotIn('numpy',Path(candidate.__file__).read_text())

if __name__=='__main__':unittest.main(verbosity=2)
