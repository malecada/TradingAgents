"""No numerical work: compare actual old/new historical evidence AST slices."""
import ast,pathlib,unittest
D=pathlib.Path(__file__).resolve().parent;OLD=D.parent/'neural-cold-feature-handoff-proof-outer-preparation02-2026-10-03'
class Tests(unittest.TestCase):
 def test_whole_native_supervisor_claim_wait_raw_materialization_chain_unchanged(self):
  def part(path,name):
   fn=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name);start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='runtime_gate');end=next(i for i,n in enumerate(fn.body) if i>start and isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='material');return ast.dump(ast.Module(body=fn.body[start:end+2],type_ignores=[]))
  self.assertEqual(part(OLD/'proof_release01.py','authenticate_prior'),part(D/'proof_release01.py','authenticated_materialization'))
 def test_other_five_selected_proof_tools_unchanged(self):
  for name in ('proof_outer01.py','proof_raw01.py','proof_supervise01.py','runtime_gate01.py','build_release_draft01.py'):self.assertEqual((D/name).read_bytes(),(OLD/name).read_bytes())
 def test_actual_predecessor_rejects_required_child_source(self):
  fn=next(n for n in ast.parse((OLD/'proof_release01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='authenticate_prior');stmt=next(n for n in fn.body if isinstance(n,ast.Expr) and 'prior/current source commits conflict' in ast.unparse(n));ns={'accepted':{'source':'a'*40},'wait':{'source':'a'*40},'current':{'source':'b'*40}}
  def require(v,m):
   if not v:raise ValueError(m)
  ns['require']=require
  with self.assertRaisesRegex(ValueError,'prior/current source commits conflict'):exec(compile(ast.Module(body=[stmt],type_ignores=[]),'actual02false-refusal','exec'),ns)
if __name__=='__main__':unittest.main(verbosity=2)
