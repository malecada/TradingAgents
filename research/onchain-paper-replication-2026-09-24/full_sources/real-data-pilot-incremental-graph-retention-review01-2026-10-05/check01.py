from pathlib import Path
import hashlib,importlib.util,json,tempfile
from unittest.mock import patch
D=Path(__file__).resolve().parent;M=D.parents[3];A=D.parent/'real-data-pilot-incremental-graph-retention01-2026-10-05'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'MANIFEST01.json')=='7b0e2e9f32ce8bc2b4c29ed4f9da176ecab9d11c5c80726ca9a828de61fa64c7'
manifest=json.loads((A/'MANIFEST01.json').read_text())
for n,r in manifest['files'].items():assert sha(A/n)==r['sha256'] and (A/n).stat().st_size==r['bytes']
assert sha(A/'select01.py')=='e02325e898567427ea65c9e346e78338d3533701222addc94da7596b469948da'
spec=importlib.util.spec_from_file_location('author_fixture_source',A/'test_select01.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);selector=f.m
record={'source_sha256':sha(A/'select01.py'),'manifest_sha256':sha(A/'MANIFEST01.json'),'author_members_authenticated':len(manifest['files'])}
# Independent active-consumer counterexample: input is genuine produced result
# metadata naming the ledger workspace, instead of directly naming the directory.
with tempfile.TemporaryDirectory(dir=D) as tmp,patch.object(selector.subprocess,'check_output',return_value=b''):
 root=Path(tmp);put,run,base=f.fixture(root)
 result=selector.select(root,f.ID);assert result['status']=='DRAFT'
 input_path=base+'result.json'
 put('research_runs/active-consumer/claim.json',{'experiment':{'inputs':{'graph_result':{'path':input_path,'sha256':sha(root/input_path)}}}})
 result=selector.select(root,f.ID)
 record['active_producer_result_consumer']={'accepted_status':result['status'],'input':input_path,'workspace':json.loads((root/input_path).read_bytes())['workspace'],'selected_ledger':result['files'][0]['path'],'finding':'active same-producer result consumer accepted despite workspace dependency'}
 assert result['status']=='DRAFT'
 # Existing direct ledger/aggregation test still refuses; this isolates scope.
 put('research_runs/active-consumer/claim.json',{'experiment':{'inputs':{'ledger':{'path':base+'aggregation'}}}})
 try:selector.select(root,f.ID)
 except ValueError as e:record['direct_aggregation_control']=str(e)
 else:raise AssertionError('direct consumer did not refuse')
# Actual unused first graph, metadata-only and no graph/ledger reads.
actual=M/'research_runs'/f.ID
assert not (actual/'complete.json').exists(),'first graph became complete; do not call it absent'
read=[];original=Path.read_bytes

def metadata_only(path):
 assert path.suffix=='.json','unexpected nonmetadata read'
 assert not path.name.endswith(('.npy','.sqlite'))
 read.append(str(path));return original(path)
with patch.object(Path,'read_bytes',metadata_only):
 try:selector.select(M,f.ID)
 except (FileNotFoundError,ValueError) as e:record['actual_first_graph_refusal']={'type':type(e).__name__,'reason':str(e),'metadata_read_paths':read,'claim_exists':(actual/'claim.json').exists(),'complete_exists':False}
 else:raise AssertionError('unproduced first graph was selected')
record['array_or_ledger_body_reads']=0;record['native_or_network_actions']=False;record['live_mutations']=False
(D/'CHECK01.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps(record,sort_keys=True))
