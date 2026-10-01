"""Compare float32 MCM size prediction with actual serializer bytes."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from tradingagents.research.onchain_replication.component_store import save_component

HERE=Path(__file__).resolve().parent
def api():
    spec=importlib.util.spec_from_file_location('mcm_sizes',HERE/'publication.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Tests(unittest.TestCase):
    def test_float32_sizes_equal_actual_component_encoding_for_all_supported_layouts(self):
        m=api();predict=getattr(m,'encoded_size',m.producer.encoded_size)
        a=np.arange(24,dtype=np.float32).reshape(4,6)
        for name,matrix in [('c',a),('f',np.asfortranarray(a)),('strided',a[::2,::2]),('reversed',a[::-1]),('one',a[:1,:1])]:
            with self.subTest(layout=name),tempfile.TemporaryDirectory() as temp:
                try:manifest,total,numeric=predict(matrix,{'purpose':'tiny MCM'})
                except ValueError as error:self.fail(f'valid float32 MCM rejected: {error}')
                path=save_component(Path(temp)/'out',matrix,{'purpose':'tiny MCM'})
                self.assertEqual(manifest,path.stat().st_size)
                self.assertEqual(total,sum(p.stat().st_size for p in path.parent.iterdir()))
                self.assertEqual(numeric,matrix.nbytes)
                np.testing.assert_array_equal(np.load(path.parent/'array-000000.npy',allow_pickle=False),matrix)
    def test_non_float32_or_non_matrix_payload_refuses(self):
        m=api();self.assertTrue(hasattr(m,'encoded_size'),'dedicated MCM size contract absent')
        for value in [np.zeros((2,2),dtype=d) for d in ('float64','int64','>f4','float16','object')]+[np.zeros(2,dtype=np.float32),np.zeros((0,2),dtype=np.float32)]:
            with self.subTest(shape=value.shape,dtype=value.dtype),self.assertRaises(ValueError):m.encoded_size(value,{})

if __name__=='__main__':unittest.main(verbosity=2)
