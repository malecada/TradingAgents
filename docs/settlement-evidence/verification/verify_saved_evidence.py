"""Offline verification of documentary artifacts; no fetch or financial replay."""
from collections import Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'data/settlement-evidence/2026-09-10'
OUT = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def git_bytes(ref, rel):
    return subprocess.check_output(['git', 'show', f'{ref}:{rel}'], cwd=ROOT)


def check_index(case, archive, checksum, api, day, expected_api):
    folder = DATA / case
    assert digest(folder / archive) == (folder / checksum).read_text().split()[0]
    with zipfile.ZipFile(folder / archive) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == 1
        rows = list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())))
    if not rows[0][0].isdigit():
        rows = rows[1:]
    assert len(rows) == 1440
    first = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() * 1000)
    assert [int(r[0]) for r in rows] == list(range(first, first + 86400000, 60000))
    lookup = {int(r[0]): r for r in rows}
    for r in rows:
        assert len(r) == 12 and int(r[6]) == int(r[0]) + 59999
        o, h, l, c = map(Decimal, r[1:5])
        assert 0 < l <= min(o, c) <= max(o, c) <= h
    observed = json.loads((folder / api).read_text())
    assert len(observed) == expected_api
    for r in observed:
        assert list(map(lambda v: Decimal(str(v)), r)) == list(map(Decimal, lookup[int(r[0])]))
    return {'case': case, 'archive_rows': len(rows), 'api_rows': len(observed),
            'all_twelve_fields_agree': True, 'provider_checksum_valid': True,
            'complete_event_day_minute_clock': True, 'actual_settlement_value_inferred': False}


def main():
    cases, events = [], []
    registration = subprocess.check_output(['git', 'rev-parse', '506373e'], cwd=ROOT, text=True).strip()
    committed_at = datetime.fromtimestamp(int(subprocess.check_output(
        ['git', 'show', '-s', '--format=%ct', registration], cwd=ROOT)), tz=timezone.utc)
    for name in ['bzrx', 'luna', 'bnx']:
        p = DATA / name / 'manifest.json'
        m = json.loads(p.read_text())
        rows = m.get('requests', m.get('responses'))
        nbytes, statuses = 0, Counter()
        for r in rows:
            filename = r.get('body_file', r.get('file'))
            n = r.get('body_bytes', r.get('response_bytes', r.get('bytes')))
            sha = r.get('body_sha256', r.get('sha256'))
            body = p.parent / filename
            assert body.stat().st_size == n and digest(body) == sha, body
            status = r.get('status', r.get('http_status'))
            statuses[str(status) if status is not None else 'timeout'] += 1
            start = datetime.fromisoformat(r.get('request_started_utc', r.get('requested_utc')))
            end = datetime.fromisoformat(r['retrieved_utc'])
            assert committed_at <= start <= end
            assert not r.get('authenticated', False)
            events.extend([(start, 1), (end, -1)])
            nbytes += n
        assert nbytes == m.get('downloaded_bytes', m.get('total_body_bytes'))
        assert nbytes <= 25000000
        for r in m.get('derived_artifacts', []):
            assert digest(p.parent / r['file']) == r['sha256']
        for r in m.get('derived_extractions', []):
            assert digest(p.parent / r['output']) == r['sha256']
            assert digest(p.parent / r['source']) == r['source_sha256']
        cases.append({'case': name, 'manifest': str(p.relative_to(ROOT)), 'manifest_sha256': digest(p),
                      'requests': len(rows), 'body_bytes': nbytes, 'statuses': dict(statuses)})
    running = maximum = 0
    for _, change in sorted(events):
        running += change
        maximum = max(maximum, running)
    assert running == 0 and maximum <= 3
    assert sum(c['body_bytes'] for c in cases) <= 100000000

    price_checks = [
        check_index('luna', 'archive-index-20220512.zip', 'archive-index-20220512.CHECKSUM',
                    'index-price-preclose-60m.json', '2022-05-12', 60),
        check_index('bnx', 'vision-bnx-index-20250317-zip.bin', 'vision-bnx-index-20250317-checksum.bin',
                    'index-final-window-api.bin', '2025-03-17', 31),
    ]
    previous = json.loads((ROOT / 'docs/data-recovery/verification/final-manifest.json').read_text())
    prior_artifacts = 0
    for r in previous['files']:
        if Path(r['path']).name == '.ledger.lock':
            continue
        assert digest(ROOT / r['path']) == r['sha256'], r['path']
        prior_artifacts += 1
    original_hashes = previous['referenced_external_original_inputs']
    for path, sha in original_hashes.items():
        assert digest(path) == sha, path
    for r in previous['prior_five_results'] + [previous['bounded_correction_result']]:
        assert digest(ROOT / r['path']) == r['sha256']
    gate_files = []
    for r in previous['prior_gate_files']:
        rel = r['path']
        old = json.loads(git_bytes('b62b3d9', rel))
        now = json.loads((ROOT / rel).read_text())
        assert all(now[k] == v for k, v in old.items()), rel
        gate_files.append({'path': rel, 'prior_entries_unchanged': len(old)})
    gate_path = 'data/predlab/gates.json'
    gate_key = 'audit_settlement_evidence_2026_09_10'
    gate = json.loads((ROOT / gate_path).read_text())[gate_key]
    assert gate == json.loads(git_bytes(registration, gate_path))[gate_key]
    source_checks = json.loads((OUT / 'source-inspection.json').read_text())['files']
    for r in source_checks:
        assert digest(ROOT / r['path']) == r['sha256']
        assert (ROOT / r['path']).read_bytes() == git_bytes(r['unchanged_from'], r['path'])
    ledger = ROOT / 'data/predlab/trial_ledger.jsonl'
    assert ledger.read_bytes() == git_bytes('b62b3d9', 'data/predlab/trial_ledger.jsonl')
    old_policy = git_bytes('b62b3d9', 'docs/audit/corrections.jsonl')
    assert (ROOT / 'docs/audit/corrections.jsonl').read_bytes().startswith(old_policy)
    inventory = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': digest(p)}
                 for p in sorted(DATA.rglob('*')) if p.is_file()]
    result = {
        'status': 'PASS', 'verified_utc': datetime.now(timezone.utc).isoformat(),
        'verification': 'Parent independent offline artifact, clock and preservation checks',
        'registration_commit': registration, 'gate_key': gate_key,
        'gate_sha256': hashlib.sha256(json.dumps(gate, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'case_receipts': cases, 'direct_requests': sum(c['requests'] for c in cases),
        'response_body_bytes': sum(c['body_bytes'] for c in cases),
        'max_overlapping_recorded_direct_requests': maximum,
        'price_integrity_checks': price_checks,
        'prior_recovery_and_replay_artifacts_unchanged': prior_artifacts,
        'external_original_file_hashes_unchanged': len(original_hashes),
        'prior_gate_files': gate_files, 'unchanged_source_files': len(source_checks),
        'financial_ledger': {'bytes': ledger.stat().st_size, 'sha256': digest(ledger), 'new_rows': 0},
        'prior_correction_prefix_unchanged': True,
        'prior_correction_prefix_sha256': hashlib.sha256(old_policy).hexdigest(),
        'financial_runs': 0, 'financial_statistics_computed': False,
        'exact_settlement_values_admitted': 0,
        'tests_rerun': False, 'accounting_source_changed': False,
        'artifact_file_count': len(inventory), 'artifact_bytes': sum(r['bytes'] for r in inventory),
        'files': inventory,
        'verification_script_sha256': digest(__file__),
    }
    (OUT / 'final-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
