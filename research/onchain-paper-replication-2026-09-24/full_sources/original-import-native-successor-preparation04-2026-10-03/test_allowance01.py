"""Actual frozen constructor allowance, extracted AST only; no arrays/authority."""
import ast,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;FULL=HERE.parent
SOURCE=HERE/'generate_inputs01.py'
if len(sys.argv)>1 and sys.argv[1]=='--source':SOURCE=Path(sys.argv.pop(2));sys.argv.pop(1)
INVENTORY=FULL/'original-import-native-successor-preparation03-2026-10-03/source_inventory01.json'
ROOT=HERE.parents[3]
class Allowance(unittest.TestCase):
    def test_actual_registered_constructor_and_tiny_inputs_fit_selected_policy(self):
        inventory=json.loads(INVENTORY.read_bytes())['source_inventory']
        row=next(x for x in inventory if x['target']=='tradingagents/research/onchain_replication/array_neighborhoods.py')
        raw=(ROOT/row['origin']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
        tree=ast.parse(raw);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ArrayNeighborhoodIndex')
        init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
        statement=next(n for n in init.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='buffer_allowance' for t in n.targets))
        guard=next(n for n in init.body if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(n,ast.Attribute) and n.attr=='buffer_allowance' for n in ast.walk(n.test)))
        code=compile(ast.Expression(statement.value),'actual-buffer-allowance','eval')
        generator=ast.parse(SOURCE.read_bytes());fn=next(n for n in generator.body if isinstance(n,ast.FunctionDef) and n.name=='inputs')
        call=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='mcm_policy')
        numeric=eval(compile(ast.Expression(call.args[1]),'actual-policy','eval'),{'__builtins__':{}})['numeric'];self.assertEqual(numeric['max_buffer_bytes'],1048576)
        for n,expected,old in [(2,655600,10486000),(3,655692,10486092)]:
            scope=dict(n=n,e=n,node_width=32,edge_width=16,edge_chunk=numeric['edge_chunk'])
            allowance=eval(code,{'__builtins__':{}},scope);self.assertLessEqual(allowance,numeric['max_buffer_bytes']);self.assertEqual(allowance,expected)
            scope['edge_chunk']=65536;self.assertEqual(eval(code,{'__builtins__':{}},scope),old)
            self.assertGreater(old,numeric['max_buffer_bytes'])
        self.assertEqual(numeric['edge_chunk'],4096)
        self.assertTrue(any(isinstance(n,ast.Constant) and n.value=='neighborhood index buffer allowance exceeded' for n in ast.walk(guard)))
if __name__=='__main__':unittest.main(verbosity=2)
