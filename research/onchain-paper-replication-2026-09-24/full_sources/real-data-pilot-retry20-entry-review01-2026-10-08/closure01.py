import json,hashlib
from pathlib import Path
R=Path.cwd(); F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=Path(__file__).resolve().parent
c=json.loads((H/'CHECKS01.json').read_text()); evidence=c['evidence']; covered={};checks=[]
def read(p,h=None):
 raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();assert h is None or digest==h;pname=str(p.relative_to(R));evidence[pname]=digest;return json.loads(raw)
def mark(p,h):covered[p]=h
p=F/'real-data-pilot-post19-source-corrections01-2026-10-08/SOURCE_ADOPTION01.json'
for v in read(p)['adopted']:
 read(R/v['independent_review'],v['review_sha256']);mark(v['path'],v['new_sha256'])
p=F/'real-data-pilot-archive-hotpath-adoption01-2026-10-08/SOURCE_ADOPTION01.json';v=read(p);read(F/'real-data-pilot-archive-hotpath-root-review01-2026-10-08/SOURCE_REVIEW01.json',v['review_sha256'])
for x in v['sources']:mark(x['path'],x['adopted_sha256'])
p=F/'real-data-pilot-checkpoint-throughput-adoption01-2026-10-08/SOURCE_ADOPTION01.json';v=read(p);read(R/v['review']['path'],v['review']['sha256'])
for name,x in v['sources'].items():mark('tradingagents/research/onchain_replication/'+name,x['after_sha256'])
v=read(F/'real-data-pilot-imported-live-history-adoption01-2026-10-08/SOURCE_ADOPTION01.json');read(R/v['review']['path'],v['review']['sha256']);mark(v['path'],v['after_sha256'])
v=read(F/'real-data-pilot-diagnostic-source-adoption01-2026-10-08/SOURCE_ADOPTION01.json')
for x in v['scoped_independent_reviews']:read(R/x['path'],x['sha256'])
for p,x in v['files'].items():mark(p,x['after_sha256'])
g=json.loads((F/'real-data-pilot-final20-2026-10-08/gate01.json').read_text())['experiments']['eth-paper-real-data-end-to-end-resource-20261008-20'];o=json.loads((F/'real-data-pilot-final19-2026-10-08/gate01.json').read_text())['experiments']['eth-paper-real-data-end-to-end-resource-20261008-19']
changes={p:h for p,h in g['source_files'].items() if p.startswith('tradingagents/') and o['source_files'].get(p)!=h}
assert all(covered.get(p)==h for p,h in changes.items()),{p:h for p,h in changes.items() if covered.get(p)!=h}
(H/'SOURCE_CLOSURE01.json').write_text(json.dumps({'status':'INHERITED_CHANGED_SOURCE_CLOSURE_ACCEPTED','changed_sources':changes,'reviewed_adoptions':covered,'evidence':evidence,'qualification':'Exact inherited independent reviews reused; no numerical or mutation suite repeated.'},indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PASS','changed_main_sources':len(changes)}))
