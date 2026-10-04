import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-cumulative20-preparation01-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
extsha=sha(A/'extension20.DRAFT.json');allocsha=sha(A/'allocation20.DRAFT.json');assert extsha=='07100b23f9a8c2dfcae98a8647f9f1eeb019f4093192cd4b2576c6a13bf9840e' and allocsha=='461df69895a0a5e70b23882c759790a4c000eb33d1662629cacd322b7d3b0116'
reconstruction=json.loads((H/'RECONSTRUCTION01.json').read_text())
for row in reconstruction['claims']:
 assert sha(S/'research_runs'/row['experiment']/'claim.json')==row['claim_sha256']
 assert sha(S/'research_runs'/row['experiment']/'failed.json')==row['terminal_sha256']
assert sha(S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json')=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c'
review={'schema_version':1,'decision':'accepted','extension_sha256':extsha,'reviewer':'Independent research reviewer /root/storage_watch_review','scope':'Exact extension20/allocation461df698 prospective same-family accounting only: base18/prior0, three genuine FAILED claims remain spent,17 original phase contracts pending, cumulative20 minimal with no refund/transfer/paper credit/cap increase. Actual allowance remains19 until Root prospective committed adoption. No source/policy/registration/recovery/native/numerical release approval. Stale ancillary ORIGINAL_PHASES18_CURRENT01 status/dependency sidecar is not accepted as current release DAG and requires additive correction before use. All failed-scope recovery, exact source/policy/gate/caller, fresh namespace/runtime/resource and subsequent outcome gates remain mandatory.'}
(H/'REVIEW_ACCEPTANCE01.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
machine={'status':'ACCEPTED_EXACT_PROSPECTIVE_BUDGET_SUBSTANCE_ONLY_NO_ADOPTION','extension_sha256':extsha,'allocation_sha256':allocsha,'actual_base':18,'actual_prior':0,'actual_highest':19,'actual_spent_failed':3,'original_phases':18,'fulfilled_original_phases':1,'remaining_original_phases':17,'existing_remaining':16,'proposed20_remaining':17,'source_metadata_assertions':293,'negative_validator_controls':8,'paper_records_rehashed':36,'paper_complete':27,'paper_failed':9,'paper_highest_current':64,'guard03_review_declared_members_authenticated':358,'actual_source_or_recovery_release':False,'actual_budget_adoption':False,'full_proposed20_admission_executed':False,'genuine_review_receipt_sha256':sha(H/'REVIEW_ACCEPTANCE01.json'),'report_sha256':sha(H/'REPORT01.md'),'findings':[{'priority':'P2','file':str(A/'ORIGINAL_PHASES18_CURRENT01.json'),'line':18,'also_lines':[44,45,46],'issue':'Stale current reference status and required_actual reference dependency points at permanentlyFAILED original100 identity.','affects':'ancillary current-DAG use; exact extension/allocation budget substance accepted'}],'untested':['Financial/numerical correctness and full capacity','Prospective source policy and native admission','Complete100 success and future dependency readiness','Actual failed-scope external/fresh recovery']}
(H/'MACHINE01.json').write_text(json.dumps(machine,indent=2,sort_keys=True)+'\n')
rows=[]
for p in sorted(H.rglob('*')):
 rel=str(p.relative_to(H))
 if rel in ('MANIFEST01.json','FREEZE01.out','FREEZE01.err'):continue
 s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(p),links=s.st_nlink)
 else:raise AssertionError('unexpected type')
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'manifest_self_excluded':True,'excluded_execution_streams':['FREEZE01.out','FREEZE01.err'],'members':rows},indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':machine['status'],'manifest_sha256':sha(H/'MANIFEST01.json'),'machine_sha256':sha(H/'MACHINE01.json'),'report_sha256':sha(H/'REPORT01.md'),'review_acceptance_sha256':sha(H/'REVIEW_ACCEPTANCE01.json'),'members':len(rows)}))
