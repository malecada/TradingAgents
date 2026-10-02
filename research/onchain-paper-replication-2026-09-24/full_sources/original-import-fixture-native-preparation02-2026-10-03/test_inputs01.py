import importlib.util,unittest,ast,struct,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent

def module():
    p=D/'generate_inputs01.py';assert p.exists(),'deterministic input generator missing'
    s=importlib.util.spec_from_file_location('tiny_input_generator',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Inputs(unittest.TestCase):
    def test_safe_npy_exact_header_extent(self):
        m=module();raw=m.npy('<f8',(2,2),[1.,0.,0.,1.]);self.assertEqual(raw[:8],b'\x93NUMPY\x01\x00')
        n=struct.unpack('<H',raw[8:10])[0];header=ast.literal_eval(raw[10:10+n].decode().strip());self.assertEqual(header,{'descr':'<f8','fortran_order':False,'shape':(2,2)});self.assertEqual(raw[10+n:],struct.pack('<4d',1,0,0,1));self.assertEqual(len(raw)%64,32)
        with self.assertRaises(ValueError):m.npy('|O',(1,),[object()])
    def test_graph_recipe_denominator_and_members(self):
        m=module();graphs,files=m.graphs();self.assertEqual(sorted(x['nodes'] for x in graphs),[2,3]);self.assertEqual(sum(x['nodes']*32 for x in graphs),160)
        self.assertEqual([x['graph_hash'] for x in graphs],sorted(x['graph_hash'] for x in graphs))
        for g in graphs:
            value=json.loads(files[g['manifest']]);self.assertEqual(value['graph_hash'],g['graph_hash'])
            for name,info in value['arrays'].items():
                body=files[str(Path(g['manifest']).parent/info['path'])];self.assertEqual(hashlib.sha256(body).hexdigest(),info['sha256']);self.assertLessEqual(len(body),65536)
    def test_graph_bytes_deterministic(self):
        m=module();self.assertEqual(m.graphs(),m.graphs())
if __name__=='__main__':unittest.main()
