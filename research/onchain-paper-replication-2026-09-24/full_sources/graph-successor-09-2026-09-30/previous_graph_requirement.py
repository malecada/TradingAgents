"""Compact trusted-review prerequisite; no repeated graph/SQLite/raw body read."""
from pathlib import Path
import hashlib
import json
NAME='eth-paper-graph-resource-20260930-08'
BASE=Path('research/onchain-paper-replication-2026-09-24/full_sources')
VERIFY=BASE/'graph-verification-08-2026-09-30'
REQUIRED=('result.json','guard01/final.json','closure01.json','CLOSURE_REVIEW.md')


def raw(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>=2_000_000:
        raise ValueError('compact regular prerequisite evidence required')
    return path.read_bytes()

def sha(path):return hashlib.sha256(raw(path)).hexdigest()
def read(path):return json.loads(raw(path))

def verify(root):
    root=Path(root);here=root/VERIFY;review=read(here/'closure-review.json')
    if review.get('decision')!='accepted' or review.get('source_claim')!=NAME or set(review.get('evidence',{}))!=set(REQUIRED):
        raise ValueError('independent prior array-verification closure acceptance required')
    for name,h in review['evidence'].items():
        if sha(here/name)!=h:raise ValueError('reviewed prerequisite evidence changed')
    result=read(here/'result.json');closure=read(here/'closure01.json')
    run=root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME
    ledger=root/'research_runs'/NAME
    if (result['status']!='complete' or result['source_claim']!=NAME
            or result['claim_sha256']!=sha(ledger/'claim.json')
            or result['terminal_sha256']!=sha(ledger/'complete.json')
            or closure['status']!='complete' or closure['result']!=result):
        raise ValueError('prior verification identity differs')
    terminal=read(ledger/'complete.json');observer=read(run/'observer.json')
    if (terminal['status']!='complete' or terminal['cell_count']!=8
            or not all(c['status']=='complete' for c in terminal['cells'])
            or observer['terminal_sha256']!=sha(ledger/'complete.json')
            or not observer['all_cells_complete'] or not observer['cgroup_empty']):
        raise ValueError('prior producer is not completely reconciled')
    for path in (here/'guard01/final.json',run/'guard/final.json'):
        g=read(path)
        if (g['phase']!='complete' or g['child_exit_code']!=0 or g['cleanup_verified'] is not True
                or Path(g['cgroup']).exists() or Path('/proc',str(g['monitor_pid'])).exists()):
            raise ValueError('prior producer or verifier owner remains')
    return {'source_claim':NAME,'review_sha256':sha(here/'closure-review.json'),'graph_hash':result['graph_hash'],
            'qualification':'Trusted independent compact closure checks, not repeated array or raw verification.'}
