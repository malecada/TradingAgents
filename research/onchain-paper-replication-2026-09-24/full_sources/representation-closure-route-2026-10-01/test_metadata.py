"""Real compact reads with producer-specific caps and lineage hash wire parity."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from tradingagents.research.onchain_replication.provenance import canonical_bytes
from tradingagents.research.onchain_replication.evaluation import feature_hash
HERE=Path(__file__).resolve().parent

def api():
    spec=importlib.util.spec_from_file_location('closure_metadata_candidate',HERE/'closure.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Tests(unittest.TestCase):
    def test_prior_events_use_admitted_artifact_cap_and_keep_it_on_lease(self):
        m=api();self.assertTrue(callable(getattr(m,'snapshot_events',None)),'producer-aware prefix reader missing')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);metadata=m.saved.producer.Metadata(root)
            prefix=[{'stage':s} for s in ('samples_complete','dictionary_complete','mcm_progress','graph_complete')]
            for i,e in enumerate(prefix):
                raw=canonical_bytes(e)+(b' '*300 if i<2 else b'')
                (root/f'event-{i:06d}.json').write_bytes(raw)
            m.snapshot_events(metadata,root,prefix,artifact_cap=1024,mcm_cap=128,graph_cap=256)
            self.assertEqual([metadata.snapshots[root/f'event-{i:06d}.json'][2] for i in range(4)],[1024,1024,128,256])
            metadata.lease()
    def test_lineage_edge_hash_matches_wire_bytes_including_empty_and_noncontiguous(self):
        m=api();a=np.array([[0,1,2],[1,2,0]],dtype=np.int64)
        for x in (a,np.asfortranarray(a),a[:,::-1]):self.assertEqual(m.edge_hash(x),feature_hash(x))
        empty=a[:,:0]
        self.assertEqual(m.edge_hash(empty),hashlib.sha256(canonical_bytes({'shape':(2,0),'dtype':'int64'})).hexdigest())
if __name__=='__main__':unittest.main(verbosity=2)
