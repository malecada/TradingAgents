import copy
import unittest
from build_inventory import dimensions

class Dimensions(unittest.TestCase):
    def fixture(self):
        manifest={'graph_hash':'abc','arrays':{k:{'bytes':100} for k in ('node_features','node_ids','edge_index','edge_features','edge_aggregates')}}
        verification={'status':'complete','graph_hash':'abc','nodes':7,'directed_edges':11,'array_bytes':500}
        return manifest,verification
    def test_payload_arithmetic(self):
        manifest,verification=self.fixture();r=dimensions(manifest,verification)
        self.assertEqual((r['mcm_float32_payload_bytes'],r['mcm_float64_payload_bytes'],r['mcm_pair_evaluations']),(896,1792,224))
    def test_identity_and_byte_mismatches(self):
        for key,value in (('graph_hash','foreign'),('array_bytes',501),('status','failed'),('nodes',True)):
            with self.subTest(key=key):
                manifest,verification=self.fixture();verification[key]=value
                with self.assertRaises(ValueError):dimensions(manifest,verification)
    def test_missing_or_extra_graph_member(self):
        for remove in (True,False):
            manifest,verification=self.fixture()
            if remove:del manifest['arrays']['node_ids']
            else:manifest['arrays']['foreign']={'bytes':1}
            with self.assertRaises(ValueError):dimensions(manifest,verification)
if __name__=='__main__':unittest.main(verbosity=2)
