"""Extracted actual draft function; explicitly qualified module-origin stand-ins."""
import ast,json,pathlib,types,sys,unittest
from unittest.mock import patch
from test_lineage02 import P,BASE,B,G,ROOT,SOURCE,ANCHOR,ROWS
class Tests(unittest.TestCase):
 def invoke(self,located):
  # No actual import/installation/authority is inferred from these module objects.
  builder=types.ModuleType('fixture_tools.capsule_builder01');builder.__dict__.update(B)
  generator=types.ModuleType('fixture_tools.generate_inputs01');generator.__dict__.update(G)
  if located:
   builder.__file__=str(ROOT/'fixture_tools/capsule_builder01.py');generator.__file__=str(ROOT/'fixture_tools/generate_inputs01.py')
  pkg=types.ModuleType('fixture_tools');pkg.capsule_builder01=builder;pkg.generate_inputs01=generator
  tree=ast.parse((P/'build_release_draft01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='held_metadata_draft')
  ns={'Path':pathlib.Path,'json':json,'require':B['require'],'__file__':str(ROOT/'proof_tools/build_release_draft01.py') if located else str(P/'build_release_draft01.py')}
  exec(compile(ast.Module([fn],[]),'exact-unmodified-draft-function','exec'),ns)
  with patch.dict(sys.modules,{'fixture_tools':pkg,'fixture_tools.capsule_builder01':builder,'fixture_tools.generate_inputs01':generator}):return ns['held_metadata_draft'](ROOT,SOURCE,ANCHOR,ROWS,{})
 def test_uninstalled_actual_origins_refuse(self):
  with self.assertRaisesRegex(ValueError,'helper origin differs'):self.invoke(False)
 def test_qualified_full_draft_composition_null_authority(self):
  result=self.invoke(True)
  self.assertEqual(len(result['source_document']['source_files']),199);self.assertEqual(len(result['source_document']['package_files']),148)
  self.assertEqual(len(result['input_plan']['remaining_roles']),15)
  for key in ['registration_authority','budget_authority','native_release','guarded_input_materialization']:self.assertIsNone(result[key])
  self.assertFalse(result['execution_admitted']);self.assertIsNone(result['runtime_readback']);self.assertIsNone(result['route_readback'])
  (P/'QUALIFIED_DRAFT_READBACK02.json').write_text(json.dumps({'qualification':'extracted original draft with synthetic module-origin labels, actual read-only Source04 199/148 Git/body checks; not actual installed candidate or release','result':result},sort_keys=True,indent=2)+'\n')
 def test_inverse_builder_and_exact_two_helpers(self):
  for n in ['generate_inputs01.py','build_release_draft01.py']:self.assertEqual((P/n).read_bytes(),(BASE/n).read_bytes())
  old=(P/'capsule_builder01.py.baseline04.txt').read_text();new=(P/'capsule_builder01.py').read_text();a=ast.parse(old);b=ast.parse(new)
  oldfn=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='held_source_plan');newfn=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='held_source_plan');lines=new.splitlines(True)
  edits=[(newfn.lineno,newfn.end_lineno,old.splitlines(True)[oldfn.lineno-1:oldfn.end_lineno])]
  for n in b.body:
   if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith('HELD_SOURCE04'):edits.append((n.lineno,n.end_lineno,[]))
  self.assertEqual(len(edits),5)
  for start,end,body in sorted(edits,reverse=True):lines[start-1:end]=body
  self.assertEqual(''.join(lines),old);self.assertEqual(ast.dump(ast.parse(''.join(lines))),ast.dump(a))
  # Within the sole changed function, inverse only the selected branch statements.
  f=ast.parse(ast.unparse(newfn)).body[0];base=ast.parse(ast.unparse(oldfn)).body[0]
  f.body=[n for n in f.body if not(isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='source04')]
  out=[]
  for n in f.body:
   if isinstance(n,ast.If) and ast.unparse(n.test)=='source04':
    if n.orelse:out.extend(n.orelse)
   else:out.append(n)
  f.body=out;self.assertEqual(ast.dump(f),ast.dump(base))
if __name__=='__main__':unittest.main(verbosity=2)
