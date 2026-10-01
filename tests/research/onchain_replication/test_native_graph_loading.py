"""Resident graph loading validates numeric extent before allocation."""
import io
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_subsets import fixture
from tradingagents.research.onchain_replication.graph_store import save_graph,load_graph,_resident_array
from tradingagents.research.onchain_replication.provenance import file_hash
class Tests(unittest.TestCase):
    def test_resident_values_equal_default_without_memmap_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            g=fixture();path=save_graph(Path(tmp)/'g',g);r=load_graph(path,file_hash(path),resident=True)
            for name in ('node_features','edge_index','edge_features','edge_aggregates'):
                a=getattr(r,name);self.assertNotIsInstance(a,np.memmap)
                np.testing.assert_array_equal(a,getattr(g,name))
            self.assertEqual(r.node_ids,g.node_ids)
    def test_lying_manifest_bytes_refused_before_numpy_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=save_graph(Path(tmp)/'g',fixture());m=json.loads(path.read_bytes());name='node_features'
            with patch.object(np,'load',side_effect=AssertionError('allocation reached')):
                with self.assertRaisesRegex(ValueError,'extent'):_resident_array(path.parent/(name+'.npy'),dict(m['arrays'][name],bytes=1))
    def test_oversized_header_shape_refused_before_numpy_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'huge.npy'
            with path.open('wb') as stream:np.lib.format.write_array_header_1_0(stream,{'descr':'<f8','fortran_order':False,'shape':(2**40,)})
            with patch.object(np,'load',side_effect=AssertionError('allocation reached')):
                with self.assertRaisesRegex(ValueError,'header extent'):_resident_array(path,{'bytes':path.stat().st_size,'sha256':file_hash(path)})
if __name__=='__main__':unittest.main(verbosity=2)
