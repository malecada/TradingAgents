"""Read explicit hash-pinned documentary metadata only. No research imports/run APIs."""
import collections,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def read_inputs():
 manifest=json.loads((HERE/'source_refs01.json').read_text());out={}
 for row in manifest['files']:
  p=ROOT/row['path'];assert p.resolve()==p and p.suffix in {'.json','.md'},'only explicit documentary metadata'
  raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'document drift: '+row['path']
  out[row['key']]=json.loads(raw) if p.suffix=='.json' else raw.decode()
 return out
def summarize(d):
 coverage=d['coverage'];requirements=coverage['requirements'];assert len(requirements)==109 and len({r['original_id'] for r in requirements})==109
 remaining=[r for r in requirements if not r['supported']];assert len(remaining)==32 and sum(r['supported'] for r in requirements)==77
 ledger=d['original_ledger'];original=ledger['cells'] if isinstance(ledger,dict) and 'cells' in ledger else ledger
 assert isinstance(original,list) and len(original)==109
 prior={r['id']:r for r in original}
 for r in requirements:assert prior[r['original_id']]['status']==r['original_status'] and prior[r['original_id']].get('reason')==r.get('original_reason')
 allocation=d['allocation'];ids=[c for b in allocation['batches'] for c in b['cells']];assert len(ids)==len(set(ids))==1420
 table=d['tables'];cells=table['cell_dispositions'];assert len(cells)==1420 and set(ids)=={c['id'] for c in cells}
 assert all(c['status']=='pending' and c['attempts']==[] for c in cells)
 paper=[c for c in cells if c['tables']];diagnostic=[c for c in cells if not c['tables']];assert len(paper)==1400 and len(diagnostic)==20
 assert len(table['rows'])==44 and not any(r['complete'] for r in table['rows'])
 return {'scope':'documentary completeness reconciliation, no new outcomes or admission','resource':{'denominator':109,'original_statuses':dict(collections.Counter(r['status'] for r in original)),'stage_totals':dict(collections.Counter(r['stage'] for r in requirements)),'evidence_counts':dict(collections.Counter(r['requirement_evidence'] for r in requirements)),'supported':77,'remaining':32,'remaining_exact':[{'id':r['original_id'],'stage':r['stage'],'date':r['date']} for r in remaining]},'fits':{'unique':1420,'paper':1400,'diagnostic':20,'statuses':dict(collections.Counter(c['status'] for c in cells)),'by_asset':dict(collections.Counter(c['asset'] for c in cells)),'seeds':sorted({c['seed'] for c in cells}),'folds':sorted({c['fold'] for c in cells}),'batches':[{'id':b['id'],'count':len(b['cells'])} for b in allocation['batches']],'printed_rows':44,'distinct_table_patterns':len({(r['asset'],r['task'],r['arm'],r['variant']) for r in table['rows']}),'paper_groups':[{'task':k[0],'variant':k[1],'count':v} for k,v in sorted(collections.Counter((c['task'],c['variant']) for c in paper).items())]},'source_grid_recorded_counts':d['source_grid']['counts'],'source_grid_qualification':'Version3 full-history admission accounting; not a fresh raw-body availability census and not a denial of later pilot source evidence.','criteria_recorded':[{'id':r['id'],'status':r['status']} for r in d['completion']['criteria']],'completion_flags':d['completion']['flags'],'qualification':'Met-synthetic statuses do not imply empirical completion; latest STATE snapshot and current genuine evidence must govern launches. No pending cell becomes unavailable or complete here.'}
if __name__=='__main__':print(json.dumps(summarize(read_inputs()),indent=2,sort_keys=True))
