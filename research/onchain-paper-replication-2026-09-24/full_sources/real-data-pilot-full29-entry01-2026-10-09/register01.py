"""Concrete29 registration draft; no admission, claim or model execution."""
import copy
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path.cwd().resolve()
HERE=Path(__file__).resolve().parent
F=HERE.parent
PREVIOUS=F/'real-data-pilot-full28-entry01-2026-10-09'
PUBLIC=F/'real-data-pilot-full29-input-draft01-2026-10-09'
T=F/'real-data-pilot-full29-transport-binding01-2026-10-09'
OLD='eth-paper-real-data-end-to-end-resource-20261009-28'
NAME='eth-paper-real-data-end-to-end-resource-20261009-29'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
def save(p,x):
    with p.open('xb') as out:out.write((json.dumps(x,sort_keys=True,indent=2)+'\n').encode())

assert not (ROOT/'research_runs'/NAME).exists()
gate=load(PREVIOUS/'gate01.json')
assert NAME not in gate['experiments']
old=gate['experiments'][OLD]
experiment=copy.deepcopy(old)
experiment['cells']=['real-eth-seven-graph-joint-update-resource29']
experiment['parent']=OLD
experiment['question']='Complete preserved seven WHOLE Ethereum graph MCMs and original GAT-attentionLSTM real joint update; measure throughput, resources and training with genuine offload authority polling, fixed exact adaptive edge cache and bounded geometry/Binding timing. No diagnostic stop or method/cap change.'
experiment['inputs']=load(T/'ALL_INPUT_REFS02.json')
experiment['charter']=ref(HERE/'CHARTER01.md')
budget=F/'real-data-pilot-full29-allocation-review01-2026-10-09/EXTENSION100_REVIEW01.json'
experiment['cumulative_budget_extension']={'extension':ref(HERE/'EXTENSION_PROPOSED100_01.json'),'review':ref(budget)}
pins=copy.deepcopy(load(PUBLIC/'SOURCE_MAP01.json')['source_files'])
additions=[HERE/'CHARTER01.md',HERE/'CUMULATIVE_ALLOCATION_PROPOSED100_01.json',HERE/'EXTENSION_PROPOSED100_01.json',budget,
 HERE/'preflight29_01.py',HERE/'root_io29_01.py',HERE/'prepare_entry01.py',HERE/'register01.py',HERE/'PUBLIC_MANIFEST01.json',HERE/'CORE_MANIFEST01.json',HERE/'CAPACITY_DECLARATION_ROOT01.json',
 PUBLIC/'prepare02.py',PUBLIC/'PREPARATION01.json',PUBLIC/'MANIFEST01.json',PUBLIC/'SOURCE_MAP01.json',PUBLIC/'PUBLIC_INPUT_REFS01.json',PUBLIC/'CARDINALITY01.json',PUBLIC/'MATCHING_SCRATCH_RESERVATION01.json',
 T/'bind_actual02.py',T/'binder02/bind01.py',T/'binder02/DEPENDENCIES01.json',T/'BINDER_DEPENDENCY_CORRECTION01.json',T/'PREPARED02.json',T/'REQUEST02.json',T/'BOUND02.json',T/'ALL_INPUT_REFS02.json',T/'UNBOUND_ARCHIVE02.json',T/'BINDING_READBACK02.json',
 F/'pilot-full28-to-successor-root-integration01-2026-10-09/INSTALL01.json',F/'pilot-full28-to-successor-integration-review01-2026-10-09/INTEGRATION_REVIEW01.json',
 F/'matching-adaptive-measurement-stack-review02-2026-10-09/SOURCE_REVIEW01.json',F/'pilot-grouped-offload-lease-poll-review01-2026-10-09/SOURCE_REVIEW01.json',
 F/'real-data-pilot-full28-outcome-review01-2026-10-09/OUTCOME_REVIEW01.json',F/'real-data-pilot-full28-outcome-review01-2026-10-09/RETURNED_GROUP_REVIEW01.json',
 F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome13/FRESH_GIT_RECOVERY13.json',F/'pilot-full28-outcome-increment-tools-review01-2026-10-09/returned13/RECOVERY_REVIEW01.json']
for p in additions:pins[str(p.relative_to(ROOT))]=sha(p)
for name,pin in pins.items():assert sha(ROOT/name)==pin
experiment['source_files']=pins
gate['experiments'][NAME]=experiment
save(HERE/'gate01.json',gate)

binding=copy.deepcopy(load(PREVIOUS/'BINDING01.json'))
binding.update(identity=NAME, gate=ref(HERE/'gate01.json'),
 core_manifest=ref(HERE/'CORE_MANIFEST01.json'),public_manifest=ref(HERE/'PUBLIC_MANIFEST01.json'),
 public_refs=ref(PUBLIC/'PUBLIC_INPUT_REFS01.json'),capacity_observation=ref(HERE/'CAPACITY_DECLARATION_ROOT01.json'),
 transport=next(iter(load(T/'BOUND02.json')['private_input'].values())),transport_binding=ref(T/'BOUND02.json'),
 preparation=ref(T/'PREPARED02.json'),unbound_archive=ref(T/'UNBOUND_ARCHIVE02.json'),budget_review=ref(budget),
 prior_outcome_review=ref(F/'real-data-pilot-full28-outcome-review01-2026-10-09/OUTCOME_REVIEW01.json'),
 prior_preservation_complete=ref(F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome13/FRESH_GIT_RECOVERY13.json'),
 prior_recovery_review=ref(F/'pilot-full28-outcome-increment-tools-review01-2026-10-09/returned13/RECOVERY_REVIEW01.json'))
binding['input_refs']={role:{k:info[k] for k in ('path','sha256')} for role,info in experiment['inputs'].items()}
binding['binding_review']=None
binding['integration_review']=ref(F/'pilot-full28-to-successor-integration-review01-2026-10-09/INTEGRATION_REVIEW01.json')
binding['measurement_stack_review']=ref(F/'matching-adaptive-measurement-stack-review02-2026-10-09/SOURCE_REVIEW01.json')
binding['offload_poll_review']=ref(F/'pilot-grouped-offload-lease-poll-review01-2026-10-09/SOURCE_REVIEW01.json')
binding['binder_dependency_correction']=ref(T/'BINDER_DEPENDENCY_CORRECTION01.json')
binding['binding_readback']=ref(T/'BINDING_READBACK02.json')
binding['public_preparation']=ref(PUBLIC/'PREPARATION01.json')
save(HERE/'BINDING_DRAFT01.json',binding)
save(HERE/'REGISTRATION_DRAFT01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'DRAFT_NOT_RELEASED','identity':NAME,'gate':ref(HERE/'gate01.json'),
 'source_pins':len(pins),'input_roles':len(experiment['inputs']),'binding_review_missing':True,
 'prior_outcome_and_actual_recovery':binding['prior_recovery_review'],
 'qualification':'Complete finite actual-source29 registration draft and genuine actual bound64 inputs. Independent exact entry/source review, committed metadata admission, current namespace/resource checks and final public increment recovery remain required. Budget100 reviewed but not adopted.'})
print(json.dumps({'status':'DRAFT_NOT_RELEASED','source_pins':len(pins),'input_roles':len(experiment['inputs'])}))
