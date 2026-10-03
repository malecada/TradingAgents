"""Finite source/retained-JSON census only. Never inspect numerical bodies."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
F='research/onchain-paper-replication-2026-09-24/full_sources/'
P='tradingagents/research/onchain_replication/'
SELECTED=F+'original-import-native-successor-preparation06-2026-10-03/capsule04/'+P
FIN=F+'financial-streamed-execution-candidate02-2026-10-02/'
paths=[F+'archive-retention-readiness-2026-10-02/observations.json',F+'compact-workflow-accounting-2026-10-02/lower-bound01.json',F+'native-resource-admission-2026-10-01/inputs02.json',F+'score-tail-archive-candidate02-2026-10-02/held_tail_adapter.py',F+'score-tail-archive-candidate02-2026-10-02/REVIEW_SCORE_TAIL02.md',FIN+'REVIEW_FINANCIAL_EXECUTION02.md']
paths += [SELECTED+n+'.py' for n in ('score_batches','score_tail','mcm_score_stream','compact_stage','compact_mcm','compact_mcm_output','compact_mcm_publication','compact_matcher','owned_io')]
paths += [P+n+'.py' for n in ('compact_graph_artifacts','compact_features','compact_native_features','feature_residency','component_store','model','evaluation')]
paths += [FIN+n+'.py' for n in ('financial_execution','training','checkpoints','model_registry','run','evaluation','replay')]
paths += [F+'terminal-output-lifetime-2026-10-01/native_map.py',F+'mcm-array-kernel-2026-10-01/kernel.py',F+'graph-feature-boundary-2026-10-01/boundary.py']
refs=[]
for path in paths:
 p=ROOT/path;s=p.stat();assert s.st_size<=1048576 and p.resolve()==p
 raw=p.read_bytes();row={'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 if path.endswith('.py'):
  tree=ast.parse(raw);row['definitions']=[{'name':n.name,'line':n.lineno} for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))]
 refs.append(row)
obs=json.loads((ROOT/paths[0]).read_bytes());lower=json.loads((ROOT/paths[1]).read_bytes());inputs=json.loads((ROOT/paths[2]).read_bytes())
graphs={r['week']:r for r in inputs['graphs']};rows=[]
for r in obs['rows']:
 n=graphs[r['week']]['nodes'];cells=n*32
 assert r['cells']==cells and r['local_score_batch_bytes']==8*cells and r['local_two_float32_matrices_bytes']==8*cells
 rows.append({'week':r['week'],'nodes':n,'cells':cells,'score_batch_f64_bytes':8*cells,'raw_mcm_f32_bytes':4*cells,'graph_artifact_mcm_f32_payload_bytes':4*cells,'non_tail_payload_bytes':16*cells,'tail_payload_bytes':80*cells})
assert len(rows)==9 and len({r['week'] for r in rows})==9
sums={k:sum(r[k] for r in rows) for k in ('nodes','cells','score_batch_f64_bytes','raw_mcm_f32_bytes','graph_artifact_mcm_f32_payload_bytes','non_tail_payload_bytes','tail_payload_bytes')}
assert sums['non_tail_payload_bytes']==9239969792 and sums['tail_payload_bytes']==46199848960
v={'schema_version':1,'scope':'nine saved metadata weeks times original32 motifs; logical payload arithmetic only','rows':rows,'totals':sums,'source_references':refs,'union80_assumed':False,'actual_offload_bytes':0,'numerical_imports':False,'array_bodies_read':0,'qualification':'Graph-artifact NPY headers, edge arrays, source graphs, metadata/inventory, dictionary, optimizer/checkpoints, scratch and physical allocation are additional; no full dataset/batch union or capacity inferred.'}
(OUT/'census01.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({'status':'PASS','source_metadata_files':len(refs),'weeks':9,'totals':sums,'array_bodies_read':0},sort_keys=True))
