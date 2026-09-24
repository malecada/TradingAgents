"""Read-only validation of protocol freeze and preserved admission metadata."""
from pathlib import Path
import hashlib
import json


def check(root):
    root=Path(root)
    study=root/'research/onchain-paper-replication-2026-09-24'
    freeze=json.loads((study/'protocol-freeze.json').read_text())
    for path,digest in freeze['files'].items():
        assert hashlib.sha256((study/path).read_bytes()).hexdigest()==digest,path
    history=json.loads((study/'history.json').read_text())
    assert len(history['lineage'])==len(set(history['lineage']))==17
    for path,digest in history['metadata_hashes'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
    records=json.loads((study/'fidelity.json').read_text())['records']
    assert {x['id'] for x in records}=={f'F{i:02}' for i in range(1,21)}|{f'U{i:02}' for i in range(1,15)}
    assert all(x['status']!='not_started' for x in records)
    rows=json.loads((study/'table-map.json').read_text())
    cells={(r['asset'],r['task'],r['arm'],r['variant'],f,s) for r in rows for f in r['folds'] for s in r['seeds']}
    assert len(rows)==44 and len(cells)==1400
    training=json.loads((study/'config/training.json').read_text())
    assert len(set(training['diagnostic_cells']))==20
    budget=json.loads((study/'budget-amendment.proposed.json').read_text())
    assert sum(x['claims'] for x in budget['stages'].values())==34
    assert budget['prior_attempts']+34==budget['cumulative_claim_ceiling']==51
    return {'freeze':'valid','prior_claims':17,'prior_metadata_hashes':len(history['metadata_hashes']),'table_rows':44,'paper_fits':1400,'diagnostic_fits':20,'empirical_admission':False}

if __name__=='__main__':
    print(json.dumps(check(Path(__file__).resolve().parents[2]),sort_keys=True))
