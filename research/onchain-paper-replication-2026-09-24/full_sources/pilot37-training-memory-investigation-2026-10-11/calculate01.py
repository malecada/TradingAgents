"""Finite stdlib metadata arithmetic; never opens arrays/labels or imports numerics."""
import hashlib,json,resource,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(128*1024**2,128*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
ROOT=Path(__file__).resolve().parents[4];DEST=Path(__file__).resolve().parent
BASE=DEST.parent/'real-data-pilot-full37-binding-preparation01-2026-10-11'
observed={}
def read(p):
    before=p.stat();assert before.st_size<2*1024**2
    raw=p.read_bytes();after=p.stat()
    assert (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
    observed[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    return json.loads(raw)
refs=read(BASE/'PUBLIC_INPUT_REFS_DRAFT01.json');p=read(BASE/'public01/pilot.json')
t=read(BASE/'public01/typed_payload.json')
model=read(ROOT/refs['model']['path'])
assert model['mlp_widths']==[64,32] and model['gat_heads']==[4,1] and model['gat_widths']==[16,32]
assert p['model_execution']==dict(backend='streamed-gat-mulsum-v1',block_edges=65536,graph_activation_checkpointing=True,schema_version=2)
assert len(p['graph_inputs'])==7 and len(p['graph_sequences'])==16 and all(len(x)==28 for x in p['graph_sequences'])
rows=[]
for h,role in p['graph_inputs'].items():
    path=ROOT/refs[role]['path'];m=read(path)
    assert observed[str(path.relative_to(ROOT))]['sha256']==refs[role]['sha256'] and m['graph_hash']==h
    C=t['graphs'][h]['kinds']['mcm-output-f32']['max_preserved_bytes']//4
    assert C%32==0;N=C//32
    a=m['arrays'];B=a['edge_index']['bytes']
    # Existing loader accepts NPY v1/v2 headers <=10,000 bytes. No NPY opened.
    # Selected training contract requires two int64 rows: payload=16E.
    emin=(B-10012+15)//16;emax=(B-10)//16
    assert 10<=a['node_features']['bytes']-32*N<=10012
    epmin=max(N,emin);epmax=N+emax # E' = E - old_self_loops + N; no duplicate edges.
    parent_min=sum(max(0,a[k]['bytes']-10012) for k in ('node_features','edge_index','edge_features','edge_aggregates'))
    rows.append(dict(graph=h,role=role,declared_nodes=N,edge_count_interval_from_metadata=[emin,emax],
        effective_gat_edges_interval=[epmin,epmax],references=sum(x.count(h) for x in p['graph_sequences']),
        mcm_float32_bytes=128*N,edge_index_int64_bytes_interval=[16*emin,16*emax],
        resident_parent_numeric_payload_lower_bytes=parent_min,node_id_tuple_slots_bytes=8*N,
        mlp_first_output_bytes=256*N,gat1_input_clean_each_bytes=128*N,gat1_projection_output_each_bytes=256*N,
        gat1_node_scores_each_bytes=16*N,gat1_edge_head_each_bytes_interval=[16*epmin,16*epmax],
        gat2_projection_output_each_bytes=128*N,gat2_edge_head_each_bytes_interval=[4*epmin,4*epmax],
        gat1_aggregate_live_payload_lower_bytes=832*N+64*epmin+65536*4*4*16))
assert sum(r['references'] for r in rows)==448
base=sum(r['mcm_float32_bytes']+r['resident_parent_numeric_payload_lower_bytes']+r['node_id_tuple_slots_bytes'] for r in rows)
for r in rows:r['coexisting_logical_payload_lower_bytes']=base+r['gat1_aggregate_live_payload_lower_bytes']
out=dict(status='SOURCE_METADATA_ONLY_NOT_PEAK_OR_ADMISSION',source_freeze='998d353d86d683e8a095ebffb4e539a5c849ca68',
    graph_rows=rows,total_declared_nodes=sum(r['declared_nodes'] for r in rows),total_references=448,
    all_mcm_logical_bytes=sum(r['mcm_float32_bytes'] for r in rows),
    all_resident_parent_numeric_payload_lower_bytes=sum(r['resident_parent_numeric_payload_lower_bytes'] for r in rows),
    all_node_id_tuple_slots_bytes=sum(r['node_id_tuple_slots_bytes'] for r in rows),
    coexisting_base_logical_payload_lower_bytes=base,
    maximum_coexisting_logical_payload_lower_bytes=max(r['coexisting_logical_payload_lower_bytes'] for r in rows),
    resident_excludes_mapped_mcm_lower_bytes=base-sum(r['mcm_float32_bytes'] for r in rows),
    assumptions=['Declared MCM32 capacity is the intended exact unchanged node denominator; no array values or headers were read.',
    'Graph raw numeric payload lower bound subtracts maximum allowed10012-byte NPY header from each of28 numeric files.',
    'Edge count is an interval from recorded extent and selected int64[2,E] training contract, not asserted measured count.',
    'GAT1 simultaneous payload counts x,clean,h,out,source_score,target_score,maximum,denom,e,numer,attention,endpoints,one full message block.',
    'Logical MCM mapped extent is not a guaranteed simultaneous RSS floor; clean file pages are reclaimable.',
    'Python strings,allocator,sort/unique workspaces,autograd,RNG,Torch/runtime,dictionary,monitor,backward scratch omitted.'],
    observed=observed)
(DEST/'SIZES01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('graph_rows','observed','assumptions')},indent=2))
print([(r['role'],r['declared_nodes'],r['edge_count_interval_from_metadata'],round(r['coexisting_logical_payload_lower_bytes']/2**30,3)) for r in rows])
