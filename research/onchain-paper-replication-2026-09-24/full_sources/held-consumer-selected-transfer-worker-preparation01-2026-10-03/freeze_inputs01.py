import ast,hashlib,json
from pathlib import Path
P=Path(__file__).parent;ROOT=P.parents[3];FS=P.parent
CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-04/source')
def digest(b):return hashlib.sha256(b).hexdigest()
def write(name,v):(P/name).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
base=json.loads((FS/'held-consumer-root-source-composition04-2026-10-03/SOURCE_COMPOSITION04.json').read_text())
entries={r['target']:dict(r) for r in base['source_entries']}
assert len(entries)==199
for name,r in entries.items():
 b=(CAP/name).read_bytes();assert digest(b)==r['sha256'] and len(b)==r['bytes'];r['origin']=str(CAP/name);r['qualification']='actual unchanged source04 body; not future source activation'
selected=FS/'batch-output-selected-transfer-preparation01-2026-10-03'
durable=FS/'batch-output-durable-context-preparation03-2026-10-03'
changes={
 'tradingagents/research/onchain_replication/held_score_consumer.py':P/'held_score_consumer.py',
 'tradingagents/research/onchain_replication/resource_fixture.py':P/'resource_fixture.py',
 'tradingagents/research/onchain_replication/archive_non_tail.py':selected/'archive_non_tail.py',
 'tradingagents/research/onchain_replication/selected_non_tail_transport.py':selected/'selected_non_tail_transport.py',
 'tradingagents/research/onchain_replication/archive_dispatch.py':durable/'archive_dispatch.py'}
install=[]
for name,origin in changes.items():
 b=origin.read_bytes();before=entries.get(name);r=dict(target=name,origin=str(origin),sha256=digest(b),bytes=len(b),package_source=True,change='replace' if before else 'new',baseline_sha256=before['sha256'] if before else None,actual_git_commit=None,qualification='prospective source only; Root must integrate and create genuine anchor')
 entries[name]=r;install.append(r)
assert len(entries)==201 and sum(r['package_source'] for r in entries.values())==150
write('SOURCE_INVENTORY01.json',dict(schema_version=1,status='source-only-unadmitted',baseline_source=base['actual_source_commit'],source_count=201,package_count=150,auxiliary_metadata_count=5,admission_source_count=206,logical_bytes=sum(r['bytes'] for r in entries.values()),entries=[entries[k] for k in sorted(entries)],numerical_anchor=None,registration=None,native_release=None))
write('INSTALL_MAP01.json',dict(schema_version=1,owned_implementation_copies=2,new_owned_helpers=0,dependencies_not_copied=3,changes=sorted(install,key=lambda r:r['target']),activation=None))
write('ROOT_INPUT_ROLES01.json',dict(schema_version=1,execution_admitted=False,selected_kind='original-import-held-score-selected-transfer-v2',original_dictionary_motifs=32,original_spent_samples=512,implementation_source_count=201,package_count=150,admission_source_count=206,registered_outputs={'original_resource':4,'original_local_readback':2,'non_tail_context':2,'full_member_roundtrip':2,'total':10},required_new_registered_inputs={'held_policy_schema2':None,'population_schema2':None,'selected_transport_policy':None,'source_closure_201_150_plus5':None,'case_specific_network_release':None},required_source_metadata={'auxiliary_declaration_selected201_150':None,'original_extension':None,'original_allocation':None,'original_review':None,'original_charter':None},original_inputs='Complete imported-original11, reused exact two target catalogs and all current job/plan/runtime/native inputs remain required without regenerated arrays.',missing={'genuine_new_package_anchor':None,'current_source_commit':None,'source_count_compatible_metadata_helpers':None,'independent_registration_review':None,'Root_finite_allowance':None,'fresh_native_release':None,'whole_source_runtime_input_remote_recovery':None,'actual_network_permission_scope':None},physical_wire_meter=None,plaintext_pipe_accounting_only=True,local_bytes_retired=0))
deps=[]
for p in [selected/'archive_non_tail.py',selected/'selected_non_tail_transport.py',durable/'archive_dispatch.py',FS/'batch-output-selected-transfer-review01-2026-10-03/REVIEW_SELECTED_TRANSFER01.md',FS/'held-consumer-auxiliary-source-pins-preparation01-2026-10-03/MANIFEST01.json']:
 if p.exists():deps.append(dict(path=str(p),sha256=digest(p.read_bytes()),bytes=p.stat().st_size))
write('DEPENDENCIES01.json',deps)
print(json.dumps({'actual_source04_bodies_rehashed':199,'future_source_count':201,'future_package_count':150,'future_admission_count':206,'future_bytes':sum(r['bytes'] for r in entries.values()),'installed':False}))
