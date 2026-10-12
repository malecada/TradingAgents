"""Pure AST/hash engineering fixtures, not genuine Run/Target or trial authority."""
from pathlib import Path
import ast,json,hashlib,copy,types,unittest
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication';N=types.SimpleNamespace
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
body=lambda v:canonical(v)+b'\n'
digest=lambda b:hashlib.sha256(b).hexdigest()
cache_key=lambda v:digest(canonical(v))
def require(ok,why):
 if not ok:raise ValueError(why)
def functions(path,names,ns):
 t=ast.parse(path.read_text());t.body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names]
 for n in ast.walk(t):
  if isinstance(n,ast.FunctionDef):n.body=[x for x in n.body if not isinstance(x,ast.ImportFrom)]
 exec(compile(t,str(path),'exec'),ns);return ns
base=dict(require=require,cache_key=cache_key,thaw=copy.deepcopy,BACKEND='fixture-backend',graph_identity=lambda x:x)
functions(S/'imported_mcm_identity.py',{'workload_record'},base)
t=ast.parse((S/'imported_mcm_identity.py').read_text());method=next(n for n in next(x for x in t.body if isinstance(x,ast.ClassDef) and x.name=='Target').body if isinstance(n,ast.FunctionDef) and n.name=='derive_scope');exec(compile(ast.Module(body=[method],type_ignores=[]),str(S/'imported_mcm_identity.py'),'exec'),base)
ns=dict(base,io=N(_hash=digest,_json=body),compact_policy=N(effective_matching=lambda c,p:copy.deepcopy(c)))
functions(S/'compact_mcm_batched.py',{'_continuation_contract'},ns)
class Target:
 derive_scope=base['derive_scope']
 def __init__(self,nonce,gate_hash):
  self.key='1'*64;self._node_order='2'*64;self.graph=N(node_ids=('n0','n1'));self.dictionary=N(identity='3'*64,matching_config_hash='4'*64,config={'hops':2},representatives=tuple(str(i) for i in range(32)))
  self.policy={'numeric':{'extraction_limit':32},'batched':{'batch_cells':4096}}
  ad=N(experiment={'source_files':{'source.py':'5'*64}},inputs={'mcm':{'path':'mcm.json','sha256':digest(body(self.policy))}})
  run=N(admission=ad);claim_sha=cache_key({'registration_sha256':gate_hash,'nonce':nonce})
  binding={'experiment':'successor','source_commit':'source','claim_sha256':claim_sha,'registration_sha256':gate_hash,'workflow_identity':'6'*64}
  self.owner=N(bound=N(_run=run,record=binding),policy={'schedule':{'steps':10},'pair':{}},matching={'max_pair_entries':4096})
  # Same deterministic hash dependency edges as original binding→Owner→receipt.
  owner_identity=cache_key({'binding':binding});receipt=digest(body({'owner':owner_identity,'kind':'dictionary-import-complete'}))
  current={'original_dictionary':self.dictionary.identity,'original_matching':self.dictionary.matching_config_hash,'execution_matching':cache_key({'config':self.owner.matching,'backend':base['BACKEND']})}
  self._execution={'current':current,'execution_identity':cache_key({'import_receipt':receipt,'current':current})}
  self.scope=self.derive_scope();self.execution=N(_owner=self.owner,_bound=self.owner.bound)
 def contract(self):
  scope=self.scope;d={'rows':2,'cells':64,'motifs':32,'graph_hash':self.key,'node_order_hash':self._node_order,'workload_sha256':scope['workflow'],'purpose_schema_version':2};start={'rows':2,'cells':64,'graph_hash':self.key,'scope':scope}
  return ns['_continuation_contract'](self,start,self.policy,d),d

def fixture(nonce='one',gate='7'*64):
 t=Target(nonce,gate);c,d=t.contract();template={**c,'workflow_identity':None,'descriptor_sha256':None};m={'contract_mode':'genuine-target-contract-template-v1','contract':template,'runtime_policy_input':'mcm'}
 events=[]
 def pin(run,target):
  require(type(target) is Target and target.owner.bound._run is run,'fixture genuine-chain model required');return(target,target.owner,target.execution,target.owner.bound)
 def read(run,role,**kw):events.append('read');return body(t.policy)
 env=dict(require=require,body=body,digest=digest,_json=json.loads,_target_identity=pin,_bounded_input=read,_poll_target=lambda r,t:events.append('poll'),compact_mcm_batched=N(_continuation_contract=ns['_continuation_contract'],validate=lambda p,c:events.append('validate')))
 functions(P/'batched_continuation.py',{'_bind_contract_template'},env)
 return t,c,d,m,env,events
class Checks(unittest.TestCase):
 def test_full_preregistration_cycle_template_stability(self):
  t,c,d,m,e,_=fixture();frozen_hash=digest(body(m['contract']));gate=cache_key({'manifest_contract_sha256':frozen_hash})
  a=fixture('nonce-a',gate);b=fixture('nonce-b',gate)
  self.assertEqual(body(a[3]['contract']),body(b[3]['contract']));self.assertNotEqual(a[1]['workflow_identity'],b[1]['workflow_identity']);self.assertNotEqual(a[1]['descriptor_sha256'],b[1]['descriptor_sha256'])
  for f in (a,b):
   t,c,d,m,e,events=f;self.assertEqual(e['_bind_contract_template'](t.owner.bound._run,t,m,c),d);self.assertEqual(events,['read','poll','validate'])
  # Freezing the actual full contract changes registration/claim and therefore
  # the very operational digest being frozen: two deterministic steps differ.
  full_gate=cache_key({'manifest_contract_sha256':digest(body(a[1]))});changed=fixture('nonce-a',full_gate)
  self.assertNotEqual(changed[1]['workflow_identity'],a[1]['workflow_identity'])
 def test_only_two_null_slots(self):
  for field in ('source_sha256','config_sha256','dictionary_sha256','graph_hash','node_order_hash','cells','batch_cells','numerical_contract_sha256'):
   t,c,d,m,e,_=fixture();m['contract'][field]=None
   with self.assertRaises(ValueError):e['_bind_contract_template'](t.owner.bound._run,t,m,c)
  for field in ('workflow_identity','descriptor_sha256'):
   t,c,d,m,e,_=fixture();m['contract'][field]=c[field]
   with self.assertRaisesRegex(ValueError,'two-slot'):e['_bind_contract_template'](t.owner.bound._run,t,m,c)
 def test_wrong_runtime_workflow_descriptor_source_and_policy(self):
  for field in ('workflow_identity','descriptor_sha256','source_sha256','config_sha256','numerical_contract_sha256'):
   t,c,d,m,e,_=fixture();c[field]='0'*64
   with self.assertRaises(ValueError):e['_bind_contract_template'](t.owner.bound._run,t,m,c)
  for mutate in (lambda t:t.owner.bound._run.admission.experiment['source_files'].update(other='new'),lambda t:t.policy['numeric'].update(extraction_limit=64),lambda t:t.dictionary.config.update(hops=3)):
   t,c,d,m,e,_=fixture();mutate(t)
   with self.assertRaises(ValueError):e['_bind_contract_template'](t.owner.bound._run,t,m,c)
 def test_exact_types_and_roster(self):
  for value in (64.0,True):
   t,c,d,m,e,_=fixture();m['contract']['cells']=value
   with self.assertRaises(ValueError):e['_bind_contract_template'](t.owner.bound._run,t,m,c)
  for extra in (False,True):
   t,c,d,m,e,_=fixture()
   if extra:m['contract']['other']=1
   else:del m['contract']['source_sha256']
   with self.assertRaisesRegex(ValueError,'two-slot'):e['_bind_contract_template'](t.owner.bound._run,t,m,c)
 def test_chain_scope_mutation(self):
  t,c,d,m,e,_=fixture();t.scope={**t.scope,'workflow':'0'*64}
  with self.assertRaisesRegex(ValueError,'scope differs'):e['_bind_contract_template'](t.owner.bound._run,t,m,c)
  t,c,d,m,e,_=fixture()
  with self.assertRaises(ValueError):e['_bind_contract_template'](t.owner.bound._run,None,m,c)
 def test_revalidation_and_runtime_storage_source(self):
  tree=ast.parse((P/'batched_continuation.py').read_text());f={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
  self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_bind_contract_template' for n in ast.walk(f['verify_prefix'])),2)
  self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_bind_contract_template' for n in ast.walk(f['restore_prefix'])),1)
  text=ast.unparse(f['verify_prefix']);self.assertIn('body(expected_contract)',text);self.assertIn('descriptors[runtime_key] = body(runtime_descriptor)',text)
  # Original full-contract exact comparison survives literally in else branch.
  self.assertIn("m['contract'] == expected_contract",text)
if __name__=='__main__':unittest.main(verbosity=2)
