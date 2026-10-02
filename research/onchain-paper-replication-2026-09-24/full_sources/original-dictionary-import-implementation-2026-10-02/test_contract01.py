"""Pure AST validators only; no numerical imports or fake Binding creation."""
import ast
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent

def load():
    file=HERE/'original_import_preparation.py'
    if not file.exists():raise AssertionError('typed preparation source absent')
    tree=ast.parse(file.read_text())
    names={'require','required_stages','materialization_bytes'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    if len(nodes)!=len(names):raise AssertionError('required pure validator absent')
    ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(file),'exec'),ns);return ns

class Contract(unittest.TestCase):
    def test_prebirth_exact_stage_order(self):
        f=load()['required_stages']
        d={'dictionary_origin':'imported-original-v1','required_graphs':['a'*64,'b'*64]}
        self.assertEqual(f(d),('dictionary-import','mcm-'+'a'*64,'mcm-'+'b'*64))
        for bad in ({**d,'dictionary_origin':'fresh'}, {**d,'required_graphs':['b'*64,'a'*64]}, {**d,'required_graphs':['a'*64]*2}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):f(bad)
    def test_numeric_extent_uses_original_order_no_allocations(self):
        f=load()['materialization_bytes'];g={'node_ids':['a','b'],'node_features':[[1.,2.,3.,4.],[0.,0.,0.,0.]],'edge_index':[[0],[1]],'edge_features':[[1.,2.]],'edge_width':2}
        self.assertEqual(f({'representatives':[g]}),96)
        self.assertEqual(f({'representatives':[g,g]}),192)
        for bad in ({**g,'edge_index':[[0],[]]}, {**g,'edge_features':[]}, {**g,'node_features':[[1.],[2.,3.]]}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):f({'representatives':[bad]})

if __name__=='__main__':unittest.main()
