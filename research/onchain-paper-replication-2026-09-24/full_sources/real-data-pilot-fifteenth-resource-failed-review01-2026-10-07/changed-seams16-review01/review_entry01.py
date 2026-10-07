"""Static exact changed-entry inverse and actual bounded early-check receipt join."""
from pathlib import Path
import ast,hashlib,json
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-fifteenth-resource-failed-review01-2026-10-07/changed-seams16-review01'
D=F/'real-data-pilot-final16-2026-10-07';OLD=F/'real-data-pilot-final15-2026-10-07';I=F/'real-data-pilot-index-capacity01-2026-10-07'
evidence={}
def raw(p):
 p=Path(p);b=p.read_bytes();evidence[str(p)]=hashlib.sha256(b).hexdigest();return b
def ref(p):return {'path':str(p),'sha256':hashlib.sha256(raw(p)).hexdigest()}
def read(p):return json.loads(raw(p))
def write(n,v):
 p=H/n
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return p
source=read(H/'SOURCE_REVIEW01.json');assert source['decision']=='accepted_source_candidates_only'
before=raw(OLD/'preflight01.py').decode();after=raw(D/'preflight01.py').decode()
tree=ast.parse(after);assign={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'INDEX_CAPACITY','EXPECTED_RESOURCES','NAME'}}
helper=assign['INDEX_CAPACITY'];assert helper==ref(I/'candidate/index_capacity.py')
policy=assign['EXPECTED_RESOURCES'];override=read(F/'real-data-pilot-ram-amendment01-2026-10-07/NEXT_PILOT_RESOURCE_OVERRIDE01.json')
assert all(policy[k]==v for k,v in override['next_resource_overrides'].items())
assert policy['start_reserve_bytes']==policy['memory_max_bytes']+policy['reserve_bytes']==9126805504
assert policy['disk_floor_bytes']==10737418240 and policy['storage_budget']['experiment']==assign['NAME']=='eth-paper-real-data-end-to-end-resource-20261007-16'
start=after.index('    # Scalar/header-only capacity refusal');end=after.index('    runtime_inventory=',start);seam=after[start:end]
assert after.index("raise ValueError('compact input pin changed:")<start<end
assert "refs.get(INDEX_CAPACITY['path'])==INDEX_CAPACITY['sha256']" in seam and "hashlib.sha256(capacity_body).hexdigest()==INDEX_CAPACITY['sha256']" in seam
assert "capacity_descriptor['resource_graph_inputs'],capacity_numeric," in seam and "capacity_descriptor['configs']['dictionary']" in seam
assert "admission.inputs[capacity_plan['compact_mcm_input']]['path']" in seam
inverse=after[:start]+after[end:]
inverse='\n'.join(line for line in inverse.split('\n') if not line.startswith('INDEX_CAPACITY='))
inverse=inverse.replace('20261007-16','20261007-15').replace('fixed16-metadata','fixed15-metadata').replace('2684354560','3221225472').replace('9126805504','9663676416').replace('!=87','!=86').replace("'effective_attempt_budget':87","'effective_attempt_budget':86").replace("'index_capacity':index_capacity,",'')
assert inverse==before
assert raw(D/'root_io.py').decode().replace('20261007-16','20261007-15')==raw(OLD/'root_io.py').decode()
actual=read(D/'ACTUAL_EARLY_CAPACITY01.json');cap=read(I/'CAPACITY01.json')
assert actual['status']=='METADATA_ONLY_NOT_ADMITTED' and actual['no_empirical_execution'] is True
assert actual['helper']==helper and actual['candidate_policy']==ref(I/'mcm_policy01.json') and actual['original_gate']=={k:cap['gate_ref'][k] for k in ('path','sha256')}
for key in ('graphs','max_buffer_required','max_output_required','qualification'):assert actual['result'][key]==cap[key]
p=write('ENTRY_SEAM_REVIEW01.json',{'schema_version':1,'decision':'accepted_changed_source_entry_seams_only','identity':assign['NAME'],'candidate_source_review':ref(H/'SOURCE_REVIEW01.json'),'evidence':evidence,'checks':['Exact inverse to original15 preflight except identity/preparer path, budget86to87 expectation, two authorized reserve fields, authenticated capacity block and returned index_capacity receipt.','RootIO byte-identical except fixed identity.','Capacity helper SHA and release-evidence membership checked before execution. Source/input pin loop precedes helper; helper precedes explicit include_torch runtime inventory.','Helper reads actual admitted selected representation descriptor, actual compact_mcm_input numeric policy and dictionary. No fixture authority substituted.','Actual early capacity receipt exactly joins previously independently reconstructed seven bounded header records and selected candidate policy.','Exact8.5GiB startup =6GiB cap+2.5GiB hostreserve;5GiB high/10GiB floor unchanged.'],'capacity':{'max_buffer_bytes':439582708,'max_output_bytes':289981568,'max_numeric_bytes':729564276},'findings':[],'qualification':'Acceptance permits Root source/config integration; it does not admit87, a genuine final16 claim, current resource headroom, private transport or final concrete release. Existing original15 remains FAILED/spent.','not_tested':['No preflight/RootIO execution or mock Admission/Owner.','Final16 completed metadata/gate/binding/committed read-only admission/release references not yet present or reviewed.','Fresh outcome15 external recovery pending Root receipt.','No real numerical run, whole-capacity/throughput/economic claim, broad unchanged matrix or body reauthentication.']})
m=write('ENTRY_MANIFEST01.json',{'schema_version':1,'files':[ref(H/'review_entry01.py'),ref(p)],'decision':'accepted_changed_source_entry_seams_only'})
print(json.dumps({'review':ref(p),'manifest':ref(m)},sort_keys=True))
