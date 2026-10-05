"""Finite offline metadata tests; no Admission, claim, checkpoint decoding or numerical import."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
REFUSAL=HERE.parent/'financial-wrapper-continuation-outcome-review01-2026-10-05/FULL_REFUSAL_RECOVERY_PROOF01.json'
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
H=module('candidate_helper',HERE/'operational_source_compatibility.py')
LEGACY=module('legacy_helper',CAP/H.HELPER)
PRE=module('candidate_preclaim',HERE/'preclaim01.py')
class Successor(unittest.TestCase):
 def setUp(self):
  self.raw=(CAP/'fixture_inputs/financial_wrapper_compatibility01/policy.json').read_bytes();self.old=json.loads(self.raw)
  self.refusal=REFUSAL.read_bytes();self.after=dict(self.old['target']['installed'])
  for k in H.SUCCESSOR_DELTA:self.after[k]=H.sha((HERE/Path(k).name).read_bytes())
  self.edge={'schema_version':1,'kind':'same-family-continuation-source-successor-v1','original_policy_sha256':H.ORIGINAL_POLICY_SHA,'consumer':{'experiment':H.SUCCESSOR_ID,'cell_id':H.SUCCESSOR_CELL},'installed':self.after,'allowed_delta':[{'path':k,'old_sha256':self.old['target']['installed'][k],'new_sha256':self.after[k]} for k in sorted(H.SUCCESSOR_DELTA)],'original_closure_input':'successor_original_closure','refusal_input':'successor_refusal'}
 def check(self,edge=None,raw=None,refusal=None):
  return H.validate_successor(self.old,self.raw if raw is None else raw,self.edge if edge is None else edge,self.after[H.HELPER],self.refusal if refusal is None else refusal)
 def test_red_legacy_rejects_successor_map_green_additive(self):
  with self.assertRaises(LEGACY.Unavailable):LEGACY.validate_maps(self.old['historical']['installed'],self.after,self.after[H.HELPER])
  effective=self.check();self.assertEqual(effective['consumers']['continue100'],self.edge['consumer']);self.assertEqual(self.old,json.loads(self.raw))
 def test_legacy_preserved(self):
  self.assertEqual(H.validate_contract(self.old,H.ORIGINAL_HELPER_SHA),LEGACY.validate_contract(self.old,H.ORIGINAL_HELPER_SHA))
  with self.assertRaises(H.Unavailable):H.validate_maps(self.old['historical']['installed'],self.after,self.after[H.HELPER])
 def test_wrong_identity_cell_old_reserved(self):
  for key,value in [('experiment',H.RESERVED_ID),('experiment','other'),('cell_id','other')]:
   edge=copy.deepcopy(self.edge);edge['consumer'][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(H.Unavailable):self.check(edge)
 def test_maps_and_delta(self):
  for mode in ['omit','extra','science','reflexive','delta','checker']:
   edge=copy.deepcopy(self.edge)
   if mode=='omit':del edge['installed'][H.PREFIX+'training.py']
   if mode=='extra':edge['installed']['other']='1'*64
   if mode=='science':edge['installed'][H.PREFIX+'training.py']='1'*64
   if mode=='reflexive':edge['installed'][H.HELPER]=self.old['target']['installed'][H.HELPER]
   if mode=='delta':edge['allowed_delta']=[]
   if mode=='checker':edge['installed'][H.HELPER]='1'*64
   with self.subTest(mode=mode),self.assertRaises(H.Unavailable):self.check(edge)
 def test_original_policy_and_refusal(self):
  with self.assertRaises(H.Unavailable):self.check(raw=self.raw+b' ')
  refusal=json.loads(self.refusal);refusal['namespace_reuse_authorized']=True
  with self.assertRaises(H.Unavailable):self.check(refusal=H.canonical(refusal))
 def reference(self):
  consumer=self.old['consumers']['complete100'];claim=json.loads((CAP/'research_runs'/consumer['experiment']/'claim.json').read_bytes())
  fit=CAP/'research_artifacts/onchain_fit_cells'/H.sha(consumer['cell_id'].encode())/consumer['experiment']
  complete=json.loads((fit/'complete.json').read_bytes());manifest=json.loads(Path(complete['checkpoint']).read_bytes());old=manifest['provenance'];new=copy.deepcopy(old);new.update(source_hashes=sorted(set(self.after.values())),source_commit='1'*40,cell_id=H.SUCCESSOR_CELL)
  return claim,old,new
 def test_real_reference_provenance_metadata(self):
  claim,old,new=self.reference();H.validate_successor_reference(self.old,self.check(),claim,old,new)
  for target,key,value in [('old','source_hashes',new['source_hashes']),('new','source_hashes',old['source_hashes']),('new','config_hash','0'*64),('new','input_hash','0'*64),('old','source_commit','0'*40),('old','cell_id',H.SUCCESSOR_CELL)]:
   a,b=copy.deepcopy(old),copy.deepcopy(new);(a if target=='old' else b)[key]=value
   with self.subTest(target=target,key=key),self.assertRaises(H.Unavailable):H.validate_successor_reference(self.old,self.check(),claim,a,b)
  for mutation in ('policy','source','identity'):
   c=copy.deepcopy(claim)
   if mutation=='policy':c['inputs'][H.ROLE]['sha256']='0'*64
   if mutation=='source':c['experiment']['source_files'][H.PREFIX+'training.py']='0'*64
   if mutation=='identity':c['experiment_id']=H.RESERVED_ID
   with self.subTest(mutation=mutation),self.assertRaises(H.Unavailable):H.validate_successor_reference(self.old,self.check(),c,old,new)
 def test_registered_successor_proofs(self):
  edge_raw=H.canonical(self.edge);bodies={H.ROLE:self.raw,H.SUCCESSOR_ROLE:edge_raw,'successor_refusal':self.refusal,'successor_original_closure':H.canonical({'installed':self.old['target']['installed'],'scientific_model':H.MODEL,'scientific_training':H.TRAINING,'schema_version':1,'candidate02':self.old['target']['installed'][H.PREFIX+'financial_execution.py']})}
  for role in H.SUCCESSOR_PROOFS:bodies[role]=H.canonical({'schema_version':1,'kind':role,'decision':'accepted','policy_sha256':H.sha(edge_raw),'original_policy_sha256':H.ORIGINAL_POLICY_SHA,'historical_map_sha256':H.sha(H.canonical(self.old['target']['installed'])),'target_map_sha256':H.sha(H.canonical(self.after)),'checker_sha256':self.after[H.HELPER],'refusal_sha256':H.REFUSAL_SHA})
  inputs={k:{'path':k} for k in bodies};sources={k:H.sha(v) for k,v in bodies.items()}
  self.assertEqual(H.successor_context(self.old,self.raw,bodies.__getitem__,sources,inputs,self.after[H.HELPER]),self.check())
  original_closure=bodies['successor_original_closure']
  malformed=json.loads(original_closure);malformed['candidate02']='0'*64
  bodies['successor_original_closure']=H.canonical(malformed)
  with self.assertRaises(H.Unavailable):H.successor_context(self.old,self.raw,bodies.__getitem__,sources,inputs,self.after[H.HELPER])
  bodies['successor_original_closure']=original_closure
  sources[H.SUCCESSOR_ROLE]='0'*64
  with self.assertRaises(H.Unavailable):H.successor_context(self.old,self.raw,bodies.__getitem__,sources,inputs,self.after[H.HELPER])
 def test_preclaim_original_closure_route(self):
  class Inputs:
   registered={H.SUCCESSOR_ROLE:None}
   def json(inner,role):return self.edge
   def raw(inner,role):return role.encode()
  self.assertEqual(PRE._original_closure_raw(Inputs(),self.old),b'successor_original_closure')
 def test_genuine_preclaim_complete_path(self):
  sys.path.insert(0,str(CAP))
  from tradingagents.research import verify
  gate=json.loads((CAP/'fixture_inputs/financial_wrapper_continuation01/gates.json').read_bytes())
  registration=gate['experiments'][H.RESERVED_ID]['inputs'];reader=PRE.Reader();base=PRE.Inputs(CAP,registration,reader)
  plan=base.json('wrapper_plan');descriptor=base.json(plan['reference_input'])
  oldclosure_raw=(CAP/registration['source_closure']['path']).read_bytes()
  class Inputs:
   root=CAP
   registered={**registration,H.SUCCESSOR_ROLE:{'path':'metadata-only-edge','sha256':'0'*64}}
   def raw(inner,role):
    if role==H.SUCCESSOR_ROLE:return H.canonical(self.edge)
    if role=='successor_original_closure':return oldclosure_raw
    return base.raw(role)
   def json(inner,role):return json.loads(inner.raw(role))
   def exact(inner,role,path):return base.exact(role,path)
   def path(inner,role):return base.path(role)
  claim,old,new=self.reference()
  self.assertEqual(PRE._complete(Inputs(),descriptor,self.check(),'complete100',new,CAP,H,verify,reader),claim)
  bad=copy.deepcopy(descriptor);bad['provenance']['config_hash']='0'*64
  with self.assertRaises(H.Unavailable):PRE._complete(Inputs(),bad,self.check(),'complete100',new,CAP,H,verify,reader)
 def test_successor_requires_original_role(self):
  fixture=module('candidate_fixture',HERE/'financial_wrapper_fixture.py')
  fixture.require_compatibility_roles({})
  fixture.require_compatibility_roles({H.ROLE:None})
  fixture.require_compatibility_roles({H.ROLE:None,H.SUCCESSOR_ROLE:None})
  with self.assertRaises(fixture.Unavailable):fixture.require_compatibility_roles({H.SUCCESSOR_ROLE:None})
 def test_nonnumerical(self):self.assertFalse({'torch','numpy','scipy','pandas'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
