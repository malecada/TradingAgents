import ast,hashlib,json,os,struct
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[3];pins={}
def read(p):
 p=R/p if not Path(p).is_absolute() else Path(p);b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return json.loads(b)
g=read(O.parent/'real-data-pilot-full24-entry01-2026-10-09/gate01.json');e=g['experiments']['eth-paper-real-data-end-to-end-resource-20261009-24'];refs=e['inputs']
def inp(k):
 d=read(refs[k]['path']);assert pins[refs[k]['path']]==refs[k]['sha256'];return d
job=inp('execution_job');cap=job['resources']['native_unit_limits']['file_size_bytes'];assert cap==1073741824
typed=inp('typed_payload');pair=inp('pair_policy');results=[]
for k in sorted(refs):
 if not k.startswith('graph_'):continue
 d=inp(k);p=R/refs[k]['path'];a=d['arrays']['node_features'];q=p.parent/a['path']
 # Read bounded NPY header only. No ndarray/runtime import, payload read or array decoding.
 with q.open('rb') as f:
  magic=f.read(8);assert magic[:6]==b'\x93NUMPY';version=tuple(magic[6:]);assert version in ((1,0),(2,0),(3,0));n=2 if version==(1,0) else 4;length=int.from_bytes(f.read(n),'little');assert length<=4096;raw=f.read(length);header=ast.literal_eval(raw.decode());extent=os.fstat(f.fileno()).st_size
 assert header['descr']=='<f8' and header['fortran_order'] is False and len(header['shape'])==2 and header['shape'][1]==4
 rows=header['shape'][0];assert extent==a['bytes']==8+n+length+rows*4*8
 assert typed['graphs'][d['graph_hash']]['rows']==rows
 cells=rows*32;results.append({'input':k,'graph_hash':d['graph_hash'],'node_feature_header_bytes':8+n+length,'header_sha256':hashlib.sha256(magic+length.to_bytes(n,'little')+raw).hexdigest(),'shape':list(header['shape']),'manifest_extent':extent,'rows':rows,'cells':cells,'scores_f32_bytes':4*cells,'matrix_f32_bytes':4*cells,'origins_bytes':9*cells,'all_three_within_fsize':9*cells<=cap})
for name in ('compact_mcm_batched','compact_mcm_output','batched_numeric_execution','grouped_offload','feature_residency','streamed_gat','real_pilot_import_caller'):
 p=R/'tradingagents/research/onchain_replication'/f'{name}.py';pins[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
v={'status':'ACTUAL_SEVEN_GRAPH_FILES_FIT_FIXED_NATIVE_FSIZE','native_file_size_bytes':cap,'graphs':results,'total_rows':sum(x['rows'] for x in results),'total_cells':sum(x['cells'] for x in results),'largest_rows':max(x['rows'] for x in results),'largest_score_or_matrix_bytes':max(x['scores_f32_bytes'] for x in results),'largest_origins_bytes':max(x['origins_bytes'] for x in results),'hypothetical_8402640_rows':{'cells':8402640*32,'score_bytes':8402640*32*4,'origins_bytes':8402640*32*9,'is_actual_registered_graph_row_count':False},'minimum_failing_rows':{'score_or_matrix':cap//128+1,'origins':cap//288+1},'source_pins':pins,'qualification':'Bounded NPY header metadata and manifest extents only; no payload/array decoding, numerical imports, OS file-limit experiment or admission claim. Aggregate disk and memory budgets remain separate.'}
(O/'FACTS01.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ('status','total_rows','total_cells','largest_rows','largest_score_or_matrix_bytes','largest_origins_bytes')}))
