from pathlib import Path
import json,hashlib,math
R=Path(__file__).resolve().parents[4];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'pilot-matching-weight-cache-candidate-2026-10-12';I=F/'pilot-matching-weight-cache-integration-2026-10-12';D=F/'pilot-matching-weight-cache-review-2026-10-12'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=json.loads((D/'SOURCE_REVIEW01.json').read_bytes())
for p,digest in review['evidence'].items():assert h(R/p)==digest,p
old=json.loads((C/'iteration01/SOURCE_MANIFEST01.json').read_bytes())
for row in old['unchanged_source_pins']:assert h(R/row['path'])==row['sha256'],row['path']
b=json.loads((I/'MATCHING_BENCHMARK01.json').read_bytes());assert b['candidate_sha256']==h(C/'matching_numeric_policy.py')
assert b['config_sha256']=='b3b8d88424a56a6009a4baa447e00b971d769930299c769414f6d33d9a4e873e'
assert b['native_caps_changed'] is False and b['peak_rss_kib']==65280
assert [x['edge_products'] for x in b['cases']]==[1024,16384,131072,1048576]
rows=[]
for row in b['cases']:
 n=row['edge_products'];assert n==row['left_edges']*row['right_edges'] and row['iterations']==48
 assert row['v1_soft_sha256']==row['v2_soft_sha256'] and row['v1_score']==row['v2_score']
 assert math.isfinite(row['v1_score'])
 x,y=row['v1'],row['v2'];assert x['operation_budget']==y['operation_budget']==1000000
 assert x['timing_interval']==y['timing_interval'];assert all(math.isfinite(a['wall_seconds']) and a['wall_seconds']>0 for a in (x,y))
 assert len(x['adapter_lifetimes'])==len(y['adapter_lifetimes'])==1
 c=y['adapter_lifetimes'][0];oldc=x['adapter_lifetimes'][0]
 assert c['cache_reserved_bytes']==c['cache_weight_bytes']==c['cache_validity_bytes']==0
 assert c['cache_allocated_bytes']==c['cache_released_bytes']==c['cache_peak_retained_bytes']<=33554432
 assert c['fallback_chunks']==oldc['fallback_chunks'] and c['index_bytes']==oldc['index_bytes']
 if n>16384:
  assert c['numpy_entries']==c['cache_miss_entries']==n
  assert c['cache_hit_entries']+c['cache_miss_entries']==oldc['numpy_entries']
  assert c['cache_allocated_bytes']==9*n+16384
  counts=y['phases']['numeric_counts']
  for field in ('cache_allocated_bytes','cache_allocations','cache_hit_chunks','cache_hit_entries','cache_released_bytes'):assert counts[field]==c[field]
  assert counts['agreement_numpy_entries']==c['numpy_entries']
 else:assert c['cache_allocations']==c['cache_hit_entries']==c['cache_allocated_bytes']==0
 rows.append({'edge_products':n,'baseline_seconds':x['wall_seconds'],'selected_seconds':y['wall_seconds'],'baseline_over_selected_ratio':x['wall_seconds']/y['wall_seconds'],'selected_wall_change_percent':100*(y['wall_seconds']/x['wall_seconds']-1),'soft_bytes_equal':True,'scores_equal':True,'cache_released_bytes':c['cache_released_bytes']})
assert (I/'MATCHING_BENCHMARK01.stderr').read_bytes()==b''
t=(I/'NUMERIC_CHECK01.stderr').read_text();assert t.count(' ... ok')==7 and 'Ran 7 tests in 0.868s' in t and t.rstrip().endswith('OK')
q=json.loads((I/'RESERVATION_CHECK02.json').read_bytes());assert q['cache_charge']==33619968 and q['required_numeric_bytes']==784951284
assert q['claim_created'] is False and q['physical_capacity_proven'] is False and q['baseline_v1_accepted'] is True
assert len(q['cases'])==6
for v in q['cases']:assert v['accepted']==(v['reserved']>=784951284)
for name,digest in q['source_sha256'].items():assert h(I/(name+'.py'))==digest
public=F/'real-data-pilot-full40-binding-preparation01-2026-10-12';refs=json.loads((public/'ALL_INPUT_REFS01.json').read_bytes())
assert refs['original_import_stage']==q['import_stage_reference']
assert h(R/refs['original_import_stage']['path'])==refs['original_import_stage']['sha256']
for name,digest in q['public_input_sha256'].items():assert h(public/'inputs01'/(name+'.json'))==digest
assert (I/'RESERVATION_CHECK02.stderr').read_bytes()==b''
print(json.dumps({'result':'PASS','rows':rows,'numeric_tests':7,'reservation_cases':6,'kernel_unchanged':h(R/'tradingagents/research/onchain_replication/matching_numeric_kernel.py'),'peak_process_rss_kib':b['peak_rss_kib'],'reservation_whole_refusal_qualification':'whole.validate calls per-graph validation first; observed underfunded whole errors occur there, not independently at later redundant aggregate guard'},indent=2))
