"""Tiny fake graph callbacks exercise receipt/guard boundaries; no real arrays."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json

import verify_saved as worker


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.graphs=[dict(week=w,manifest={'path':w+'/manifest.json','sha256':'b'*64},
                    arrays=[{'declared_bytes':100}],graph_hash=w,nodes=2,directed_edges=1,
                    metadata={'admitted_count':3}) for w in ('first','second')]
        for name,value in [('RECEIPT',self.root),('ROOT',self.root)]:
            p=patch.object(worker,name,value);p.start();self.addCleanup(p.stop)
        self.source=patch.object(worker,'source_check',return_value='bound').start()
        self.guard=patch.object(worker,'live_guard',return_value={}).start()
        self.load=patch.object(worker,'load_metadata',return_value=({'graphs':self.graphs,'historical_dispositions':{'complete':7,'unavailable':102}},{})).start()
        self.stable=patch.object(worker,'unchanged').start()
        self.calls=[]
        def verify(path,**kwargs):
            self.calls.append((path,kwargs))
            return dict(graph_hash=path.parent.name,nodes=2,directed_edges=1,admitted_transactions=3,array_mappings_closed=True)
        self.verify=patch.object(worker,'verify',side_effect=verify).start()
        self.addCleanup(patch.stopall)
    def test_ordered_two_graph_receipts_and_complete(self):
        worker.main('source')
        self.assertEqual([p.parent.name for p,k in self.calls],['first','second'])
        self.assertTrue(all(k['max_array_bytes']==562558280 for p,k in self.calls))
        self.assertEqual(self.source.call_count,2)
        value=json.loads((self.root/'payload/complete.json').read_bytes())
        self.assertEqual(len(value['graphs']),2);self.assertEqual(value['empirical_trials'],0)
    def test_existing_attempt_refused_without_second_callback(self):
        worker.main('source')
        before=(self.root/'payload/complete.json').read_bytes()
        with self.assertRaises(FileExistsError):worker.main('source')
        self.assertEqual(len(self.calls),2)
        self.assertEqual(before,(self.root/'payload/complete.json').read_bytes())
    def test_source_refused_before_any_array_read(self):
        self.source.side_effect=ValueError('source changed')
        with self.assertRaisesRegex(ValueError,'source changed'):worker.main('source')
        self.verify.assert_not_called();self.assertTrue((self.root/'payload/failed.json').exists())
    def test_dead_guard_before_any_array_read(self):
        self.guard.side_effect=ValueError('stale guard')
        with self.assertRaisesRegex(ValueError,'stale guard'):worker.main('source')
        self.verify.assert_not_called()
    def test_failure_after_first_preserves_partial_receipt(self):
        original=self.verify.side_effect
        def fail_second(path,**kwargs):
            if path.parent.name=='second':raise ValueError('second rejected')
            return original(path,**kwargs)
        self.verify.side_effect=fail_second
        with self.assertRaisesRegex(ValueError,'second rejected'):worker.main('source')
        self.assertTrue((self.root/'payload/first.json').exists())
        self.assertTrue((self.root/'payload/failed.json').exists())
        self.assertFalse((self.root/'payload/complete.json').exists())
    def test_guard_failure_after_array_prevents_publication(self):
        self.guard.side_effect=[{}, {}, ValueError('guard lost')]
        with self.assertRaisesRegex(ValueError,'guard lost'):worker.main('source')
        self.assertEqual(len(self.calls),1);self.assertFalse((self.root/'payload/first.json').exists())
    def test_unclosed_mapping_cannot_publish(self):
        self.verify.return_value=dict(graph_hash='first',nodes=2,directed_edges=1,admitted_transactions=3,array_mappings_closed=False)
        self.verify.side_effect=None
        with self.assertRaisesRegex(ValueError,'summary mismatch'):worker.main('source')
        self.assertFalse((self.root/'payload/first.json').exists())


if __name__=='__main__':unittest.main(verbosity=2)
