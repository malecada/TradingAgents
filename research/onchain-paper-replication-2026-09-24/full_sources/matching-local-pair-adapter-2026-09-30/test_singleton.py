"""Target the local identity's zero-edge byte-hashing branch and singleton solve."""
import tempfile
import unittest
from pathlib import Path
from test_adapter import m, graph, config, CONTEXT, POLICY, match_reference
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
