"""Changed metadata comparison only; no empirical input bodies or numerical imports."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[3];F=H.parent;j=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=j(H/'PREPARATION01.json');old=j(ROOT/r['inherited_evidence']['preparation']['path'])['builder03_result']['inputs'];new=r['builder03_result']['inputs']
def reverse(v):
 if type(v) is dict:return {reverse(k):reverse(x) for k,x in v.items()}
 if type(v) is list:return [reverse(x) for x in v]
 if type(v) is str:return v.replace('eth-paper-real-data-end-to-end-resource-20261009-27','eth-paper-real-data-end-to-end-resource-20261009-26').replace('real-eth-seven-graph-joint-update-resource27','real-eth-seven-graph-joint-update-resource26').replace('ethpilot-20261009-27','ethpilot-20261009-26')
 return v
for role,value in old.items():
 actual=reverse(new[role])
 if role=='pair_policy':
  assert set(actual['numerical_source']['files'])==set(value['numerical_source']['files']) and len(actual['numerical_source']['files'])==193
  assert {n for n in actual['numerical_source']['files'] if actual['numerical_source']['files'][n]!=value['numerical_source']['files'][n]}==set(r['source_changes'])
  actual['numerical_source']=value['numerical_source']
 if role in ('execution_job','producer_plan'):
  a=actual['payload']['representation_jobs']['original32'] if role=='execution_job' else actual['producers']['original32'];b=value['payload']['representation_jobs']['original32'] if role=='execution_job' else value['producers']['original32']
  for k in ('pair_execution','compact_execution','compact_archive_execution'):a['descriptor'][k]['policy_sha256']=b['descriptor'][k]['policy_sha256']
 assert actual==value,role
assert reverse(new['archive_policy'])==j(ROOT/r['inherited_evidence']['unbound_archive']['path'])
refs=j(H/'PUBLIC_INPUT_REFS01.json');assert len(refs)==64
for role in new:
 p=ROOT/refs[role]['path'];assert sha(p)==refs[role]['sha256'] and j(p)==new[role]
for side in (new['execution_job']['payload']['representation_jobs']['original32'],new['producer_plan']['producers']['original32']):
 for role,key in [('pair_policy','pair_execution'),('compact_policy','compact_execution'),('archive_policy','compact_archive_execution')]:assert side['descriptor'][key]['policy_sha256']==refs[role]['sha256']
public=j(H/'PUBLIC_MANIFEST01.json');assert public['source_anchor'] is None and r['source_anchor'] is None and len(r['pending_source_paths'])==6
assert len(public['source_pins'])==365 and all(sha(ROOT/n)==pin for n,pin in public['source_pins'].items())
assert all(public['source_pins'][n]==pin for n,pin in new['pair_policy']['numerical_source']['files'].items())
cap=j(H/'CAPACITY_DECLARATION01.json');prior=j(ROOT/r['inherited_evidence']['capacity_observation']['path'])
for k in ('directory_allocated_bound_bytes','new_allocated_growth_bytes','new_entries','new_logical_growth_bytes','non_directory_new_allocated_growth_bytes','other_writer_reserved_bytes','runtime_residuals_included','directory_and_other_writers_included','allocation_semantics'):assert cap[k]==prior[k]
assert cap['decision']=='DRAFT_NOT_REVIEWED' and cap['basis']['currentness_sample'] is cap['basis']['remote_storage_sample'] is None and cap['at']==prior['at']
assert new['archive_transport']['connection'] is None
report=dict(status='PASS_DRAFT_METADATA_ONLY',numerical_roster=193,public_source_roster=365,changed_sources=sorted(r['source_changes']),input_roles=64,public_documents=12,identity_inverse_except_explicit_numerical_pins_and_descriptors=True,scientific_and_native_storage_config_unchanged=True,capacity_numbers_unchanged=True,source_anchor_pending=True,private_connection_unbound=True,no_claim=True)
(H/'CHECK01.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
