from pathlib import Path
import ast,json,hashlib,math
R=Path(__file__).resolve().parents[4];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';I=F/'pilot-post-cache-hotpath-integration-2026-10-12'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((I/'INSTRUMENTATION01.json').read_bytes());original=R/'tradingagents/research/onchain_replication/matching_annealing.py';assert h(original)==record['original_sha256']
text=original.read_text();t=ast.parse(text);f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked');source='\n'.join(text.splitlines()[f.lineno-1:f.end_lineno])+'\n';initial=source
for change in record['literal_changes']:
 assert source.count(change['old'])==1;source=source.replace(change['old'],change['new'])
assert source==(I/'INSTRUMENTED_advance01.py').read_text()
for change in reversed(record['literal_changes']):
 assert source.count(change['new'])==1;source=source.replace(change['new'],change['old'])
assert source==initial
prior=json.loads((F/'pilot-matching-weight-cache-integration-2026-10-12/MATCHING_BENCHMARK01.json').read_bytes());expected={r['edge_products']:r for r in prior['cases']}
p=json.loads((I/'POST_CACHE_PROFILE01.json').read_bytes());assert [r['products'] for r in p['cases']]==[16384,131072,1048576]
rows=[]
for row in p['cases']:
 baseline=expected[row['products']];assert row['soft_sha256']==baseline['v2_soft_sha256'] and row['operations']==baseline['used_operations']
 wall=row['advance_wall_seconds'];assert math.isfinite(wall) and wall>0
 times=row['timings']
 for k,v in times.items():
  assert type(v['calls']) is int and v['calls']>=0
  assert 0<=v['exclusive_seconds']<=v['inclusive_seconds'] and math.isfinite(v['inclusive_seconds'])
 exclusive=sum(v['exclusive_seconds'] for v in times.values());assert exclusive<=wall
 rows.append({'products':row['products'],'advance_wall_seconds':wall,'geometry_fraction':times['geometry']['inclusive_seconds']/wall,'ordered_scatter_fraction':times['ordered_scatter']['inclusive_seconds']/wall,'timed_exclusive_fraction':exclusive/wall,'soft_matches_accepted_v2':True,'operations_match_accepted_v2':True,'snapshot_cache_live_bytes':row['cache_counts']['cache_reserved_bytes']})
assert (I/'PROFILE01.stderr').read_bytes()==b''
assert json.loads((I/'PROFILE01.log').read_bytes())==p
print(json.dumps({'result':'PASS','literal_instrumentation_inverse':True,'rows':rows,'qualification':'Instrumented advance/hardening interval; timers perturb cost and helper dispatch. Soft-result digest and operation totals agree for three synthetic observations; no full sparse score, assignment or failure-prefix proof follows from this profile. Snapshots precede cleanup; live bytes here are not leak evidence.'},indent=2))
