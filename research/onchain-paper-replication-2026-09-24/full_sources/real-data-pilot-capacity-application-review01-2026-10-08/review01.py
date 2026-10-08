import ast,hashlib,json,types,sys,difflib
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;R=H.parents[3]
P=B/'real-data-pilot-complete-neighborhood-capacity-preparation01-2026-10-08';A=B/'real-data-pilot-capacity-application01-2026-10-08'
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes())
b=(P/'successor02/capacity.py').read_bytes();assert sha(b)=='2d2f4f3e7b3804ce0721aefbdd822e8766d45da61afa30d8fce0b76788415315'
assert b.decode().replace((P/'successor02/ADDITION.txt').read_text(),'')==(P/'capacity.py').read_text()
k=(P/'imported_kernel.py').read_bytes();assert sha(k)=='dc0a244b7cce4261093a95ce686a01bae0f26c8797a8616463c7d5078a2b2604'
basepath=B/'original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py'
a=basepath.read_text();new=k.decode()
assert ''.join(difflib.unified_diff(a.splitlines(True),new.splitlines(True),fromfile=str(basepath.relative_to(R)),tofile='candidate/imported_kernel.py'))==(P/'KERNEL.patch').read_text()
x=read(A/'INPUTS01.json');actual=read(A/'CAPACITY01.json');dpath=B/'real-data-pilot-original-motif-dimensions01-2026-10-08/MOTIF_DIMENSIONS01.json';db=dpath.read_bytes();assert sha(db)=='05a3d78114463bec74d1d507fb05c120d893c1d95b42a943fabc4db8944cf70d';d=json.loads(db)
cpath=R/'research_artifacts/onchain-paper-replication-2026-09-24/engineering/eth-seven-graph-weak-one-hop-census-20261008-01/results/SUMMARY01.json';cb=cpath.read_bytes();assert sha(cb)=='db189e23d44799ef5656fd8b89b243d262127d73707640a1057e27452de019e7';c=json.loads(cb)
assert len(x['topology']['graphs'])==len(c['graphs'])==7 and len(x['motifs']['representatives'])==len(d['motifs'])==d['motif_count']==32
for t,r,o in zip(x['topology']['graphs'],c['graphs'],x['feature_header_observations'],strict=True):
 assert (t['graph_sha256'],t['nodes'],t['edges'],t['maximum_cardinality'],t['maximum_center_index'])==(r['graph_hash'],r['node_count'],r['edge_count'],r['maximum_cardinality'],r['maximum_center_index'])
 assert o['graph']==t['graph_sha256']
 for key,rows,itemkey in [('node_features',t['nodes'],'node_itemsize'),('edge_features',t['edges'],'edge_itemsize')]:
  h=o['feature_headers'][key];assert h['descr']=='<f8' and not h['fortran_order'] and h['shape']==[rows,t[key]] and t[itemkey]==8
  assert h['file_bytes']==h['header_bytes']+rows*t[key]*8
for a,m in zip(x['motifs']['representatives'],d['motifs'],strict=True):
 assert (a['motif_index'],a['graph_sha256'],a['nodes'],a['edges'],a['node_features'],a['edge_features'])==(m['motif_index'],m['representative_json_sha256'],m['node_count'],m['edge_count'],m['node_feature_width'],m['edge_feature_width'])
 assert a['node_itemsize']==a['edge_itemsize']==8
assert x['motifs']['dictionary_sha256']==d['original_dictionary_json_sha256']
module=types.ModuleType('reviewed_capacity');exec(compile(b,'capacity.py','exec'),module.__dict__)
computed=module.prepare(x['topology'],x['motifs'],expected_topology_sha256=module.digest(x['topology']),expected_motifs_sha256=module.digest(x['motifs']),limits=x['limits'])
assert computed==actual and len(actual['pairs'])==224 and len(actual['refusals'])==1287
assert not actual['execution_admitted'] and not actual['complete_resource_envelope_proven'] and not actual['reported_limits_satisfied']
w=actual['universal_component_envelopes'];expected={'pair_entries':8402640,'retained_pair_state_bytes':268884480,'normalization_axis_entries':700220,'checkpoint_single_array_file_bytes':67221248,'score_tail_records_single_file_bytes':5242880,'pair_event_chunk_single_file_bytes':8257536}
for k,v in expected.items():assert w[k]['required']==v
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
result={'decision':'ACCEPT narrow source/metadata capacity diagnosis only','source_sha256':sha(b),'kernel_candidate_sha256':sha((P/'imported_kernel.py').read_bytes()),'application_inputs_sha256':sha((A/'INPUTS01.json').read_bytes()),'application_result_sha256':sha((A/'CAPACITY01.json').read_bytes()),'pairs':224,'component_refusals':1287,'execution_admitted':False,'complete_resource_envelope_proven':False,'checked_maxima':expected,'checks':['successor insertion exact inverse','optional kernel patch exact baseline diff','pinned motif/census metadata joined all7x32','retained14header observations internally consistent; no header/body reread','exact integer-only application replay matches full report'],'scope':'no numerical imports, original bodies, native jobs or scientific admission'}
(H/'CHECKS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
