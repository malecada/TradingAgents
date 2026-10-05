"""Focused metadata preparation checks; no simulated research authority."""
import json
from emit01 import build,raw,GATE
x=build();assert raw(x)==raw(build())
g=json.loads(x['gate_candidate_text']);old=json.loads(GATE.read_bytes());identity=x['identity'];case=g['experiments'][identity]
assert set(g['experiments'])==set(old['experiments'])|{identity}
# Exact textual inverse proves preservation of whitespace and every old case byte.
addition=','+json.dumps(identity)+':'+raw(case).decode().rstrip()
assert x['gate_candidate_text'].count(addition)==1
assert x['gate_candidate_text'].replace(addition,'',1).encode()==GATE.read_bytes()
assert len(case['inputs'])==len(set(x['required_roles']))==29
assert case['parent']==x['parent_binding']['dependency_parent']
assert all(case[k]==old['experiments'][case['parent']][k] for k in ('charter','runtime_hashes','cumulative_budget_extension','windows','family','cells','outputs'))
assert g['families']==old['families']
missing=[role for role,v in case['inputs'].items() if v['sha256'] is None]
assert set(missing)=={'prediction_source_successor_review','prediction_source_successor_recovery','prediction_parent_recovery'}
assert x['recovery_bridge_unaccepted_template']['decision'] is None
assert x['parent_binding']['launch_authority'] is False and x['byte_estimate']['complete_reader_estimate'] is None
print('PASS: deterministic emission; exact literal gate inverse/historical preservation; 29-role genuine-parent topology; fixed protocol/runtime/budget; three missing proofs remain unadmittable. No numerical imports or authority objects.')
print(json.dumps({k:v for k,v in x['byte_estimate'].items() if not isinstance(v,dict)},sort_keys=True))
