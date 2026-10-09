"""Materialize one unused successor from actual accepted28 and public29 metadata.

No numerical execution, claim, provider connection or opaque body inspection.
The accepted binder is called separately after this draft is materialized.
"""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
OLD = 'eth-paper-real-data-end-to-end-resource-20261009-28'
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-29'
PREVIOUS = F/'real-data-pilot-full28-entry01-2026-10-09'
PUBLIC = F/'real-data-pilot-full29-input-draft01-2026-10-09'
TRANSPORT = F/'real-data-pilot-full29-transport-binding01-2026-10-09'

def load(path): return json.loads(path.read_bytes())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path): return {'path':str(path.relative_to(ROOT)), 'sha256':digest(path), 'bytes':path.stat().st_size}
def save(path, value):
    with path.open('xb') as out:
        out.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
def move(value):
    if type(value) is dict:return {k:move(v) for k,v in value.items()}
    if type(value) is list:return [move(v) for v in value]
    if type(value) is str:return value.replace(OLD,NAME).replace('resource28','resource29')
    return value

assert not (ROOT/'research_runs'/NAME).exists()
assert not (ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME).exists()
anchor = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
source_map=load(PUBLIC/'SOURCE_MAP01.json')
assert anchor == source_map['source_anchor']
pins=source_map['source_files']
assert len(pins)==419
for name,pin in pins.items():assert digest(ROOT/name)==pin
public_refs=load(PUBLIC/'PUBLIC_INPUT_REFS01.json')
assert len(public_refs)==64
save(HERE/'PUBLIC_MANIFEST01.json', {
    'status':'DRAFT_NOT_RELEASED','experiment':NAME,'all_input_roles':64,
    'public_inputs':load(PUBLIC/'PREPARATION01.json')['public_inputs'],
    'source_anchor':anchor,'source_pins':pins,
    'source_map':ref(PUBLIC/'SOURCE_MAP01.json'),
    'preparation':ref(PUBLIC/'PREPARATION01.json'),
    'qualification':'Actual accepted installed source union and concrete29 public metadata; private transport, exact release and empirical admission remain separate.'})

# Preserve the complete finite physical growth formula. Selected metadata fits
# the original8192-byte summaries; adaptive scratch replaces an existing term.
capacity=move(load(PREVIOUS/'CAPACITY_DECLARATION_ROOT01.json'))
capacity.update(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                source_anchor=anchor, source_body_pins=pins)
capacity['basis']['prior_declaration']=ref(PREVIOUS/'CAPACITY_DECLARATION_ROOT01.json')
capacity['basis']['public_source_manifest']=ref(HERE/'PUBLIC_MANIFEST01.json')
capacity['basis']['source_adoption']=ref(F/'pilot-full28-to-successor-root-integration01-2026-10-09/INSTALL01.json')
capacity['qualification']+=' Successor29 keeps all growth terms and native/writable caps. Selected geometry1536 and binding timing640 remain inside the existing8192-byte summary cap; aggregate831971328 is not assigned to every stage. Adaptive explicit bound229376 is inside existing262144 scratch. Actual failed28 stays in the fresh union baseline. No current resource observation, remote reservation, whole capacity or real speedup is asserted.'
save(HERE/'CAPACITY_DECLARATION_ROOT01.json',capacity)

core=copy.deepcopy(load(PREVIOUS/'CORE_MANIFEST01.json'))
for role in core['inputs']:core['inputs'][role]=ref(ROOT/public_refs[role]['path'])
for name in core['source']:core['source'][name]=digest(ROOT/name)
core['scope']='Four concrete29 core bodies derived from preserved full28; only mcm optional adaptive cache/geometry/binding timing selections changed. Bound transport, final gate and exact independent release remain separate.'
save(HERE/'CORE_MANIFEST01.json',core)

# Preserve RootIO behavior; change only the fixed preflight module identifier.
rootio=(PREVIOUS/'root_io28_01.py').read_text()
with (HERE/'root_io29_01.py').open('x') as out:out.write(rootio.replace('from preflight28_01 import check','from preflight29_01 import check'))
preflight=(PREVIOUS/'preflight28_01.py').read_text().replace(OLD,NAME)
preflight=preflight.replace('admission.effective_attempt_budget!=99','admission.effective_attempt_budget!=100').replace("'effective_attempt_budget':99", "'effective_attempt_budget':100")
needle="    schedule=compact['stage_policy']['schedule']\n"
addition="""    execution=mcm['batched']['execution']
    need(execution.get('edge_cache_policy')=={'format':'adaptive-lazy-edge-cache-v1','max_edge_products':16384,'chunk_entries':256,'max_scratch_bytes':262144},'fixed adaptive cache policy differs')
    need(execution.get('geometry')=={'format':'provisional-pair-geometry-v1','max_body_bytes':1536},'fixed geometry policy differs')
    need(execution.get('binding_timing')=={'format':'binding-lease-phases-v1','max_body_bytes':640},'fixed binding timing policy differs')
    need(execution['max_summary_bytes']==144998400,'original per-stage summary cap differs')
"""
assert preflight.count(needle)==1
preflight=preflight.replace(needle,addition+needle)
with (HERE/'preflight29_01.py').open('x') as out:out.write(preflight)

TRANSPORT.mkdir(exist_ok=False)
binder=(F/'real-data-pilot-full28-transport-binding01-2026-10-09/bind_actual01.py').read_text()
binder=binder.replace('real-data-pilot-full28-input-draft01-2026-10-09','real-data-pilot-full29-input-draft01-2026-10-09').replace(OLD,NAME).replace('pilot-transport-20261009-28-01','pilot-transport-20261009-29-01')
binder=binder.replace("PUBLIC / 'PUBLIC_MANIFEST02.json'","PUBLIC / 'PREPARATION01.json'").replace("PUBLIC/'PUBLIC_MANIFEST02.json'","PUBLIC/'PREPARATION01.json'").replace("PUBLIC/'PUBLIC_INPUT_REFS02.json'","PUBLIC/'PUBLIC_INPUT_REFS01.json'")
with (TRANSPORT/'bind_actual01.py').open('x') as out:out.write(binder)
save(HERE/'ENTRY_PREPARATION01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,
 'source_anchor':anchor,'baseline':ref(PREVIOUS/'BINDING01.json'),
 'public_preparation':ref(PUBLIC/'PREPARATION01.json'),
 'sources':{str(p.relative_to(ROOT)):digest(p) for p in (HERE/'preflight29_01.py',HERE/'root_io29_01.py',TRANSPORT/'bind_actual01.py')},
 'source_pins':419,'input_roles':64,
 'qualification':'Actual successor caller/public manifests materialized. RootIO unchanged except fixed preflight module; preflight fixed identity/allowance plus strict three selected controls and original summary cap. No admission, claim, reservation or native job.'})
print(json.dumps({'identity':NAME,'source_pins':419,'status':'DRAFT_NOT_RELEASED'}))
