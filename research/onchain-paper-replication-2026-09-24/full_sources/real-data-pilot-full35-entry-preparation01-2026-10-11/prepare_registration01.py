"""Root-only concrete35 registration draft; no admission, claim or launch."""
from pathlib import Path
import copy, hashlib, json, sys
ROOT=Path.cwd().resolve(); HERE=Path(__file__).resolve().parent; F=HERE.parent
OLD=F/'real-data-pilot-full34-entry-preparation01-2026-10-11'
T=F/'real-data-pilot-full35-binding-preparation01-2026-10-11'
BUDGET=F/'real-data-pilot-full35-cumulative-preparation01-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261011-35'
PRIOR='eth-paper-real-data-end-to-end-resource-20261011-34'
EXPECTED_HERE=F/'real-data-pilot-full35-entry-preparation01-2026-10-11'
assert len(sys.argv)==2, 'actual accepted106 review SHA required'
REVIEW_SHA=sys.argv[1]
assert len(REVIEW_SHA)==64 and all(c in '0123456789abcdef' for c in REVIEW_SHA)
def load(p): return json.loads(p.read_bytes())
def ref(p):
    b=p.read_bytes(); return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,x):
    with p.open('xb') as stream: stream.write((json.dumps(x,sort_keys=True,indent=2)+'\n').encode())
def main():
    assert HERE==EXPECTED_HERE, 'copy reviewed candidate into exact Root E35 before execution'
    review_path=F/'pilot35-cumulative-machine-review01-2026-10-11/EXTENSION106_REVIEW01.json'
    assert ref(review_path)['sha256']==REVIEW_SHA
    review=load(review_path)
    assert set(review)=={'schema_version','decision','extension_sha256','reviewer','scope'} and review['decision']=='accepted'
    extension=ref(BUDGET/'EXTENSION_PROPOSED106_01.json')
    assert extension['sha256']==review['extension_sha256']=='e0a1e3f89926094373e6c58022627e5861cda03064657e88a245129756810b9a'
    assert ref(BUDGET/'CUMULATIVE_ALLOCATION_PROPOSED106_01.json')['sha256']=='0320608cc703f7c8c2e4f1867bfc478a51efcd62ac70d318b409bd49c55815db'
    source_preparation=load(HERE/'SOURCE_PREPARATION01.json')
    assert source_preparation['source_anchor']=='53b8890630765d06f8a44e3e8fbaee1f4b00bdfb' and source_preparation['capacity_source_bodies']==423 and source_preparation['numerical_source_bodies']==200
    assert not (ROOT/'research_runs'/NAME).exists()
    bound=load(T/'BOUND01.json'); refs=load(T/'ALL_INPUT_REFS01.json')
    assert bound['status']=='BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED' and len(refs)==72
    assert len(load(T/'PUBLIC_INPUT_REFS_DRAFT01.json'))==71
    assert set(refs)==set(load(T/'PUBLIC_INPUT_REFS_DRAFT01.json'))|{'archive_transport'}
    assert bound['source_request']['private_parent']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-35-01'
    baseline=load(OLD/'gate01.json')['experiments'][PRIOR]['inputs']['matching_ordered_edge_scratch']
    assert ref(ROOT/baseline['path'])['sha256']==baseline['sha256']
    scratch=load(ROOT/baseline['path'])
    assert scratch['experiment']==PRIOR; scratch['experiment']=NAME
    kernel='tradingagents/research/onchain_replication/matching_annealing.py'
    assert scratch['installed_source']['path']==kernel
    assert ref(ROOT/kernel)['sha256']=='86ccc3a471827bdce7784145914240d04416d2cc0023e8acb77fb26ae473df57'
    scratch['installed_source']['sha256']=ref(ROOT/kernel)['sha256']
    save(HERE/'MATCHING_SCRATCH_RESERVATION01.json',scratch)
    pin=ref(HERE/'MATCHING_SCRATCH_RESERVATION01.json')
    refs['matching_ordered_edge_scratch']={k:pin[k] for k in ('path','sha256')}; refs['matching_ordered_edge_scratch']['dataset']='eth'
    gate=load(OLD/'gate01.json'); assert NAME not in gate['experiments']
    experiment=copy.deepcopy(gate['experiments'][PRIOR]); gate['experiments'][NAME]=experiment
    experiment['parent']=PRIOR; experiment['inputs']=refs; experiment['charter']=ref(BUDGET/'CHARTER01.md')
    experiment['question']='Measure full original seven-WHOLE-graph MCM and GAT/attention-LSTM real joint update/checkpoint with the exact reviewed installed two-attribute native edge backend and five fresh serializers, using unchanged scientific method, model training, compiled normalization, 60s lease and native limits.'
    evidence={
        'budget_review':ref(F/'pilot35-cumulative-machine-review01-2026-10-11/EXTENSION106_REVIEW01.json'),
        'capacity_observation':ref(HERE/'CAPACITY_DECLARATION_ROOT01.json'),
        'prior_outcome_review':ref(F/'pilot34-terminal-outcome-review01-2026-10-11/REVIEW01.json'),
        'prior_root_closure_review':ref(F/'pilot34-terminal-outcome-review01-2026-10-11/REVIEW01.json'),
        'prior_preservation_complete':ref(F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome27/FRESH_GIT_RECOVERY27.json'),
        'prior_recovery_review':ref(F/'pilot34-outcome-increment-return-review01-2026-10-11/REVIEW01.json'),
        'integration_review':ref(F/'pilot34-two-attribute-main-integration-review01-2026-10-11/REVIEW01.json'),
        'prior_outcome_locator_correction':ref(F/'pilot31-terminal-locator-correction01-2026-10-11/CORRECTION01.json'),
        'native_outcome_review':ref(F/'pilot34-native-owner03-outcome-review01-2026-10-11/REVIEW01.json'),
        'native_preservation_complete':ref(F/'real-data-pilot-full24-preparation-increment01-2026-10-09/nativeoutcome29/FRESH_GIT_RECOVERY29.json'),
        'native_recovery_review':ref(F/'pilot34-native03-increment-return-review01-2026-10-11/REVIEW01.json'),
        'native_installation':ref(F/'pilot34-two-attribute-main-adoption01-2026-10-11/INTEGRATION01.json'),
        'serializer_installation':ref(F/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json')}
    evidence['budget_review']={k:evidence['budget_review'][k] for k in ('path','sha256')}
    experiment['cumulative_budget_extension']={role:{k:pin[k] for k in ('path','sha256')} for role,pin in {'extension':ref(BUDGET/'EXTENSION_PROPOSED106_01.json'),'review':evidence['budget_review']}.items()}
    pins=experiment['source_files']; public_pins=load(HERE/'CAPACITY_SOURCE_MAP01.json')['source_files']
    assert len(public_pins)==423
    for name in ('EXTENSION_PROPOSED106_01.json','CUMULATIVE_ALLOCATION_PROPOSED106_01.json'):
        pin=ref(BUDGET/name);pins[pin['path']]=pin['sha256']
    pins.update(public_pins)
    for path,digest in pins.items(): assert ref(ROOT/path)['sha256']==digest,path
    for p in sorted(T.rglob('*')):
        if p.is_file(): pins[str(p.relative_to(ROOT))]=ref(p)['sha256']
    for p in sorted(HERE.iterdir()):
        if p.is_file(): pins[str(p.relative_to(ROOT))]=ref(p)['sha256']
    for p in evidence.values(): pins[p['path']]=p['sha256']
    public={'experiment':NAME,'all_input_roles':72,'source_pins':public_pins,'status':'DRAFT_NOT_RELEASED'}
    save(HERE/'PUBLIC_MANIFEST01.json',public)
    pins[str((HERE/'PUBLIC_MANIFEST01.json').relative_to(ROOT))]=ref(HERE/'PUBLIC_MANIFEST01.json')['sha256']
    save(HERE/'gate01.json',gate)
    binding={'schema_version':1,'identity':NAME,'status':'DRAFT_NOT_RELEASED','gate':ref(HERE/'gate01.json'),
             'core_manifest':ref(HERE/'CORE_MANIFEST01.json'),'public_manifest':ref(HERE/'PUBLIC_MANIFEST01.json'),
             'public_refs':ref(T/'PUBLIC_INPUT_REFS_DRAFT01.json'),'transport':bound['private_input']['archive_transport'],
             'transport_binding':ref(T/'BOUND01.json'),'preparation':ref(T/'PREPARED01.json'),
             'unbound_archive':ref(T/'public01/archive_policy.json'),'public_preparation':ref(T/'MANIFEST01.json'),
             'binding_readback':ref(T/'BINDING_CHECK01.json'),'input_refs':{role:{k:v[k] for k in ('path','sha256')} for role,v in refs.items()},
             'binding_review':None,**evidence}
    save(HERE/'BINDING_DRAFT01.json',binding)
    save(HERE/'REGISTRATION_DRAFT01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'gate':ref(HERE/'gate01.json'),'source_pins':len(pins),'input_roles':72,'claim':False,'admission':False})
    print(json.dumps({'status':'DRAFT_NOT_RELEASED','source_pins':len(pins),'input_roles':72,'claim':False}))
if __name__=='__main__':main()
