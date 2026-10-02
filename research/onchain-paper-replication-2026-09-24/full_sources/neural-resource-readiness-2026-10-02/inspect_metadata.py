"""No model/array imports: pin source/compact metadata and calculate shape terms."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
S='research/onchain-paper-replication-2026-09-24/'
P='tradingagents/research/onchain_replication/'
paths=[P+n+'.py' for n in ['model','gat','job','resources','checkpoints','graph_store','job_payload','environment','workflow_storage']]
paths += [S+'pilot_successor_02/phase.py',S+'pilot_successor_02/resource-contract-v4.json',S+'config/model.json',S+'full_sources/native-resource-admission-2026-10-01/inputs02.json',S+'full_sources/native-resource-admission-2026-10-01/budget-allocation.draft.json','tests/research/onchain_replication/test_activation_checkpointing.py']
(OUT/'observed-source').mkdir()
pins=[]
for i,path in enumerate(paths):
 raw=(ROOT/path).read_bytes();name=f'{i:02d}-{Path(path).name}'
 (OUT/'observed-source'/name).write_bytes(raw)
 pins.append({'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'snapshot':'observed-source/'+name})
inv=json.loads((ROOT/(S+'full_sources/native-resource-admission-2026-10-01/inputs02.json')).read_bytes())
config=json.loads((ROOT/(S+'config/model.json')).read_bytes())
assert config['gat_heads']==[4,1] and config['gat_widths']==[16,32]
pending=[r for r in inv['pending_requirements'] if r['stage']=='neural_checkpoint']
assert len(pending)==9
rows=[]
for graph in inv['graphs']:
 n,e=graph['nodes'],graph['directed_edges']
 rows.append({'week':graph['week'],'original_requirement':next(r for r in pending if r['date']==graph['week']),
 'graph_manifest':graph['manifest'],'graph_manifest_sha256':graph['manifest_sha256'],'graph_hash':graph['graph_hash'],
 'nodes':n,'directed_edges':e,'saved_graph_file_bytes':graph['saved_array_file_bytes'],
 'historical_heuristic_bytes':e*4*64*8+n*32*4*16,
 'unique_synthetic_mcm_float32_bytes':n*32*4,
 'edge_index_int64_copy_payload_bytes':e*2*8,
 'first_gat_projected_node_payload_bytes':n*4*16*4,
 'first_gat_single_gather_or_message_at_max_effective_edges_bytes':(e+n)*4*16*4,
 'formula_qualification':'Single tensor payload at effective edge-count upper bound E+N, not peak RSS, simultaneous allocation sum or feasibility bound. Self-edge count not read.'})
assert all(r['historical_heuristic_bytes']>1073741824 for r in rows)
assert rows[0]['historical_heuristic_bytes']==10713395200
mem={}
for line in Path('/proc/meminfo').read_text().splitlines():
 if line.startswith(('MemAvailable:','MemTotal:')):
  k,v=line.split(':',1);mem[k+'_bytes']=int(v.split()[0])*1024
value={'status':'READ_ONLY_NONEXECUTABLE','execution_admitted':False,'created_at_utc':datetime.now(timezone.utc).isoformat(),
 'source_pins':pins,'neural_cells':rows,'count':9,'numerical_mcm_dependency':False,
 'activation_checkpointing_in_pinned_model_config':config.get('graph_activation_checkpointing',False),
 'host_observation':{**mem,'local_free_bytes':shutil.disk_usage(ROOT).free,'qualification':'point-in-time only, not guard readback or reservation'},
 'fresh_6gib_job_startup_minimum_bytes':9*2**30,
 'remaining_requirements_unchanged':32,'coverage_unchanged':{'supported':77,'total':109},
 'budget':{'spent':33,'body':12,'financial':15,'resource_proposed':1,'ceiling_unadopted':61,'new_slots_granted':0},
 'known_unknowns':{'peak_rss_bytes':None,'checkpoint_serialization_peak_bytes':None,'checkpoint_disk_bytes':None,
 'fresh_registration_sha256':None,'fresh_runner_source_sha256':None,'effective_graph_array_availability':None},
 'unknown_reason':'No fresh maintained neural resource runner/gate, adopted population/resource policy, array reread or measured full-size peak exists for this proposed separate route.'}
(OUT/'observations.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
for pin in pins:
 assert hashlib.sha256((OUT/pin['snapshot']).read_bytes()).hexdigest()==pin['sha256']
print(json.dumps({'status':'PASS','sources_and_compact_inputs_pinned':len(pins),'neural_requirement_records':9,'historical_heuristic_first_week_bytes':rows[0]['historical_heuristic_bytes'],'all_historical_estimates_exceed_1gib':True,'array_reads':0,'model_imports':0,'empirical_runs':0,'execution_admitted':False},sort_keys=True))
