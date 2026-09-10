"""Offline, read-only preservation check after the fixed eighteen-cell correction."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = '0b7292148b9229eb58cf528b20948395819f9200'
REGISTRATION = '9cedcc42aafa2e555828306bdf32f5fd2a4908a2'
KEY = 'audit_factor_floor_2026_09_10'
LEDGER = 'data/predlab/trial_ledger.jsonl'
GATES = 'data/predlab/gates.json'
POLICY = 'docs/audit/corrections.jsonl'
FINDINGS = 'THESIS_FINDINGS.md'
TRACE = 'scripts/baseline_strategy_v2.py'
ALLOWED = {LEDGER, GATES, POLICY, FINDINGS, TRACE, 'CLAUDE.md'}
LEDGER_SHA = '710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791'
MANIFESTS = ('docs/funding-capture/verification/preservation-final.json',
             'docs/funding-capture/verification/final-manifest.json')

# Reuse the previously reviewed streaming/race-aware hash and exclusive writer.
_helper_path = ROOT / 'docs/funding-capture/verification/verify_preservation.py'
_spec = importlib.util.spec_from_file_location('prior_preservation', _helper_path)
_helper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helper)
inspect_file, require_match, write_new = _helper.inspect_file, _helper.require_match, _helper.write_new
git, local_path = _helper.git, _helper.local_path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def baseline_bytes(path, commit=BASELINE):
    return git('show', f'{commit}:{path}')


def append_suffix(before, after, label):
    if not after.startswith(before):
        raise ValueError(f'original prefix changed: {label}')
    return after[len(before):]


def gate_addition(before, after, expected):
    if set(after) - set(before) != {KEY} or set(before) - set(after):
        raise ValueError('gate keys changed beyond the single registered addition')
    if any(after[k] != v for k, v in before.items()) or after[KEY] != expected:
        raise ValueError('prior or registered gate object changed')


def safe_path(relative):
    path = local_path(relative)
    parts = Path(relative).parts
    if any(p in ('.venv', 'keys', 'apis') for p in parts) or path.name in ('.env', 'hf_token.txt'):
        raise ValueError(f'sensitive or excluded path requires separate review: {relative}')
    if path.is_symlink():
        raise ValueError(f'symlink not admitted: {relative}')
    return path


def verify(source_commit):
    if not re.fullmatch(r'[0-9a-f]{40}', source_commit):
        raise ValueError('source commit must be the full reviewed forty-hex commit')
    if git('rev-parse', '--show-object-format').strip() != b'sha1':
        raise ValueError('unsupported Git object format')
    frozen = {}
    for entry in git('ls-tree', '-r', '-l', '-z', BASELINE).split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        mode, kind, oid, size = meta.decode().split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError(f'unsupported baseline entry: {name.decode()}')
        frozen[name.decode()] = {'git_blob': oid, 'bytes': int(size)}
    if not frozen or not ALLOWED.issubset(frozen):
        raise ValueError('baseline inventory or exception paths missing')
    cache = {}
    def inspect(path):
        key = str(path)
        if key not in cache:
            cache[key] = inspect_file(path)
        return cache[key]
    inventory, changes = {}, []
    for name, expected in sorted(frozen.items()):
        actual = inspect(safe_path(name))
        if name in ALLOWED:
            changes.append({'path': name, 'baseline': expected, 'current': actual,
                            'changed': actual['git_blob'] != expected['git_blob']})
        else:
            require_match(actual, expected, name)
            inventory[name] = {'path': name, **actual}
    expected_gate = json.loads(baseline_bytes(GATES, REGISTRATION))[KEY]
    before_gates = json.loads(baseline_bytes(GATES))
    current_gates = json.loads(safe_path(GATES).read_text())
    gate_addition(before_gates, current_gates, expected_gate)
    trace_source = baseline_bytes(TRACE, source_commit)
    require_match(inspect(safe_path(TRACE)), {'sha256': digest(trace_source)}, TRACE)

    ledger_base = baseline_bytes(LEDGER)
    if len(ledger_base) != 428150 or digest(ledger_base) != LEDGER_SHA or len(ledger_base.splitlines()) != 730:
        raise ValueError('unexpected original ledger baseline')
    suffix = append_suffix(ledger_base, safe_path(LEDGER).read_bytes(), LEDGER)
    rows = [json.loads(line) for line in suffix.splitlines()]
    names = [c['name'] for c in expected_gate['cells']]
    if len(rows) != 18 or [r.get('cell') for r in rows] != names:
        raise ValueError('ledger does not append the registered eighteen cells in order')
    if any(r.get('experiment') != KEY or r.get('git_commit') != source_commit or
           r.get('window') != expected_gate['development_window'] for r in rows):
        raise ValueError('ledger source/experiment/window differs from registration')
    if len({r.get('trial_id') for r in rows}) != 18:
        raise ValueError('ledger appended duplicate identities')
    append_checks = []
    for name in (POLICY, FINDINGS):
        before = baseline_bytes(name)
        suffix = append_suffix(before, safe_path(name).read_bytes(), name)
        if not suffix.strip():
            raise ValueError(f'expected completion append absent: {name}')
        if name == POLICY:
            for line in suffix.splitlines():
                if line.strip():
                    json.loads(line)
        elif not re.search(rb'^## Section 95\b', suffix, re.M):
            raise ValueError('findings append lacks Section 95')
        append_checks.append({'path': name, 'original_bytes': len(before),
                              'original_sha256': digest(before), 'appended_bytes': len(suffix)})

    references, manifests, exclusions = 0, [], []
    for name in MANIFESTS:
        manifest = json.loads(safe_path(name).read_text())
        checked = 0
        for row in manifest['files']:
            filename = row['path']
            if Path(filename).name == '.ledger.lock':
                exclusions.append({'path': filename, 'reason': 'operational lock'})
                continue
            if filename in ALLOWED:
                # Prior manifest bytes must match the pinned baseline, even though
                # these explicitly permitted current paths may now have changed.
                original = baseline_bytes(filename)
                require_match({'sha256': digest(original), 'bytes': len(original),
                               'git_blob': frozen[filename]['git_blob']}, row, filename)
            else:
                actual = inspect(safe_path(filename))
                require_match(actual, row, filename)
                inventory[filename] = {'path': filename, **actual}
            checked += 1
        references += checked
        manifests.append({'path': name, 'sha256': inspect(safe_path(name))['sha256'],
                          'file_references_verified': checked})
    recovery = json.loads(safe_path('docs/data-recovery/verification/final-manifest.json').read_text())
    originals = recovery['referenced_external_original_inputs']
    if len(originals) != 222:
        raise ValueError('original external input denominator differs from 222')
    external = []
    roots = [ROOT.parent / name / 'data' for name in ('TradingAgents', 'TradingAgents-predlab')]
    for filename, sha in sorted(originals.items()):
        path = Path(filename)
        if path.is_symlink() or not any(path.resolve().is_relative_to(root.resolve()) for root in roots):
            raise ValueError('external original path escaped registered data roots')
        actual = inspect(path)
        require_match(actual, {'sha256': sha}, filename)
        external.append({'path': filename, **actual})
    provenance_name = 'docs/factor-correction/data-provenance.json'
    require_match(inspect(safe_path(provenance_name)),
                  {'sha256': expected_gate['pinned_files'][provenance_name]}, provenance_name)
    provenance = json.loads(safe_path(provenance_name).read_text())
    for row in provenance['inputs']:
        source = row['source']
        path = Path(source['path'])
        expected_path = ROOT.parent / 'TradingAgents/tradingagents/dataflows/data_cache' / f"{row['coin']}-crypto-ohlcv.csv"
        if path != expected_path or path.is_symlink() or row['coin'] not in ('bitcoin', 'ethereum'):
            raise ValueError('factor cache path escaped exact registered identities')
        actual = inspect(path)
        require_match(actual, source, str(path))
        external.append({'path': str(path), **actual})
    if len(external) != 224 or len({r['path'] for r in external}) != 224:
        raise ValueError('external input denominator differs from 222 plus 2')
    return {'status': 'PASS', 'baseline_commit': BASELINE, 'registration_commit': REGISTRATION,
            'reviewed_source_commit': source_commit, 'baseline_tracked_files': len(frozen),
            'baseline_byte_identical_files': len(frozen) - len(ALLOWED),
            'permitted_paths': changes, 'prior_local_artifacts_verified': len(inventory),
            'manifest_checks': manifests, 'manifest_file_references_verified': references,
            'operational_locks_excluded': exclusions, 'append_only_checks': append_checks,
            'prior_predlab_gate_entries_unchanged': len(before_gates), 'new_gate_keys': [KEY],
            'registered_gate_sha256': digest(json.dumps(expected_gate, sort_keys=True).encode()),
            'financial_ledger': {'original_bytes': 428150, 'original_rows': 730,
                                 'original_sha256': LEDGER_SHA, 'new_rows': 18, 'rows': 748,
                                 'sha256': inspect(safe_path(LEDGER))['sha256']},
            'external_original_inputs_verified': 222, 'factor_caches_verified': 2,
            'financial_statistics_computed': False, 'network_requests': 0,
            'old_evidence_write_operations': 0, 'files': list(inventory.values()),
            'external_inputs': external,
            'qualification': 'Local byte preservation only; no financial recalculation, semantic result review or Git retention certification.'}


class SelfTests(unittest.TestCase):
    def test_prefix_rewrite_rejected(self):
        with self.assertRaisesRegex(ValueError, 'prefix'):
            append_suffix(b'old\n', b'changed\nnew\n', 'fixture')
    def test_append_preserved(self):
        self.assertEqual(append_suffix(b'old\n', b'old\nnew\n', 'fixture'), b'new\n')
    def test_gate_edit_rejected(self):
        with self.assertRaisesRegex(ValueError, 'object'):
            gate_addition({'old': 1}, {'old': 2, KEY: 3}, 3)
    def test_extra_gate_rejected(self):
        with self.assertRaisesRegex(ValueError, 'keys'):
            gate_addition({'old': 1}, {'old': 1, KEY: 3, 'extra': 4}, 3)
    def test_gate_accepted(self):
        gate_addition({'old': 1}, {'old': 1, KEY: 3}, 3)
    def test_report_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            path.write_bytes(b'prior')
            with self.assertRaises(FileExistsError):
                write_new(path, {'status': 'PASS'})
            self.assertEqual(path.read_bytes(), b'prior')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--source-commit')
    parser.add_argument('--output', type=Path, default=OUT / 'preservation.json')
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=[__file__])
    if not args.source_commit:
        parser.error('--source-commit is required; use only after financial and documentation completion')
    output = args.output.resolve()
    if output.parent != OUT or output.suffix != '.json' or output.exists():
        parser.error('output must be a new JSON file in this verification directory')
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = verify(args.source_commit)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        result = {'status': 'FAIL', 'baseline_commit': BASELINE, 'error': f'{type(error).__name__}: {error}'}
    result.update(started_utc=started, verified_utc=datetime.now(timezone.utc).isoformat(),
                  script_sha256=inspect_file(Path(__file__))['sha256'])
    write_new(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('files', 'external_inputs')}, indent=2))
    raise SystemExit(result['status'] != 'PASS')
