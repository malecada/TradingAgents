"""Synthetic interruption/continuation parity with the existing scalar oracle."""
import importlib.util
from pathlib import Path
import tempfile
from dataclasses import replace
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph,config
from tradingagents.research.onchain_replication.matching_reference import match_reference
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('annealing',HERE/'annealing.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CheckpointTests(unittest.TestCase):
    def fixture(self):
        return graph([[0.],[.3],[1.]],[(0,1,.1),(1,0,.2),(2,1,.4)]),graph([[.1],[.4],[1.2],[2.]],[(0,1,.3),(1,2,.2),(3,0,.4)])

    def finish(self,state,a,b,c,budget):
        calls=0
        while state['phase']!='done':
            m.advance(state,a,b,c,max_operations=budget);calls+=1
            self.assertLess(calls,10000)
        return m.result(state,a,b,c)

    def equal(self,got,want):
        np.testing.assert_array_equal(got.soft_assignment,want.soft_assignment)
        np.testing.assert_array_equal(got.assignment,want.assignment)
        self.assertEqual((got.score,got.iterations,got.convergence),(want.score,want.iterations,want.convergence))

    def test_resume_across_node_edge_normalization_and_iteration_boundaries(self):
        a,b=self.fixture();c=config();want=match_reference(a,b,c)
        phases=set()
        for cut in (1,6,12,13,16,22,23,24,40,100):
            state=m.create(a,b,c,max_state_bytes=1024**2)
            m.advance(state,a,b,c,max_operations=cut);phases.add(state['phase'])
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'checkpoint';sha=m.save(state,path,a,b,c,max_checkpoint_bytes=1024**2)
                state=m.load(path,a,b,c,expected_sha256=sha,max_state_bytes=1024**2)
                self.equal(self.finish(state,a,b,c,3),want)
        self.assertTrue({'nodes','outer','edges','normalize_scale'}<=phases)

    def test_rectangular_zero_edge_ties_and_iteration_cap(self):
        cases=[(graph([[0]],[]),graph([[0],[0],[0]],[])),self.fixture()]
        for a,b in cases:
            for iterations in (1,2,50):
                c=config()|{'max_iterations':iterations};state=m.create(a,b,c,max_state_bytes=1024**2)
                self.equal(self.finish(state,a,b,c,1),match_reference(a,b,c))

    def test_array_tampering_rejected_before_loading_any_array(self):
        a,b=self.fixture();c=config();state=m.create(a,b,c,max_state_bytes=1024**2)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'checkpoint';sha=m.save(state,path,a,b,c,max_checkpoint_bytes=1024**2)
            with (path/'Q.npy').open('r+b') as f:f.seek(-1,2);f.write(b'x')
            with patch.object(m.np,'load',side_effect=AssertionError('opened before hash validation')):
                with self.assertRaises(ValueError):m.load(path,a,b,c,expected_sha256=sha,max_state_bytes=1024**2)

    def test_configuration_or_input_identity_change_refused(self):
        a,b=self.fixture();c=config();state=m.create(a,b,c,max_state_bytes=1024**2)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'checkpoint';sha=m.save(state,path,a,b,c,max_checkpoint_bytes=1024**2)
            with self.assertRaises(ValueError):m.load(path,a,b,c|{'alpha':2},expected_sha256=sha,max_state_bytes=1024**2)
            changed=b.node_features.copy();changed[0,0]=9
            b=replace(b,node_features=changed)
            with self.assertRaises(ValueError):m.load(path,a,b,c,expected_sha256=sha,max_state_bytes=1024**2)

    def test_budget_and_existing_identity_refusals(self):
        a,b=self.fixture();c=config()
        with patch.object(m.np,'zeros',side_effect=AssertionError('allocated before budget')):
            with self.assertRaises(ValueError):m.create(a,b,c,max_state_bytes=1)
        with self.assertRaises(ValueError):m.create(a,b,c|{'max_pair_entries':1},max_state_bytes=1024**2)
        state=m.create(a,b,c,max_state_bytes=1024**2)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'checkpoint'
            with self.assertRaises(ValueError):m.save(state,path,a,b,c,max_checkpoint_bytes=1)
            self.assertFalse(path.exists())
            sha=m.save(state,path,a,b,c,max_checkpoint_bytes=1024**2)
            with self.assertRaises(FileExistsError):m.save(state,path,a,b,c,max_checkpoint_bytes=1024**2)
            (path/'manifest.json').unlink()
            with self.assertRaises(FileNotFoundError):m.load(path,a,b,c,expected_sha256=sha,max_state_bytes=1024**2)

    def test_unreachable_phase_states_are_refused_before_checkpoint(self):
        a,b=self.fixture();c=config()
        mutations=[{'phase':'nodes','cursor':12},{'phase':'done'},
                   {'phase':'normalize_scale','iterations':c['max_iterations']}]
        for mutation in mutations:
            state=m.create(a,b,c,max_state_bytes=1024**2);state.update(mutation)
            if state['iterations']:
                for _ in range(state['iterations']):state['beta']*=1+c['beta_rate']
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):m.save(state,Path(tmp)/'invalid',a,b,c,max_checkpoint_bytes=1024**2)
                self.assertFalse((Path(tmp)/'invalid').exists())

    def test_interrupted_matrix_update_poisoned_state_cannot_be_saved(self):
        a,b=self.fixture();c=config();state=m.create(a,b,c,max_state_bytes=1024**2)
        m.advance(state,a,b,c,max_operations=13)
        self.assertEqual(state['phase'],'edges')
        class InterruptAfterWrite(np.ndarray):
            def __setitem__(self,key,value):
                super().__setitem__(key,value)
                raise KeyboardInterrupt('between mutation and cursor')
        state['Q']=state['Q'].view(InterruptAfterWrite)
        with self.assertRaises(KeyboardInterrupt):m.advance(state,a,b,c,max_operations=1)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):m.save(state,Path(tmp)/'invalid',a,b,c,max_checkpoint_bytes=1024**2)
        with self.assertRaises(ValueError):m.advance(state,a,b,c,max_operations=1)

    def test_every_normalization_return_is_durably_resumable(self):
        pairs = [self.fixture(),
                 (graph([[0.],[.3],[1.]],[(0,1,.2)]),
                  graph([[0.],[.1],[.4],[1.],[2.]],[(0,1,.3),(3,4,.1)])),
                 (graph([[0.],[1.],[2.]],[]),graph([[.5]],[]))]
        phases = set()
        for a,b in pairs:
            n,k = len(a.node_ids),len(b.node_ids)
            cap = max(k,n if k==1 else 2*n)
            c=config()|{'max_iterations':2}
            state=m.create(a,b,c,max_state_bytes=24*n*k,max_chunk_entries=cap)
            want=match_reference(a,b,c)
            with tempfile.TemporaryDirectory() as tmp:
                step=0
                while state['phase']!='done':
                    m.advance(state,a,b,c,max_operations=1)
                    phases.add(state['phase']);step+=1
                    before={name:state[name].tobytes() for name in m.NAMES}
                    path=Path(tmp)/str(step)
                    digest=m.save(state,path,a,b,c,max_checkpoint_bytes=1024**2)
                    state=m.load(path,a,b,c,expected_sha256=digest,
                                 max_state_bytes=24*n*k,max_chunk_entries=cap)
                    self.assertEqual(before,{name:state[name].tobytes() for name in m.NAMES})
                    self.assertLess(step,1000)
            self.equal(m.result(state,a,b,c),want)
            self.assertEqual(m.result(state,a,b,c).soft_assignment.tobytes(),want.soft_assignment.tobytes())
        self.assertTrue({'normalize_scale','normalize_rows','normalize_columns','normalize_exp'}<=phases)

    def test_normalization_policy_rejected_before_allocation_or_restore(self):
        a,b=self.fixture();c=config()
        with patch.object(m.np,'zeros',side_effect=AssertionError('allocation before policy')):
            with self.assertRaises(ValueError):
                m.create(a,b,c,max_state_bytes=1024**2,max_chunk_entries=5)
        state=m.create(a,b,c,max_state_bytes=1024**2,max_chunk_entries=6)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'checkpoint';digest=m.save(state,path,a,b,c,max_checkpoint_bytes=1024**2)
            with patch.object(m.np,'load',side_effect=AssertionError('array opened before policy')):
                with self.assertRaises(ValueError):
                    m.load(path,a,b,c,expected_sha256=digest,max_state_bytes=1024**2,max_chunk_entries=7)

    def test_interrupted_normalization_block_poisoned(self):
        a,b=self.fixture();c=config()|{'max_iterations':1}
        state=m.create(a,b,c,max_state_bytes=1024**2,max_chunk_entries=6)
        for _ in range(100):
            if state['phase']=='normalize_exp':break
            m.advance(state,a,b,c,max_operations=1)
        self.assertEqual(state['phase'],'normalize_exp')
        real_exp=m.np.exp
        def interrupted(*args,**kwargs):
            real_exp(*args,**kwargs)
            raise KeyboardInterrupt('after native output mutation')
        with patch.object(m.np,'exp',side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):m.advance(state,a,b,c,max_operations=1)
        self.assertFalse(state['safe'])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):m.save(state,Path(tmp)/'invalid',a,b,c,max_checkpoint_bytes=1024**2)

if __name__=='__main__':unittest.main(verbosity=2)
