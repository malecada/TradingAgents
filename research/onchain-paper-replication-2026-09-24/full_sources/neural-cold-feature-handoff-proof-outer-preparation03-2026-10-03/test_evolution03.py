"""Source-only typed evolution fixtures; no Git repository/claims/numerics."""
import ast,copy,os,pathlib,types,unittest
D=pathlib.Path(__file__).resolve().parent;SOURCE=pathlib.Path(os.environ.get('RELEASE_SOURCE',D/'proof_release01.py'))
def require(v,m):
 if not v:raise ValueError(m)
def extracted(name,env):
 tree=ast.parse(SOURCE.read_text());node=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),None)
 if node is None:raise AssertionError('missing actual helper '+name)
 exec(compile(ast.Module(body=[node],type_ignores=[]),'actual '+name,'exec'),env);return env[name]
A='a'*40;B='b'*40;MAT='compact-cold-inputs-20261003-01';CMP='compact-cold-comparison-20261003-01'
def fixture():
 first={'parent':None,'family':'f','inputs':{'environment':{'path':'env','sha256':'e'*64,'dataset':'synthetic-cold'}},'source_files':{str(i):'s'*64 for i in range(195)}}
 old={'schema_version':1,'program_id':'compact-cold-engineering-20261003','families':{'f':{'attempt_budget':2,'prior_attempts':0,'history_reference':'unchanged'}},'datasets':{'synthetic-cold':{'exposures':[]}},'experiments':{MAT:first}}
 second=copy.deepcopy(first);second['parent']=MAT;second['inputs']|={'execution_job':{'path':'emitted/job','sha256':'j'*64,'dataset':'synthetic-cold'}};new=copy.deepcopy(old);new['experiments'][CMP]=second
 material={'inputs':{'future_execution_job':second['inputs']['execution_job']}}
 return old,new,second,material
class Tests(unittest.TestCase):
 def test_registration_addition_and_corruptions(self):
  fn=extracted('_registration_evolution',{'require':require,'IDENTITIES':{'materialize':MAT,'compare':CMP},'MATERIAL_INPUTS':{'future_execution_job'}});old,new,second,material=fixture();fn(old,new,second,material)
  for mutate in (lambda x:x['families']['f'].update(attempt_budget=3),lambda x:x['datasets']['synthetic-cold']['exposures'].append('changed'),lambda x:x['experiments'][MAT].update(parent='other'),lambda x:x['experiments'][CMP].update(parent=None),lambda x:x['experiments'][CMP]['inputs']['environment'].update(sha256='x'*64),lambda x:x['experiments'][CMP]['source_files'].update({'0':'x'*64}),lambda x:x.update(history='invented'),lambda x:x['experiments'].update(other={})):
   changed=copy.deepcopy(new);mutate(changed)
   with self.assertRaises(ValueError):fn(old,changed,changed['experiments'][CMP],material)
 def test_historical_head_and_exact_parent(self):
  outputs={'head':B,'parents':B+' '+A}
  def check(command,**kw):return outputs['head']+'\n' if command[1]=='rev-parse' else outputs['parents']+'\n'
  fn=extracted('_source_head',{'require':require,'subprocess':types.SimpleNamespace(check_output=check)})
  self.assertEqual(fn(None,A,'retained-materialization'),B);self.assertEqual(fn(None,B,'unclaimed'),B)
  outputs['head']=A;outputs['parents']=A+' '+'c'*40;self.assertEqual(fn(None,A,'retained-materialization'),A)
  for parents in (B+' '+'c'*40,B+' '+A+' '+'c'*40):
   outputs.update(head=B,parents=parents)
   with self.assertRaises(ValueError):fn(None,A,'retained-materialization')
  with self.assertRaises(ValueError):fn(None,A,'unclaimed')
 def test_real_historical_authentication_chain_still_present(self):
  tree=ast.parse(SOURCE.read_text());fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='authenticated_materialization'),None);self.assertIsNotNone(fn)
  calls={ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)};self.assertTrue({'_release_context','authenticate','closure','runtime_gate.check'}<=calls)
  text=ast.unparse(fn)
  for fragment in ('wait[\'controller_exit_code\']','claim[\'owner_pid\']','child[\'pid\']','intent[\'worker_command\']','set(material[\'inputs\'])'):self.assertIn(fragment,text)
if __name__=='__main__':unittest.main(verbosity=2)
