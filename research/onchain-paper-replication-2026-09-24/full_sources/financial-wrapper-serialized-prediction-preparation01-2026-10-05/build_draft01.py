"""Print prospective metadata only; never writes, creates admission, or infers completion."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PARENT='financial-wrapper-classification-eager-continue100-serialized-storage-successor-20261005-01'
PREDICTION='financial-wrapper-classification-eager-predict-serialized-storage-successor-20261005-01'
SOURCE='6b07c0f841e7d38102814aabb335751fd71fb7f7'
CLAIM_SHA='2dd47f07f3ad3e250ff2e668a8e1a62d88f450635c056c2391cba0d27f9064ea'
POLICY_SHA='f5b6521770ba21dc33c42816093e97739dca51b3abc7e53c4b5c48630fe9ec28'
CLOSURE_SHA='16f05d94c9419aad6072a68da78eb0a305e87c3757e8517aae7da46a10a5b610'
PREFIX='tradingagents/research/onchain_replication/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pinned(path,pin):
 raw=path.read_bytes()
 if sha(raw)!=pin:raise ValueError('actual parent metadata pin differs: '+str(path))
 return json.loads(raw)
def build():
 claim_path=CAP/'research_runs'/PARENT/'claim.json';claim=pinned(claim_path,CLAIM_SHA)
 if claim['experiment_id']!=PARENT or claim['source']!=SOURCE or claim['design_source']!=SOURCE:raise ValueError('actual continued parent identity/source differs')
 policy_path=CAP/claim['inputs']['continuation_source_successor']['path'];policy=pinned(policy_path,POLICY_SHA)
 closure_path=CAP/claim['inputs']['source_closure']['path'];closure=pinned(closure_path,CLOSURE_SHA)
 if closure['installed']!=policy['installed']:raise ValueError('actual parent closure/edge map differs')
 after=dict(policy['installed'])
 for name in ('operational_source_compatibility.py','financial_wrapper_fixture.py','evaluation.py'):after[PREFIX+name]=sha((HERE/name).read_bytes())
 delta=[{'path':k,'old_sha256':policy['installed'][k],'new_sha256':after[k]} for k in sorted(after) if after[k]!=policy['installed'][k]]
 if len(delta)!=3:raise ValueError('exact three prediction metadata source replacements required')
 return {'schema_version':1,'status':'UNAVAILABLE_WAITING_FOR_GENUINE_COMPLETE_REVIEW_AND_FULL_RECOVERY','parent':PARENT,'prediction_identity':PREDICTION,'actual_parent_source':SOURCE,'actual_parent_claim':{'path':str(claim_path),'sha256':CLAIM_SHA},'actual_parent_policy':{'path':str(policy_path),'sha256':POLICY_SHA},'actual_parent_closure':{'path':str(closure_path),'sha256':CLOSURE_SHA},'prediction_edge_candidate':{'schema_version':1,'kind':'same-family-prediction-source-successor-v1','continuation_policy_sha256':POLICY_SHA,'consumer':{'experiment':PREDICTION,'cell_id':policy['consumer']['cell_id']},'installed':after,'allowed_delta':delta,'continuation_closure_input':'prediction_continuation_closure','parent_recovery_input':'prediction_parent_recovery'},'unresolved':{'complete_terminal':None,'fit_completion':None,'checkpoint_manifest':None,'checkpoint_members':None,'original_checkpoint_provenance':None,'independent_outcome_review':None,'full_external_recovery':None,'prediction_policy_review':None,'prediction_policy_recovery':None,'actual_prediction_source_commit':None,'registration':None,'final_parent_release':None},'qualification':'draft source/input preparation only; actual claim is not completion or prediction authority'}
if __name__=='__main__':print(json.dumps(build(),sort_keys=True,indent=2))
