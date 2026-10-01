"""Static capacity-reservation arithmetic; no measurements or numerical execution."""
import ast
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
inputs=HERE/'inputs02.json'
journal=HERE.parent/'pair-owner-route-2026-09-30/journal.py'
kernel=HERE.parent/'mcm-array-kernel-2026-10-01/kernel.py'

def assess():
    source=journal.read_text();tree=ast.parse(source)
    values=[n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LIMIT' for t in n.targets) and isinstance(n.value,ast.Constant)]
    assert values==[65536]
    # These exact branches charge reserve/publish envelopes and the new session owner.
    assert "result['reserved_bytes'] += record['declared_artifact_bytes'] + 2*LIMIT" in source
    assert "result['reserved_bytes'] += LIMIT  # one PairSession owner manifest" in source
    scope=json.loads(inputs.read_text());pairs=scope['totals']['mcm_pair_evaluations']
    return {'schema_version':1,'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (inputs,journal,kernel)},
        'mcm_cell_count':pairs,'journal_limit_bytes':values[0],'minimum_constant_allowance_per_new_pair':3*values[0],
        'constant_allowance_for_all_mcm_cells_if_current_new_pair_route_is_used':pairs*3*values[0],
        'minimum_reserve_publish_events_if_current_new_pair_route_is_used':pairs*2,
        'qualification':'Conditional static quota-reservation arithmetic, NOT actual bytes written, disk capacity required, peak RAM, observed runtime or a new empirical result. Excludes positive declared artifact bytes, additional pair checkpoints, dictionary work and all other workflow outputs.',
        'next_requirement':'Replace or prospectively adapt the per-pair persistence/accounting route with bounded batch/checkpoint ownership and preserved results; verify exact numerical equivalence and failure lineage. Merely increasing a quota or lowering the motif/node denominator cannot establish feasibility.'}
if __name__=='__main__':
    result=assess()
    with (HERE/'journal-scaling01.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
