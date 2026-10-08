from tradingagents.research.onchain_replication import matching_checkpoint as engine
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.research.onchain_replication.test_matching_reference import graph, config
from tradingagents.research.onchain_replication.matching_reference import match_reference

from tradingagents.research.onchain_replication import matching_pair as m
CONTEXT = dict(namespace='a'*64, source_commit='b'*40, runtime_hash='c'*64)
POLICY = dict(max_state_bytes=1024**2, normalization_chunk_entries=6,
              hardening_chunk_entries=2, hardening_buffer_bytes=10000,
              max_score_buffer_bytes=10000, chunk_edges=2,
              max_checkpoint_bytes=256*1024, max_publications=100,
              total_checkpoint_bytes=40*1024**2)


class Tests(unittest.TestCase):
    def fixture(self):
        return (graph([[0.], [.3], [1.]], [(0, 1, .2), (2, 1, .1)]),
                graph([[0.], [.1]], [(0, 1, .3)]),
                config() | {'max_iterations': 1})

    def create(self, root, name='one', **changes):
        a, b, c = self.fixture()
        options = dict(owner='d'*64, context=CONTEXT, policy=POLICY)
        options.update(changes)
        return m.PairSession.create(root, name, a, b, c, **options)

    def resume(self, root, name, ref, *, a=None, b=None, c=None, **changes):
        x, y, z = self.fixture()
        options = dict(owner='e'*64, expected_owner='d'*64, context=CONTEXT, policy=POLICY)
        options.update(changes)
        return m.PairSession.resume(root, name, a or x, b or y, c or z, ref, **options)

    def finish(self, pair):
        for _ in range(1000):
            result = pair.step(max_operations=2)
            if result is not None:
                return result
        self.fail('pair did not finish')

    def test_progress_resume_and_directional_reference_parity(self):
        a, b, c = self.fixture()
        expected = match_reference(a, b, c)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = self.create(root)
            pair.step(max_operations=2)
            ref = pair.save()
            pair.close()
            resumed = self.resume(root, 'successor', ref)
            try:
                actual = self.finish(resumed)
                self.assertEqual((actual.score, actual.convergence, actual.iterations),
                                 (expected.score, expected.convergence, expected.iterations))
            finally:
                resumed.close()

    def test_completed_score_reused_without_solver_or_array_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = self.create(root)
            expected = self.finish(pair)
            ref = pair.save()
            pair.close()
            with patch.object(engine, 'create', side_effect=AssertionError('create repeated')), \
                 patch.object(engine, 'load', side_effect=AssertionError('array load repeated')), \
                 patch.object(engine, 'advance', side_effect=AssertionError('advance repeated')), \
                 patch.object(engine, 'score_only', side_effect=AssertionError('score repeated')):
                resumed = self.resume(root, 'reuse', ref)
                try:
                    self.assertEqual(resumed.step(max_operations=2), expected)
                    self.assertEqual(resumed.step(max_operations=2), expected)
                finally:
                    resumed.close()

    def test_orientation_context_owner_policy_and_hash_refused_before_loading(self):
        a, b, c = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = self.create(root)
            ref = pair.save()
            pair.close()
            cases = [dict(a=b, b=a), dict(context=CONTEXT | {'source_commit': 'f'*40}),
                     dict(context=CONTEXT | {'runtime_hash': 'f'*64}),
                     dict(context=CONTEXT | {'namespace': 'f'*64}),
                     dict(expected_owner='f'*64), dict(policy=POLICY | {'chunk_edges': 1}),
                     dict(c=c | {'alpha': 2})]
            with patch.object(engine, 'load', side_effect=AssertionError('loaded before rejection')):
                for i, changes in enumerate(cases):
                    with self.assertRaises(ValueError):
                        self.resume(root, 'bad'+str(i), ref, **changes)
                    self.assertFalse((root / ('bad'+str(i))).exists())
                with self.assertRaises(ValueError):
                    self.resume(root, 'bad_hash', ref | {'sha256': '0'*64})

    def test_failed_publication_preserved_and_prior_checkpoint_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = self.create(root)
            prior = pair.save()
            with patch.object(engine, 'save', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    pair.save()
            self.assertTrue((root / 'one' / 'artifact-000001').is_dir())
            with self.assertRaises(ValueError):
                pair.step(max_operations=2)
            pair.close()
            resumed = self.resume(root, 'after_failure', prior)
            try:
                self.assertIsNotNone(self.finish(resumed))
            finally:
                resumed.close()

    def test_exclusive_names_containment_and_checkpoint_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = self.create(root, policy=POLICY | {'max_publications': 1})
            try:
                pair.save()
                with self.assertRaises(ValueError):
                    pair.save()
                self.assertFalse((root/'one'/'artifact-000001').exists())
                with self.assertRaises((ValueError, FileExistsError)):
                    self.create(root)
                with self.assertRaises(ValueError):
                    self.create(root, '../outside')
                with self.assertRaises(ValueError):
                    self.create(root, 'too_small', policy=POLICY | {'total_checkpoint_bytes': 1})
                self.assertFalse((root/'too_small').exists())
            finally:
                pair.close()

    def test_successor_publication_keeps_exact_parent_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = self.create(root)
            prior = pair.save(); pair.close()
            resumed = self.resume(root, 'successor', prior)
            try:
                next_ref = resumed.save()
                expected = {'reference': prior, 'owner': 'd'*64}
                self.assertEqual(json.loads(Path(next_ref['path']).read_bytes())['parent'], expected)
                self.assertEqual(json.loads((root/'successor'/'owner.json').read_bytes())['parent'], expected)
            finally:
                resumed.close()

    def test_cleanup_failure_preserves_primary_interruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = self.create(Path(tmp))
            original = KeyboardInterrupt('primary interruption')
            with patch.object(engine, 'advance', side_effect=original), \
                 patch.object(engine, 'close', side_effect=RuntimeError('secondary cleanup')):
                with self.assertRaises(KeyboardInterrupt) as caught:
                    pair.step(max_operations=2)
            self.assertIs(caught.exception, original)
            self.assertIn('RuntimeError', caught.exception.__notes__[0])
            self.assertFalse(pair.safe)


class LocalTests(Tests):
    def fixture(self):
        from tradingagents.research.onchain_replication.neighborhoods import NeighborhoodIndex
        a, b, c = super().fixture()
        options = {'hop_depth': 1, 'maximum_neighborhood_nodes': 10}
        return (NeighborhoodIndex(a).neighborhood(1, options),
                NeighborhoodIndex(b).neighborhood(0, options), c)

    def test_local_parent_center_order_and_features_bound_before_load(self):
        from dataclasses import replace
        a, b, c = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = self.create(root)
            ref = pair.save(); pair.close()
            variants = [replace(a, parent_hash='f'*64), replace(a, center_id=a.node_ids[0]),
                        replace(a, node_ids=tuple(reversed(a.node_ids))),
                        replace(a, node_features=a.node_features+.01),
                        replace(a, edge_index=a.edge_index[:, ::-1], edge_features=a.edge_features[::-1])]
            with patch.object(engine, 'load', side_effect=AssertionError('body opened')):
                for i, changed in enumerate(variants):
                    with self.assertRaises(ValueError):
                        self.resume(root, 'changed'+str(i), ref, a=changed)

    def test_actual_local_soft_assignment_and_score_match_reference(self):
        import numpy as np
        a, b, c = self.fixture()
        expected = match_reference(a, b, c)
        state = engine.create(a, b, c, **{k: POLICY[k] for k in m.ENGINE_FIELDS})
        try:
            for _ in range(1000):
                if state['phase'] == 'done':
                    break
                engine.advance(state, a, b, c, max_operations=2)
            else:
                self.fail('local engine did not finish')
            actual = engine.result(state, a, b, c)
            self.assertEqual(actual.soft_assignment.tobytes(), expected.soft_assignment.tobytes())
            np.testing.assert_array_equal(actual.assignment, expected.assignment)
            self.assertEqual(actual.score, expected.score)
        finally:
            engine.close(state)

    def test_restored_rank_mapping_closed_on_score_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = self.create(root)
            for _ in range(1000):
                if pair.state['phase'] == 'hardening':
                    break
                pair.step(max_operations=1)
            else:
                self.fail('hardening boundary not reached')
            ref = pair.save(); pair.close()
            resumed = self.resume(root, 'mapped', ref)
            mapping = resumed.state['hardening']['order']._mmap
            self.assertFalse(mapping.closed)
            try:
                self.finish(resumed)
                self.assertTrue(mapping.closed)
                self.assertIsNone(resumed.state)
            finally:
                resumed.close()

    def test_old_composite_and_annealing_schemas_refused_before_array_load(self):
        import hashlib
        a, b, c = self.fixture()
        policy = {k: POLICY[k] for k in m.ENGINE_FIELDS}
        state = engine.create(a, b, c, **policy)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)/'state'
                engine.save(state, directory, a, b, c, max_checkpoint_bytes=POLICY['max_checkpoint_bytes'])
                outer = directory/'manifest.json'; saved = json.loads(outer.read_bytes())
                outer.write_bytes(m.body(saved | {'version': 2}))
                with patch.object(engine.ann, 'load', side_effect=AssertionError('nested load')):
                    with self.assertRaises(ValueError):
                        engine.load(directory, a, b, c, expected_sha256=hashlib.sha256(outer.read_bytes()).hexdigest(), **policy)
                inner = directory/'annealing'/'manifest.json'
                inner.write_bytes(m.body(json.loads(inner.read_bytes()) | {'schema_version': 2}))
                outer.write_bytes(m.body(saved | {'annealing_sha256': hashlib.sha256(inner.read_bytes()).hexdigest()}))
                with patch.object(engine.ann.np, 'load', side_effect=AssertionError('array load')):
                    with self.assertRaises(ValueError):
                        engine.load(directory, a, b, c, expected_sha256=hashlib.sha256(outer.read_bytes()).hexdigest(), **policy)
        finally:
            engine.close(state)


from tradingagents.research.onchain_replication.neighborhoods import NeighborhoodIndex


class SingletonTest(unittest.TestCase):
    def test_empty_edges_through_owned_checkpoint_restore(self):
        source = graph([[0.], [.5]], [])
        index = NeighborhoodIndex(source)
        options = dict(hop_depth=1, maximum_neighborhood_nodes=10)
        a, b = index.neighborhood(0, options), index.neighborhood(1, options)
        self.assertEqual(a.edge_index.shape, (2, 0))
        self.assertEqual(b.edge_features.shape, (0, 1))
        c = config() | {'max_iterations': 2}
        expected = match_reference(a, b, c)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pair = m.PairSession.create(root, 'first', a, b, c, owner='d'*64,
                                        context=CONTEXT, policy=POLICY)
            reference = pair.save(); pair.close()
            pair = m.PairSession.resume(root, 'second', a, b, c, reference,
                                        owner='e'*64, expected_owner='d'*64,
                                        context=CONTEXT, policy=POLICY)
            try:
                for _ in range(100):
                    result = pair.step(max_operations=1)
                    if result is not None:
                        break
                else:
                    self.fail('singleton did not finish')
                self.assertEqual((result.score, result.convergence, result.iterations),
                                 (expected.score, expected.convergence, expected.iterations))
            finally:
                pair.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
