"""Root-only concrete31 registration draft; no admission, claim or launch."""
from pathlib import Path
import copy, hashlib, json
ROOT=Path.cwd().resolve(); HERE=Path(__file__).resolve().parent; F=HERE.parent
OLD=F/'real-data-pilot-full31-entry-preparation02-2026-10-11'
T=F/'real-data-pilot-full32-binding-preparation01-2026-10-11'
BUDGET=F/'real-data-pilot-full32-cumulative-preparation01-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261011-32'
PRIOR='eth-paper-real-data-end-to-end-resource-20261011-31'
def load(p): return json.loads(p.read_bytes())
def ref(p):
    b=p.read_bytes(); return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,x):
    with p.open('xb') as stream: stream.write((json.dumps(x,sort_keys=True,indent=2)+'\n').encode())
def main():
    assert not (ROOT/'research_runs'/NAME).exists()
    bound=load(T/'BOUND01.json'); refs=load(T/'ALL_INPUT_REFS01.json')
    assert bound['status']=='BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED' and len(refs)==67
    assert bound['source_request']['private_parent']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-32-01'
    baseline=load(OLD/'gate03.json')['experiments'][PRIOR]['inputs']['matching_ordered_edge_scratch']
    assert ref(ROOT/baseline['path'])['sha256']==baseline['sha256']
    scratch=load(ROOT/baseline['path'])
    assert scratch['experiment']==PRIOR; scratch['experiment']=NAME
    save(HERE/'MATCHING_SCRATCH_RESERVATION01.json',scratch)
    pin=ref(HERE/'MATCHING_SCRATCH_RESERVATION01.json')
    refs['matching_ordered_edge_scratch']={k:pin[k] for k in ('path','sha256')}; refs['matching_ordered_edge_scratch']['dataset']='eth'
    gate=load(OLD/'gate03.json'); assert NAME not in gate['experiments']
    experiment=copy.deepcopy(gate['experiments'][PRIOR]); gate['experiments'][NAME]=experiment
    experiment['parent']=PRIOR; experiment['inputs']=refs; experiment['charter']=ref(BUDGET/'CHARTER01.md')
    experiment['question']='Measure full original seven-WHOLE-graph MCM and GAT/attention-LSTM real joint update/checkpoint after exact accepted selected compiled helper preactivation loading, using unchanged scientific method, compiled route and native limits.'
    evidence={
        'budget_review':ref(F/'pilot32-cumulative-machine-review01-2026-10-11/EXTENSION103_REVIEW01.json'),
        'capacity_observation':ref(HERE/'CAPACITY_DECLARATION_ROOT01.json'),
        'prior_outcome_review':ref(F/'pilot31-terminal-outcome-review01-2026-10-11/REVIEW01.json'),
        'prior_root_closure_review':ref(F/'pilot31-terminal-outcome-review01-2026-10-11/REVIEW01.json'),
        'prior_preservation_complete':ref(F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome21/FRESH_GIT_RECOVERY21.json'),
        'prior_recovery_review':ref(F/'pilot31-outcome-increment-return-review01-2026-10-11/REVIEW01.json'),
        'integration_review':ref(F/'pilot31-loaded-identity-correction-review01-2026-10-11/REVIEW01.json'),
        'prior_outcome_locator_correction':ref(F/'pilot31-terminal-locator-correction01-2026-10-11/CORRECTION01.json')}
    experiment['cumulative_budget_extension']={role:{k:pin[k] for k in ('path','sha256')} for role,pin in {'extension':ref(BUDGET/'EXTENSION_PROPOSED103_01.json'),'review':evidence['budget_review']}.items()}
    pins=experiment['source_files']; public_pins=load(HERE/'CAPACITY_SOURCE_MAP01.json')['source_files']
    for name in ('EXTENSION_PROPOSED103_01.json','CUMULATIVE_ALLOCATION_PROPOSED103_01.json'):
        pin=ref(BUDGET/name);pins[pin['path']]=pin['sha256']
    pins.update(public_pins)
    for path,digest in pins.items(): assert ref(ROOT/path)['sha256']==digest,path
    for p in sorted(T.rglob('*')):
        if p.is_file(): pins[str(p.relative_to(ROOT))]=ref(p)['sha256']
    for p in sorted(HERE.iterdir()):
        if p.is_file(): pins[str(p.relative_to(ROOT))]=ref(p)['sha256']
    for p in evidence.values(): pins[p['path']]=p['sha256']
    public={'experiment':NAME,'all_input_roles':67,'source_pins':public_pins,'status':'DRAFT_NOT_RELEASED'}
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
    save(HERE/'REGISTRATION_DRAFT01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'gate':ref(HERE/'gate01.json'),'source_pins':len(pins),'input_roles':67,'claim':False,'admission':False})
    print(json.dumps({'status':'DRAFT_NOT_RELEASED','source_pins':len(pins),'input_roles':67,'claim':False}))
if __name__=='__main__':main()
