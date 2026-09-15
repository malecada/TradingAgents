"""Read-only reconstruction of the stopped R1 source denominator and charges.

Writes a separate closure report, never a run output or missing parsed result.
No network, financial calculation, source mutation or experiment restart.
"""
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'research/defi-depth-2026-09-15'
RUN = ROOT / 'research_runs/defi-depth-r1-20260915'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def reconstruct():
    claim_raw = (RUN / 'claim.json').read_bytes()
    terminal_raw = (RUN / 'failed.json').read_bytes()
    claim, terminal = json.loads(claim_raw), json.loads(terminal_raw)
    expected = claim['experiment']['cells']
    counts, errors, published, raw_days = Counter(), Counter(), {}, set()
    request_ids, response_ids, missing_response_ids = set(), set(), []
    paired, actual_names = set(), set()
    daily_dates = []
    for path in sorted((RUN / 'outputs').glob('*.json')):
        raw = path.read_bytes()
        assert terminal['output_sha256'][path.name] == digest(raw)
        actual_names.add(path.name)
        obj = json.loads(raw)
        if path.name.endswith('-attempt.json'):
            counts['durable_intents'] += 1
        if path.name.endswith('-receipt.json'):
            counts['durable_receipts'] += 1
        if path.name.endswith('-attempt.json') and obj.get('attempted'):
            counts['http_intents'] += 1
            payload = obj['request']
            members = payload if isinstance(payload, list) else [payload]
            counts['rpc_subcalls'] += len(members)
            for member in members:
                assert member['id'] not in request_ids
                request_ids.add(member['id'])
            receipt = path.name.replace('-attempt.json', '-receipt.json')
            if (RUN / 'outputs' / receipt).exists():
                paired.add(receipt)
        if path.name.endswith('-receipt.json') and obj.get('attempted'):
            counts['http_receipts'] += 1
            body = base64.b64decode(obj['body_base64'], validate=True)
            assert len(body) == obj['body_bytes'] and digest(body) == obj['body_sha256']
            counts['raw_bytes'] += len(body)
            counts['http_status_' + str(obj['http_status'])] += 1
            if path.name[:4].isdigit():
                raw_days.add(path.name[:10])
            members = obj['request'] if isinstance(obj['request'], list) else [obj['request']]
            intended = {m['id'] for m in members}
            if obj.get('error'):
                errors['transport: ' + obj['error']] += 1
            try:
                decoded = json.loads(body)
            except (ValueError, TypeError):
                decoded = []
            replies = decoded if isinstance(decoded, list) else [decoded]
            received = set()
            for reply in replies:
                assert reply['id'] in intended and reply['id'] not in received
                received.add(reply['id'])
                if 'error' in reply:
                    error = reply['error']
                    errors['rpc ' + str(error.get('code')) + ': ' + str(error.get('message'))] += 1
            response_ids.update(received)
            missing_response_ids.extend(sorted(intended - received))
        if path.name.endswith('-results.json'):
            daily_dates.append(obj['day']['date'])
            for cell in obj['cells']:
                assert cell['id'] not in published
                published[cell['id']] = cell['status']
        if path.name == 'chain-result.json':
            for cell in obj.get('cells', [obj]):
                # The actual chain output is a single cell object.
                if 'id' in cell:
                    assert cell['id'] not in published
                    published[cell['id']] = cell['status']
    assert actual_names == set(terminal['output_sha256'])
    assert set(published) <= set(expected)
    denominator = []
    for cell in expected:
        if cell in published:
            category = 'published_' + published[cell]
        elif cell[:10] in raw_days:
            category = 'raw_retained_no_published_parsed_cell'
        else:
            category = 'unattempted_after_provider_limit_stop'
        counts[category] += 1
        denominator.append({'id': cell, 'closure_category': category})
    counts['outputs'] = len(actual_names)
    counts['paired_http_receipts'] = len(paired)
    counts['published_daily_vectors'] = len(daily_dates)
    counts['registered_cells'] = len(expected)
    return {'scope': 'Failure-only source closure; no new outcomes or missing run-output reconstruction',
            'source': claim['source'], 'claim_sha256': digest(claim_raw),
            'terminal_sha256': digest(terminal_raw), 'started_at': claim['started_at'],
            'ended_at': terminal['ended_at'], 'terminal_status': 'failed',
            'counts': dict(counts), 'raw_error_counts': dict(errors),
            'received_rpc_response_ids': len(response_ids),
            'rpc_ids_without_response': missing_response_ids,
            'published_daily_first': min(daily_dates), 'published_daily_last': max(daily_dates),
            'raw_only_days': sorted(raw_days - set(daily_dates)), 'denominator': denominator,
            'decision': 'Observed repeated provider throttling; graceful owner stop, not elapsed-time or economic failure. No repair allowance remains; no restart.'}


if __name__ == '__main__':
    result = reconstruct()
    output = BASE / 'r1-closure-audit.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('denominator', 'rpc_ids_without_response')}))
