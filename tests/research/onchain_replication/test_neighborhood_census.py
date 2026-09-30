"""Synthetic-only exact census oracle; no empirical graph access."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

from tradingagents.research.onchain_replication import neighborhood_census as engine

class CensusTests(unittest.TestCase):
    def run_case(self,n,edges,chunk=2):
        edge_index=np.asarray(edges,dtype=np.int64).reshape((-1,2)).T
        neighbors=[{i} for i in range(n)]
        for a,b in edges:neighbors[a].add(b);neighbors[b].add(a)
        expected=np.asarray([len(x) for x in neighbors],dtype=np.int64)
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/'census'
            result=engine.census(edge_index,n,out,identity={'graph':'synthetic'},edge_chunk=chunk,max_output_bytes=1024**2)
            np.testing.assert_array_equal(np.load(out/'cardinalities.npy'),expected)
            np.testing.assert_array_equal(np.load(out/'maxima_indices.npy'),np.flatnonzero(expected==expected.max()))
            values,counts=np.unique(expected,return_counts=True)
            np.testing.assert_array_equal(np.load(out/'histogram.npy'),np.column_stack((values,counts)))
            self.assertEqual(result['nodes'],n)
            self.assertEqual(result['minimum'],int(expected.min()))
            self.assertEqual(result['maximum'],int(expected.max()))
            self.assertEqual(result['above_10000'],int((expected>10000).sum()))
            self.assertEqual(result['unique_nonself_pairs'],sum(len(x)-1 for x in neighbors)//2)
            self.assertLessEqual(result['output_bytes'],1024**2)
            self.assertTrue((out/'checkpoints'/'03-summary.json').is_file())
            before={p.name:p.read_bytes() for p in out.iterdir() if p.is_file()}
            with self.assertRaises(FileExistsError):engine.census(edge_index,n,out,identity={'graph':'synthetic'},edge_chunk=chunk,max_output_bytes=1024**2)
            self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir() if p.is_file()})

    def test_asymmetric_reciprocal_duplicates_loops_and_isolates(self):
        self.run_case(7,[(4,1),(1,4),(4,1),(2,4),(4,4),(0,0),(6,3)])
    def test_empty_edges_and_singleton(self):
        self.run_case(1,[]);self.run_case(5,[])
    def test_all_equal_cardinalities(self):
        self.run_case(5,[(0,1),(1,2),(2,3),(3,4),(4,0)])
    def test_fixed_random_oracle_and_chunk_invariance(self):
        rng=np.random.default_rng(417)
        edges=rng.integers(0,37,size=(203,2)).tolist()
        for chunk in (1,7,64,1024):self.run_case(37,edges,chunk)
    def test_capacity_does_not_truncate(self):
        n=10002;self.run_case(n,[(0,i) for i in range(1,n)],65536)
    def test_bad_inputs_and_disk_admission_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/'census'
            for array,n,kw in [(np.array([[0],[2]]),2,{}),(np.array([[0.],[1.]]),2,{}),(np.empty((2,0),dtype=np.int64),0,{}),(np.empty((2,0),dtype=np.int64),2**32,{}),(np.array([[0],[1]]),2,{'edge_chunk':True}),(np.array([[0],[1]]),2,{'max_output_bytes':1})]:
                with self.assertRaises(ValueError):engine.census(array,n,out,identity={'graph':'synthetic'},**kw)
                self.assertFalse(out.exists())
    def test_all_owned_maps_close_on_success_and_failure(self):
        original=np.lib.format.open_memmap
        for fail_phase in (None,'sorted_pairs','cardinalities','summary'):
            with tempfile.TemporaryDirectory() as temporary:
                owned=[]
                def capture(*args,**kwargs):
                    value=original(*args,**kwargs);owned.append(value);return value
                def checkpoint(phase):
                    if phase==fail_phase:raise RuntimeError('injected phase failure')
                with patch.object(np.lib.format,'open_memmap',side_effect=capture):
                    if fail_phase is None:engine.census(np.array([[0,1],[1,2]]),3,Path(temporary)/'census',identity={'graph':'synthetic'},checkpoint=checkpoint)
                    else:
                        with self.assertRaisesRegex(RuntimeError,'injected'):
                            engine.census(np.array([[0,1],[1,2]]),3,Path(temporary)/'census',identity={'graph':'synthetic'},checkpoint=checkpoint)
                self.assertTrue(owned);self.assertTrue(all(value._mmap.closed for value in owned))

    def test_cleanup_attempts_every_map_and_keeps_primary_failure(self):
        original=np.lib.format.open_memmap
        with tempfile.TemporaryDirectory() as temporary:
            closed=[]
            class Proxy:
                def __init__(self,value,name):self.value=value;self.name=name
                def __getattr__(self,name):return getattr(self.value,name)
                def close(self):
                    closed.append(self.name);self.value.close()
                    if self.name=='cardinalities.npy':raise OSError('injected close failure')
            def capture(path,*args,**kwargs):
                value=original(path,*args,**kwargs);value._mmap=Proxy(value._mmap,Path(path).name);return value
            def checkpoint(phase):
                if phase=='cardinalities':raise RuntimeError('primary phase failure')
            with patch.object(np.lib.format,'open_memmap',side_effect=capture):
                with self.assertRaisesRegex(RuntimeError,'primary phase failure') as caught:
                    engine.census(np.array([[0,1],[1,2]]),3,Path(temporary)/'census',identity={'graph':'synthetic'},checkpoint=checkpoint)
            self.assertEqual(closed,['cardinalities.npy','sorted_pairs.npy'])
            self.assertTrue(any('cleanup' in note for note in caught.exception.__notes__))

    def test_maximal_admitted_identity_fits_metadata_reserve(self):
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/'census'
            result=engine.census(np.empty((2,0),dtype=np.int64),1,out,identity={'graph':'x'*16350})
            self.assertLessEqual(sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),result['reserved_output_bytes'])

    def test_checkpoint_failure_preserves_completed_phase(self):
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/'census'
            def fail(phase):
                if phase=='sorted_pairs':raise RuntimeError('injected interruption')
            with self.assertRaisesRegex(RuntimeError,'injected'):
                engine.census(np.array([[0,1,2],[1,0,2]]),3,out,identity={'graph':'synthetic'},checkpoint=fail)
            self.assertTrue((out/'checkpoints'/'01-sorted_pairs.json').exists())
            self.assertFalse((out/'summary.json').exists())
            self.assertEqual(np.load(out/'sorted_pairs.npy').tolist(),[-1,1,1])

if __name__=='__main__':unittest.main(verbosity=2)
