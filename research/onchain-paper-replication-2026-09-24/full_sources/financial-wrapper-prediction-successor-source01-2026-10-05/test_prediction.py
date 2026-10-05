"""Pure invented metadata only: no genuine success, Admission or Run is manufactured."""
import copy,importlib.util,json,sys,unittest,ast
from pathlib import Path
P=Path(__file__).parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
H=load('prediction_candidate',P/'operational_source_compatibility.py')
F=load('prediction_fixture',P/'financial_wrapper_fixture.py')
PRE=load('prediction_preclaim',P/'preclaim01.py')
class Prediction(unittest.TestCase):
 def setUp(self):
  self.original_raw=(CAP/'fixture_inputs/financial_wrapper_compatibility01/policy.json').read_bytes();self.original=json.loads(self.original_raw)
  self.cont_raw=(CAP/'fixture_inputs/financial_wrapper_continuation_successor01/successor.json').read_bytes();self.cont=json.loads(self.cont_raw)
  self.continued=H.validate_successor(self.original,self.original_raw,self.cont,H.CONTINUATION_HELPER_SHA,(CAP/'fixture_inputs/financial_wrapper_continuation_successor01/refusal.json').read_bytes())
  after=dict(self.cont['installed'])
  for k in H.PREDICTION_DELTA:after[k]=H.sha((P/Path(k).name).read_bytes())
  self.edge={'schema_version':1,'kind':'same-family-prediction-source-successor-v1','continuation_policy_sha256':H.CONTINUATION_POLICY_SHA,'consumer':{'experiment':H.PREDICTION_ID,'cell_id':H.SUCCESSOR_CELL},'installed':after,'allowed_delta':[{'path':k,'old_sha256':self.cont['installed'][k],'new_sha256':after[k]} for k in sorted(H.PREDICTION_DELTA)],'continuation_closure_input':'prediction_continuation_closure','parent_recovery_input':'prediction_parent_recovery'}
 def effective(self,edge=None):return H.validate_prediction_successor(self.continued,self.cont_raw,edge or self.edge,self.edge['installed'][H.HELPER])
 def metadata(self):
  # Only arguments to a pure predicate; never verified or written as a claim.
  claim={'experiment_id':H.SUCCESSOR_ID,'source':H.CONTINUATION_SOURCE,'design_source':H.CONTINUATION_SOURCE,'program_id':H.PROGRAM,'bindings':None,'bindings_sha256':None,'experiment':{'family':H.FAMILY,'cells':[H.SUCCESSOR_CELL],'source_files':self.cont['installed']},'inputs':{H.ROLE:{'sha256':H.ORIGINAL_POLICY_SHA},H.SUCCESSOR_ROLE:{'sha256':H.CONTINUATION_POLICY_SHA},'source_closure':{'sha256':'9'*64}}}
  old={'source_commit':H.CONTINUATION_SOURCE,'source_hashes':sorted(set(self.cont['installed'].values())),'cell_id':H.SUCCESSOR_CELL,'config_hash':'c'*64,'input_hash':'d'*64,'dictionary_hash':'e'*64,'fold_id':'synthetic-16x28-distinct'}
  new=copy.deepcopy(old);new.update(source_commit='1'*40,source_hashes=sorted(set(self.edge['installed'].values())))
  return claim,old,new
 def test_legacy_red_new_green_metadata_only(self):
  with self.assertRaises(H.Unavailable):H.validate_prediction_parent(self.original,H.ORIGINAL_POLICY_SHA,'9'*64,H.SUCCESSOR_ID,{},self.cont['installed'],[H.SUCCESSOR_CELL])
  self.assertEqual(self.effective()['consumers']['predict']['experiment'],H.PREDICTION_ID)
 def test_exact_identity_maps(self):
  for mutation in ('identity','science','missing','extra','delta','checker'):
   edge=copy.deepcopy(self.edge)
   if mutation=='identity':edge['consumer']['experiment']=H.SUCCESSOR_ID
   if mutation=='science':edge['installed'][H.PREFIX+'training.py']='0'*64
   if mutation=='missing':del edge['installed'][H.PREFIX+'training.py']
   if mutation=='extra':edge['installed']['other']='0'*64
   if mutation=='delta':edge['allowed_delta']=[]
   if mutation=='checker':edge['installed'][H.HELPER]='0'*64
   with self.subTest(mutation=mutation),self.assertRaises(H.Unavailable):self.effective(edge)
 def test_every_scientific_field_and_source_list(self):
  claim,old,new=self.metadata();H.validate_prediction_successor_parent(self.cont,self.effective(),claim,old,new,'9'*64)
  for key in old:
   bad=copy.deepcopy(old);bad[key]='bad'
   with self.subTest(key=key),self.assertRaises(H.Unavailable):H.validate_prediction_successor_parent(self.cont,self.effective(),claim,bad,new,'9'*64)
  bad=copy.deepcopy(new);bad['source_hashes']=old['source_hashes']
  with self.assertRaises(H.Unavailable):H.validate_prediction_successor_parent(self.cont,self.effective(),claim,old,bad,'9'*64)
 def test_parent_authority_metadata(self):
  claim,old,new=self.metadata()
  for mutation in ('identity','policy','source','closure'):
   c=copy.deepcopy(claim)
   if mutation=='identity':c['experiment_id']=H.RESERVED_ID
   if mutation=='policy':c['inputs'][H.SUCCESSOR_ROLE]['sha256']='0'*64
   if mutation=='source':c['experiment']['source_files'][H.PREFIX+'training.py']='0'*64
   if mutation=='closure':c['inputs']['source_closure']['sha256']='0'*64
   with self.subTest(mutation=mutation),self.assertRaises(H.Unavailable):H.validate_prediction_successor_parent(self.cont,self.effective(),c,old,new,'9'*64)
 def test_roles_and_missing_outcome_fail_closed(self):
  for roles in ({H.PREDICTION_ROLE:None},{H.PREDICTION_ROLE:None,H.SUCCESSOR_ROLE:None}):
   with self.assertRaises(F.Unavailable):F.require_compatibility_roles(roles)
  F.require_compatibility_roles({H.PREDICTION_ROLE:None,H.SUCCESSOR_ROLE:None,H.ROLE:None})
  with self.assertRaises(H.Unavailable):H.validate_prediction_recovery_record({},b'claim',b'terminal',b'checkpoint')
  # A refusal cannot be relabelled as a successful parent outcome.
  refusal=json.loads((CAP/'fixture_inputs/financial_wrapper_continuation_successor01/refusal.json').read_bytes())
  with self.assertRaises(H.Unavailable):H.validate_prediction_recovery_record(refusal,b'claim',b'terminal',b'checkpoint')
 def test_original_closure_routes_distinct(self):
  outer=self
  class Inputs:
   registered={H.PREDICTION_ROLE:None,H.SUCCESSOR_ROLE:None}
   def json(self,role):return outer.edge if role==H.PREDICTION_ROLE else outer.cont
   def raw(self,role):return role.encode()
  inputs=Inputs()
  self.assertEqual(PRE._dependency_closure_raw(inputs,self.original),b'prediction_continuation_closure')
  self.assertEqual(PRE._original_closure_raw(inputs,self.original),self.cont['original_closure_input'].encode())
 def test_evaluation_only_metadata_guard_changed(self):
  old=(CAP/H.PREFIX/'evaluation.py').read_text();new=(P/'evaluation.py').read_text()
  before="    if {k:v for k,v in old.items() if k!='source_commit'}!={k:v for k,v in provenance.items() if k!='source_commit'}:raise ValueError('recovery science differs')"
  after="    if 'prediction_source_successor' in run.admission.inputs:\n        from .operational_source_compatibility import require_prediction_recovery\n        require_prediction_recovery(run,old,provenance)\n    elif {k:v for k,v in old.items() if k!='source_commit'}!={k:v for k,v in provenance.items() if k!='source_commit'}:raise ValueError('recovery science differs')"
  self.assertEqual(new.replace(after,before),old)
  for name in ('evaluation.py','operational_source_compatibility.py','financial_wrapper_fixture.py','preclaim01.py'):ast.parse((P/name).read_text())
 def test_legacy_contract_still_valid(self):H.validate_contract(self.original,H.ORIGINAL_HELPER_SHA)
 def test_no_numerical_import(self):self.assertFalse({'torch','numpy','scipy','pandas'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
