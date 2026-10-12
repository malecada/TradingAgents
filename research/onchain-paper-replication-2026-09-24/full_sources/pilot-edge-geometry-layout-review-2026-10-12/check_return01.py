from pathlib import Path
import json,hashlib,math,struct
R=Path(__file__).resolve().parents[4];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'pilot-edge-geometry-layout-review-2026-10-12';I=F/'pilot-post-cache-hotpath-integration-2026-10-12';C=F/'pilot-edge-geometry-layout-candidate-2026-10-12';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((D/'SOURCE_REVIEW01.json').read_bytes())
for name,digest in s['evidence'].items():assert h(R/name)==digest,name
receipt=I/'GEOMETRY_RETURN01.json';assert h(receipt)=='9f68a2fa28692e4e617a0625d9591a917403c18fe2d1e47bab7ba619de0f5e06';v=json.loads(receipt.read_bytes());p=I/'GEOMETRY_BENCHMARK01.json';e=I/'GEOMETRY_BENCHMARK01.stderr';assert h(p)==v['raw_json_sha256'] and h(e)==v['stderr_sha256']
b=json.loads(p.read_bytes());resources=json.loads(e.read_bytes());assert resources['actual_affinity']==[0,1] and resources['cpu_limit']==[120,120] and resources['file_limit']==[4194304,4194304]
assert b['source_sha256']==h(C/'matching_annealing.py') and b['harness_sha256']=='fdc0940ca0b18d75cb933bbaa58c4a0fd38824b638f6ed09d0d1adc3ad3729e8'
assert b['numeric_kernel_policy']=='v2 both routes' and b['iterations']==48 and b['budget']==1000000
assert [r['edge_products'] for r in b['cases']]==[1024,16384,131072,1048576] and len(b['focused'])==1
prior=json.loads((F/'pilot-matching-weight-cache-integration-2026-10-12/MATCHING_BENCHMARK01.json').read_bytes());prior={r['edge_products']:r for r in prior['cases']}
rows=[]
for row in b['cases']+b['focused']:
 assert row['iterations']==48 and row['edge_products']==row['left_edges']*row['right_edges']
 assert row['v1_soft_sha256']==row['v2_soft_sha256'] and struct.pack('!d',row['v1_score'])==struct.pack('!d',row['v2_score'])
 for route in ('baseline','candidate'):
  x=row[route];assert math.isfinite(x['wall_seconds']) and x['wall_seconds']>0
  for life in x['adapter_lifetimes']:
   assert life['cache_reserved_bytes']==0 and life['cache_allocated_bytes']==life['cache_released_bytes']
   assert life['cache_peak_retained_bytes']<=33554432
 if row in b['cases']:
  old=prior[row['edge_products']]
  assert row['v1_soft_sha256']==old['v2_soft_sha256'] and row['assignment_sha256']==old['assignment_sha256'] and row['cursor_sha256']==old['cursor_sha256'] and row['used_operations']==old['used_operations']
  assert row['baseline']['operation_budget']==row['candidate']['operation_budget']==1000000
  assert not row['baseline']['checkpoint_reloaded'] and not row['candidate']['checkpoint_reloaded']
  x=row['baseline']['wall_seconds'];y=row['candidate']['wall_seconds'];rows.append({'edge_products':row['edge_products'],'baseline_seconds':x,'candidate_seconds':y,'wall_reduction_percent':100*(1-y/x),'baseline_over_candidate_ratio':x/y})
f=b['focused'][0];assert f['edge_products']==16900 and f['candidate']['operation_budget']==f['baseline']['operation_budget']==1024 and f['candidate']['checkpoint_reloaded'] is True and not f['baseline']['checkpoint_reloaded']
print(json.dumps({'result':'PASS','rows':rows,'focused_checkpoint_exact':True,'focused_performance_comparison_valid':False,'resource_wrapper_report':resources,'peak_process_rss_kib':b['peak_rss_kib'],'legacy_key_qualification':'v1/v2 result field names are inherited from harness; both routes select CACHE_POLICYv2','exact_result_qualification':'reviewed hook asserts bitwise matrices/packed score and full cursor history before shared digest output; arrays/histories are not separately persisted'},indent=2))
