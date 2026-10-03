"""Actual source selection/whole-AST proof; no parent main or child launched."""
import ast,pathlib,sys,unittest
SOURCE=pathlib.Path(sys.argv[1]);BASE=pathlib.Path(sys.argv[2]);del sys.argv[1:]
OLD='compact-cold-inputs-20261003-01';NEW='compact-cold-comparison-20261003-01'
MAPPING={NEW:OLD,'compare':'materialize','this exact parent selects only comparison':'this exact parent selects only materialization'}
class Cases(unittest.TestCase):
 def select(self,identity,phase):
  tree=ast.parse(SOURCE.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='require');main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');statement=next(n for n in main.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(x,ast.Constant) and type(x.value)is str and x.value.startswith('this exact parent selects only ') for x in n.value.args));namespace={'identity':identity,'request':{'phase':phase}};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn,statement],type_ignores=[])),str(SOURCE),'exec'),namespace)
 def test_actual_compare_selection(self):self.select(NEW,'compare')
 def test_old_materialization_refused(self):
  with self.assertRaises(ValueError):self.select(OLD,'materialize')
 def test_mixed_or_unknown_selection_refused(self):
  for identity,phase in ((NEW,'materialize'),(OLD,'compare'),(NEW,'unknown'),('unused','compare')):
   with self.subTest(identity=identity,phase=phase),self.assertRaises(ValueError):self.select(identity,phase)
 def test_exact_three_literal_delta_and_inverse_whole_AST(self):
  selected=ast.parse(SOURCE.read_text());before=ast.parse(BASE.read_text());seen=[]
  class Normalize(ast.NodeTransformer):
   def visit_Constant(self,node):
    if type(node.value)is str and node.value in MAPPING:seen.append(node.value);return ast.copy_location(ast.Constant(MAPPING[node.value]),node)
    return node
  normalized=Normalize().visit(selected);self.assertEqual(sorted(seen),sorted(MAPPING));self.assertEqual(ast.dump(normalized,include_attributes=False),ast.dump(before,include_attributes=False))
 def test_process_io_cleanup_and_eight_field_wait_exact(self):
  selected=ast.parse(SOURCE.read_text());before=ast.parse(BASE.read_text());functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
  a,b=functions(selected),functions(before)
  for name in a.keys()-{'main'}:self.assertEqual(a[name],b[name],name)
  call=next(n for n in ast.walk(selected) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='write' and len(n.args)>2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='wait.json')
  self.assertEqual({n.value for n in call.args[2].keys},{'schema_version','identity','source','wrapper_pid','wrapper_exit_code','command','request','output_root'})
if __name__=='__main__':unittest.main(verbosity=2)
