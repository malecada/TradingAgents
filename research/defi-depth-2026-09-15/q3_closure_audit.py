"""Read-only Q3 failure closure; no acquisition or economic calculation."""
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'research/defi-depth-2026-09-15'
RUN = ROOT / 'research_runs/defi-depth-q3-20260915'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def reconstruct():
    claim_raw = (RUN/'claim.json').read_bytes()
    terminal_raw = (RUN/'failed.json').read_bytes()
    claim, terminal = json.loads(claim_raw), json.loads(terminal_raw)
    expected = claim['experiment']['cells']
    counts, errors, published, receipts, intents = Counter(), Counter(), {}, {}, {}
    actual = set()
    def add(cell):
        cid = cell['id']
        if cid in published:
            assert published[cid] == cell['status']
        published[cid] = cell['status']
    for path in sorted((RUN/'outputs').glob('*.json')):
        raw = path.read_bytes()
        assert terminal['output_sha256'][path.name] == sha(raw)
        actual.add(path.name)
        obj = json.loads(raw)
        if path.name.endswith('-attempt.json'):
            intents[obj['id']] = obj
        elif path.name.endswith('-receipt.json'):
            receipts[obj['id']] = obj
            body = base64.b64decode(obj['body_base64'], validate=True)
            assert len(body) == obj['body_bytes'] and sha(body) == obj['body_sha256']
            counts['raw_bytes'] += len(body)
            counts['actual_rpc_requests' if obj['attempted'] else 'suppressed_requests'] += 1
            if obj['attempted']:
                counts['http_status_' + str(obj['http_status'])] += 1
                decoded = json.loads(body)
                assert decoded['id'] == obj['request']['id']
                if 'error' in decoded:
                    errors[str(decoded['error'].get('code')) + ': ' + str(decoded['error'].get('message'))] += 1
        elif path.name == 'boundaries.json':
            for date, row in obj['boundaries'].items():
                add({'id': 'base-' + date + '-boundary-eligibility', **row})
            for year, row in obj['cohorts'].items():
                add({'id': 'cohort-' + year + '-boundary-eligibility', **row})
        else:
            for row in obj.get('cells', []): add(row)
    assert actual == set(terminal['output_sha256'])
    assert set(intents) == set(receipts)
    for rid in intents:
        for key in ('id','attempted','request','url','request_utc'):
            assert intents[rid][key] == receipts[rid][key]
    assert set(published) <= set(expected)
    rows = []
    for cid in expected:
        if cid in published: category = 'published_' + published[cid]
        elif cid in receipts: category = 'receipt_only_attempted' if receipts[cid]['attempted'] else 'receipt_only_suppressed'
        else: category = 'unclassified_without_direct_q3_receipt'
        counts[category] += 1
        rows.append({'id': cid, 'closure_category': category})
    counts.update(outputs=len(actual), paired_intents=len(intents), registered_cells=len(expected))
    counts['potential_request_slots_without_intent'] = 4243 - len(intents)
    assert sum(counts[k] for k in ('published_complete','published_unavailable','receipt_only_attempted','receipt_only_suppressed','unclassified_without_direct_q3_receipt')) == len(expected)
    return {'scope':'Failure-only closure, not missing Q3 outputs or financial outcomes',
            'source':claim['source'], 'claim_sha256':sha(claim_raw), 'terminal_sha256':sha(terminal_raw),
            'started_at':claim['started_at'], 'ended_at':terminal['ended_at'], 'terminal_status':'failed',
            'counts':dict(counts), 'raw_error_counts':dict(errors), 'denominator':rows,
            'decision':'Coordinator changed current HEAD; operational isolation failure. No restart or economic verdict.'}
if __name__ == '__main__':
    result = reconstruct()
    (BASE/'q3-closure-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'denominator'}))
