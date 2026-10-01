"""Independent NPY serialization comparisons for pre-write content bindings."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from tradingagents.research.onchain_replication.component_store import save_component

HERE=Path(__file__).resolve().parent
def api():
    path=HERE/'encoded_hashes.py';assert path.exists(),'encoded feature hashing missing'
    spec=importlib.util.spec_from_file_location('encoded_feature_hashes',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Tests(unittest.TestCase):
    def test_bounded_hashes_equal_actual_npy_bytes_for_all_layouts(self):
        m=api();a=np.arange(35,dtype=np.float32).reshape(5,7)/35;e=np.array([[0,1,2,3],[1,2,3,4]],dtype=np.int64)
        for x,y in ((a,e),(np.asfortranarray(a),np.asfortranarray(e)),(a[::-1,::2],e[:,::-1]),(a,e[:,:0])):
            for chunk in (1,2,13):
                with self.subTest(strides=(x.strides,y.strides),chunk=chunk),tempfile.TemporaryDirectory() as tmp:
                    feature={'mcm':x,'edge_index':y};expected=m.descriptors(feature,chunk)
                    path=save_component(Path(tmp)/'component',{'feature':feature,'aligned_vectors':None},{})
                    actual=json.loads(path.read_text())['arrays'];self.assertEqual(expected,actual)
    def test_invalid_chunk_or_schema_refuses(self):
        m=api();a=np.ones((2,2),dtype=np.float32);e=np.zeros((2,1),dtype=np.int64)
        for chunk in (0,True,65537):
            with self.subTest(chunk=chunk),self.assertRaises(ValueError):m.descriptors({'mcm':a,'edge_index':e},chunk)
        for feature in ({'mcm':a,'edge_index':e,'extra':a},{'mcm':a.astype('float64'),'edge_index':e},{'mcm':a,'edge_index':e.astype('int32')}):
            with self.subTest(keys=list(feature)),self.assertRaises(ValueError):m.descriptors(feature,2)

if __name__=='__main__':unittest.main(verbosity=2)
