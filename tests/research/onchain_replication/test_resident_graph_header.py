"""Regression checks for mutable and oversized NPY header admission."""
import json
import struct
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_subsets import fixture
from tradingagents.research.onchain_replication.graph_store import save_graph,_resident_array
from tradingagents.research.onchain_replication.provenance import file_hash
class Tests(unittest.TestCase):
    def test_admitted_header_is_not_reparsed_from_mutable_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=save_graph(Path(tmp)/'g',fixture());info=json.loads(manifest.read_bytes())['arrays']['node_features']
            with patch.object(np,'load',side_effect=AssertionError('mutable header reparsed')):
                actual=_resident_array(manifest.parent/'node_features.npy',info)
            np.testing.assert_array_equal(actual,fixture().node_features)
    def test_large_header_length_refuses_before_header_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'oversized.npy';path.write_bytes(b'\x93NUMPY\x02\x00'+struct.pack('<I',2**30))
            with patch.object(np.lib.format,'read_array_header_2_0',side_effect=AssertionError('oversized header read reached')):
                with self.assertRaisesRegex(ValueError,'header length'):_resident_array(path,{'bytes':path.stat().st_size,'sha256':file_hash(path)})
    def test_payload_change_during_allocation_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=save_graph(Path(tmp)/'g',fixture());info=json.loads(manifest.read_bytes())['arrays']['node_features'];path=manifest.parent/'node_features.npy'
            original=np.empty
            def mutate(shape,*args,**kwargs):
                raw=bytearray(path.read_bytes());raw[-1]^=1;path.write_bytes(raw)
                self.assertEqual(shape,fixture().node_features.shape)
                return original(shape,*args,**kwargs)
            with patch.object(np,'empty',side_effect=mutate):
                with self.assertRaisesRegex(ValueError,'changed|hash'):_resident_array(path,info)
if __name__=='__main__':unittest.main(verbosity=2)
