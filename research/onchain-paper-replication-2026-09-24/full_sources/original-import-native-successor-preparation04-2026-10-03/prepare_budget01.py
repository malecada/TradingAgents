"""Prepare a finite cumulative engineering amendment; no claim or release."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;FULL=HERE.parent
OLD=FULL/'original-import-native-release-2026-10-03/capsule01'
PARENT='original-import-native-success-20261003-01'
FIRST='original-import-native-success-20261003-02'
SECOND='original-import-native-publication-failure-20261003-02'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def write(name,value):
    raw=encode(value)
    with (HERE/name).open('xb') as stream:stream.write(raw)
    return sha(raw)
def main():
    run=OLD/'research_runs'/PARENT;claim_raw=(run/'claim.json').read_bytes();terminal_raw=(run/'failed.json').read_bytes()
    claim=json.loads(claim_raw);terminal=json.loads(terminal_raw)
    assert claim['experiment_id']==terminal['experiment_id']==PARENT and terminal['status']=='failed'
    assert terminal['claim_sha256']==sha(claim_raw) and not (run/'complete.json').exists()
    assert terminal['reason']=='ValueError: compact metadata bound'
    assert not (OLD/'research_runs'/'original-import-native-publication-failure-20261003-01').exists()
    allocation={'schema_version':1,'program_id':claim['program_id'],'mechanism_id':claim['family']['mechanism_id'],
        'base_attempt_budget':2,'prior_attempts':0,'closed_before':1,'proposed_cumulative_ceiling':3,
        'retained_closed_attempts':[{'identity':PARENT,'status':'failed','claim_sha256':sha(claim_raw),'terminal_sha256':sha(terminal_raw),'disposition':'permanently spent; never rerun'}],
        'new_attempts':[{'identity':FIRST,'case':'success','maximum_claims':1,'depends_on':'Exact accepted source/metadata/cleanup and original failed raw closure/recovery, reviewed exact capsule gate/runtime/control release and fresh baseline'},
            {'identity':SECOND,'case':'second_target_publication_failure','maximum_claims':1,'depends_on':'First successor complete raw closure/review/verified external recovery and fresh baseline; never launch on unchanged blocker'}],
        'unlaunched_superseded':[{'identity':'original-import-native-publication-failure-20261003-01','status':'unlaunched','disposition':'withdrawn before attempt because source preflight is known to fail; no terminal receipt, claim, refund or numerical result is fabricated'}],
        'case_denominators':{'success':{'targets':2,'scalar_reference_comparisons':160},'second_target_publication_failure':{'first_target_scalar_reference_comparisons':64,'second_target_numerical_cells':96,'second_target_publication_and_scalar_reference':'expected unavailable; classify genuine retained stage separately'}},
        'guard':{'memory_max_bytes':3221225472,'memory_high_bytes':3221225472,'memory_swap_max_bytes':0,'host_reserve_bytes':3221225472,'startup_available_bytes':6442450944,'file_size_bytes':4194304,'native_wall_seconds':1800,'outer_active_seconds':1840,'disk_floor_bytes':10737418240,'whole_capsule_sampled_stop_bytes':1073741824},
        'remaining_refusal_obligations':{'classes':16,'variants':27,'preclaim':4,'maximum_claims':23,'fresh_owners':17,'journal_groups':19,'status':'separate unexecuted suite; two primary cases do not discharge it'},
        'paper_accounting_unchanged':{'closed':36,'complete':27,'failed':9,'highest_adopted_ceiling':64,'budget65_authority':False,'financial_fits_pending':1420},
        'qualification':'Engineering amendment only; base family object and every closed claim remain byte-exact. No budget refund/category transfer, new paper-family allowance, scientific representation_complete, fullgraph capacity, numerical agreement or financial fitting permission follows. Complete typed transport/fullhistory/comparisons remain required.'}
    allocation_pin=write('successor-allocation01.json',allocation)
    extension={'schema_version':1,'program_id':claim['program_id'],'base_family':claim['family'],'cumulative_ceiling':3,
        'consumed_before':1,'initial_experiment':FIRST,'allocation':{'path':'fixture_budget/successor-allocation01.json','sha256':allocation_pin},
        'claims':[{'experiment':PARENT,'claim_sha256':sha(claim_raw),'terminal_status':'failed','terminal_sha256':sha(terminal_raw)}],
        'reason':'The first genuine dictionary import completed but compact MCM start metadata exceeded the fixed8192B cap before any MCM stage. A selected source-reference correction and independently reviewed failure cleanup are needed to complete the unchanged two primary engineering cases. Preserve one spent failed attempt and add only the one cumulative slot necessary for two fresh fixed identities; no paper budget or sampling is moved.'}
    extension_pin=write('cumulative-extension01.json',extension)
    proposal={'status':'frozen_proposal_pending_independent_budget_review_and_exact_execution_release','extension_sha256':extension_pin,'allocation_sha256':allocation_pin,'consumed_before':1,'base_budget':2,'proposed_ceiling':3,'fresh_identities':[FIRST,SECOND],'review_file_future':'fixture_budget/cumulative-extension-review01.json','actual_claims_created':0,'qualification':'Preparation metadata only, not an accepted review or registration. Genuine historical claim/terminal source is the closed original capsule; copying its unchanged claim history into a new owned capsule must be independently verified with original Git source before admission.'}
    print(json.dumps(proposal,sort_keys=True))
    write('BUDGET_PROPOSAL01.json',proposal)
if __name__=='__main__':main()
