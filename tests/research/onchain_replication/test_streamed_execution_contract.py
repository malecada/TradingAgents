"""Pure stdlib checks compile exact validator AST without importing numerical code."""
import ast
from pathlib import Path
from types import MappingProxyType
import unittest
ROOT=Path(__file__).resolve().parents[3]
PACKAGE=ROOT/'tradingagents/research/onchain_replication'
POLICY={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536}

def function(file,name):
    tree=ast.parse((PACKAGE/file).read_text())
    node=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),None)
    if node is None:raise AssertionError('missing selected validator '+name)
    namespace={'MappingProxyType':MappingProxyType}
    exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),namespace)
    return namespace[name]

class ExecutionContract(unittest.TestCase):
    def test_selector_exact_and_detached(self):
        validate=function('model.py','validate_execution');source=dict(POLICY)
        self.assertIsNone(validate(None));selected=validate(source);source['block_edges']=1
        self.assertEqual(dict(selected),POLICY)
        with self.assertRaises(TypeError):selected['block_edges']=1
    def test_selector_refusals(self):
        validate=function('model.py','validate_execution')
        for bad in ({},True,{'extra':1,**POLICY},{**POLICY,'backend':'unknown'},
                    {**POLICY,'schema_version':True},{**POLICY,'block_edges':True},
                    {**POLICY,'block_edges':0},{**POLICY,'block_edges':65537}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):validate(bad)
    def test_resource_versions_explicit(self):
        schema=function('neural_resource.py','_plan_schema')
        old={'schema_version':1,'model_input':'m','graph_activation_checkpointing':False,'cells':[],'limits':{}}
        schema(old);schema({**old,'schema_version':2,'model_execution':dict(POLICY)})
        for bad in ({**old,'model_execution':dict(POLICY)},{**old,'schema_version':2},
                    {**old,'schema_version':True},{**old,'schema_version':3},
                    {**old,'schema_version':2,'model_execution':dict(POLICY),'other':1}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):schema(bad)
    def test_exact_candidate_source(self):
        candidate=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/neural-streamed-gat-candidate-2026-10-02/candidate02.py'
        self.assertEqual((PACKAGE/'streamed_gat.py').read_bytes(),candidate.read_bytes())

if __name__=='__main__':unittest.main()
