"""Preserve pre-diagnostic evidence; only write a new metadata-only JSON report."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = 'a3afb85040fd13d65fdc69908a32054bf9dc173d'
KEYS = ('audit_saved_forecast_inference_2026_09_10', 'audit_factor_risk_2026_09_10')
GATES = 'data/predlab/gates.json'
LEDGER = 'data/predlab/trial_ledger.jsonl'
APPEND_ONLY = ('THESIS_FINDINGS.md', 'docs/audit/corrections.jsonl')
MUTABLE = {GATES, *APPEND_ONLY}
FACTOR_RECEIPTS = 'docs/factor-correction/verification/preservation.json'
FORECAST_RESULT = 'data/predlab/audit_correction_2026_09_09/result.json'
FACTOR_RESULT = 'data/factor-correction/2026-09-10/results/result.json'
MANIFEST = OUT / 'baseline-input-manifest.json'
LEDGER_SHA = '4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601'

# Existing reviewed implementation hashes streams and detects file replacement
# or mutation during a read. Importing it performs no verification or writes.
_helper_path = ROOT / 'docs/funding-capture/verification/verify_preservation.py'
_spec = importlib.util.spec_from_file_location('prior_diagnostic_preservation', _helper_path)
_helper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helper)
inspect_file, require_match, write_new, git = (
    _helper.inspect_file, _helper.require_match, _helper.write_new, _helper.git)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def baseline_bytes(path, commit=BASELINE):
    return git('show', f'{commit}:{path}')


def safe_local(root, relative):
    root, relative = Path(root).resolve(), Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError(f'nonlocal evidence path: {relative}')
    excluded = {'.git', '.venv', 'keys', 'apis'}
    if excluded.intersection(relative.parts) or relative.name in {'.env', 'hf_token.txt'}:
        raise ValueError(f'excluded evidence path: {relative}')
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'evidence escapes checkout: {relative}')
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise ValueError(f'symlink not admitted: {relative}')
        cursor = cursor.parent
    return path


def check_tree(root, frozen, mutable):
    checked = []
    for name, expected in sorted(frozen.items()):
        if name in mutable:
            continue
        actual = inspect_file(safe_local(root, name))
        require_match(actual, expected, name)
        checked.append({'path': name, **actual})
    return checked


def gate_additions(before, after, expected=None):
    additions = set(after) - set(before)
    if set(before) - set(after) or additions - set(KEYS):
        raise ValueError('gate keys changed beyond the two declared additions')
    if any(after[key] != value for key, value in before.items()):
        raise ValueError('prior gate object changed')
    if expected is not None and (set(expected) != set(KEYS) or additions != set(KEYS)
                                 or any(after.get(k) != v for k, v in expected.items())):
        raise ValueError('registered gate missing or changed')
    return sorted(additions)


def append_suffix(before, after, label):
    if not after.startswith(before):
        raise ValueError(f'original prefix changed: {label}')
    return after[len(before):]


def require_ledger(after, before):
    if after != before:
        raise ValueError('financial ledger changed; diagnostic rows belong in separate forensic ledgers')
    rows = [json.loads(line) for line in after.splitlines() if line.strip()]
    return {'path': LEDGER, 'bytes': len(after), 'sha256': digest(after),
            'rows': len(rows), 'new_rows': 0, 'byte_identical': True}


def merge_receipts(first, second):
    merged = {}
    for row in first:
        if row['path'] in merged:
            raise ValueError(f'duplicate original receipt: {row["path"]}')
        merged[row['path']] = dict(row)
    for path, sha in second.items():
        if path in merged and merged[path]['sha256'] != sha:
            raise ValueError(f'conflicting original receipt: {path}')
        merged.setdefault(path, {'path': path, 'sha256': sha})
    return [merged[path] for path in sorted(merged)]


def tracked_baseline():
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
    if not frozen or not (MUTABLE | {LEDGER, FACTOR_RECEIPTS, FORECAST_RESULT,
                                    FACTOR_RESULT}).issubset(frozen):
        raise ValueError('baseline inventory is empty or incomplete')
    return frozen


def original_receipts():
    factor = json.loads(baseline_bytes(FACTOR_RECEIPTS))['external_inputs']
    forecast = json.loads(baseline_bytes(FORECAST_RESULT))['input_sha256']
    if len(factor) != 224 or len(forecast) != 46:
        raise ValueError('original receipt denominators differ from 224 plus 46')
    merged = merge_receipts(factor, forecast)
    if len(merged) != 270:
        raise ValueError('original receipt union differs from 270 distinct files')
    return merged


def check_external(rows):
    roots = tuple(ROOT.parent / name / 'data' for name in ('TradingAgents', 'TradingAgents-predlab'))
    caches = {ROOT.parent / 'TradingAgents/tradingagents/dataflows/data_cache' /
              f'{coin}-crypto-ohlcv.csv' for coin in ('bitcoin', 'ethereum')}
    checked = []
    for row in rows:
        path = Path(row['path'])
        if not path.is_absolute() or '..' in path.parts or path.is_symlink():
            raise ValueError(f'invalid original input identity: {path}')
        if not (any(path.resolve().is_relative_to(root.resolve()) for root in roots)
                or path in caches):
            raise ValueError(f'original input escaped registered roots: {path}')
        if any(part in {'keys', 'apis', '.venv'} for part in path.parts) or path.name in {'.env', 'hf_token.txt'}:
            raise ValueError(f'excluded original input: {path}')
        actual = inspect_file(path)
        require_match(actual, row, str(path))
        checked.append({'path': str(path), **actual})
    return checked


def diagnostic_inputs():
    forecast = json.loads(baseline_bytes(FORECAST_RESULT))
    factor = json.loads(baseline_bytes(FACTOR_RESULT))
    vectors, baselines, traces = [], [], []
    original_root = ROOT.parent / 'TradingAgents-predlab/data/predlab/forecasts/predlab_p2_ml'
    for cell in forecast['enet']:
        stem = cell['cell'].replace('|', '_')
        name = stem + '_enet.parquet'
        vectors.append({'cell': cell['cell'], 'path': str(Path(FORECAST_RESULT).parent / name),
                        'sha256': forecast['output_sha256'][name], 'saved_rows': cell['n_saved'],
                        'scoreable_rows_previously_reported': cell['n_scoreable']})
        path = str(original_root / stem / (cell['baseline'] + '.parquet'))
        baselines.append({'cell': cell['cell'], 'baseline': cell['baseline'], 'path': path,
                          'sha256': forecast['input_sha256'][path]})
    for cell in factor['cells']:
        for coin in ('bitcoin', 'ethereum'):
            name = f'{cell["id"]}-primary-{coin}-trace.parquet'
            traces.append({'cell': cell['id'], 'coin': coin,
                           'path': str(Path(FACTOR_RESULT).parent / name),
                           'sha256': factor['output_sha256'][name]})
    if len(vectors) != 16 or len(baselines) != 16 or len(traces) != 36:
        raise ValueError('diagnostic input scope differs from 16 vectors, 16 baselines and 36 primary traces')
    return {'forecast_vectors': vectors, 'forecast_baselines': baselines,
            'primary_factor_traces': traces,
            'parent_results': [{'path': name, 'sha256': digest(baseline_bytes(name))}
                               for name in (FORECAST_RESULT, FACTOR_RESULT)]}


def verify(registration_commit=None):
    frozen = tracked_baseline()
    files = check_tree(ROOT, frozen, MUTABLE)
    expected = None
    if registration_commit is not None:
        if not re.fullmatch(r'[0-9a-f]{40}', registration_commit):
            raise ValueError('registration commit must be the full forty-hex commit')
        registered = json.loads(baseline_bytes(GATES, registration_commit))
        expected = {key: registered[key] for key in KEYS}
    before_gates = json.loads(baseline_bytes(GATES))
    gate_bytes = safe_local(ROOT, GATES).read_bytes()
    added = gate_additions(before_gates, json.loads(gate_bytes), expected)
    appends = []
    for name in APPEND_ONLY:
        before, after = baseline_bytes(name), safe_local(ROOT, name).read_bytes()
        suffix = append_suffix(before, after, name)
        if name.endswith('.jsonl'):
            for line in suffix.splitlines():
                if line.strip():
                    json.loads(line)
        appends.append({'path': name, 'original_bytes': len(before), 'original_sha256': digest(before),
                        'appended_bytes': len(suffix), 'current_sha256': digest(after)})
    ledger_before = baseline_bytes(LEDGER)
    if len(ledger_before) != 569325 or digest(ledger_before) != LEDGER_SHA:
        raise ValueError('unexpected fixed financial ledger baseline')
    ledger = require_ledger(safe_local(ROOT, LEDGER).read_bytes(), ledger_before)
    if ledger['rows'] != 748:
        raise ValueError('fixed financial ledger denominator differs from 748')
    external = check_external(original_receipts())
    inputs = diagnostic_inputs()
    gates = [{'path': name, 'entries': len(json.loads(baseline_bytes(name)))}
             for name in sorted(frozen) if Path(name).name == 'gates.json']
    # Baseline manifest contains immutable declarations, not a snapshot of mutable
    # gate/completion files. New registrations are checked against their commit.
    baseline_entries = [{'path': name, **meta} for name, meta in sorted(frozen.items())]
    return {'status': 'PASS', 'baseline_commit': BASELINE,
            'registration_commit': registration_commit, 'baseline_tracked_files': len(frozen),
            'baseline_byte_identical_files': len(files), 'permitted_mutable_paths': sorted(MUTABLE),
            'prior_gate_files': gates, 'prior_gate_objects_unchanged': sum(r['entries'] for r in gates),
            'new_gate_keys': added, 'registered_gates_checked': registration_commit is not None,
            'registered_gate_sha256': {key: digest(json.dumps(value, sort_keys=True,
                separators=(',', ':')).encode()) for key, value in (expected or {}).items()},
            'append_only_checks': appends, 'financial_ledger': ledger,
            'external_original_inputs_verified': len(external), 'external_inputs': external,
            'diagnostic_input_scope': inputs, 'files': files, 'baseline_git_entries': baseline_entries,
            'financial_statistics_computed': False, 'network_requests': 0,
            'old_evidence_write_operations': 0,
            'qualification': 'Byte preservation and declared input identities only. Original files are opaque '
              'hash streams, not financial inputs consumed by this verifier. Diagnostic outputs and separate '
              'forensic ledgers require independent result review; this report does not certify Git retention.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-baseline', action='store_true')
    parser.add_argument('--registration-commit')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.capture_baseline and not args.registration_commit:
        parser.error('choose --capture-baseline or provide --registration-commit')
    output = (args.output or (MANIFEST if args.capture_baseline else OUT / 'preservation-final.json')).absolute()
    if output.parent.resolve() != OUT or output.suffix != '.json' or output.exists():
        parser.error('output must be a new JSON file inside this verification directory')
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = verify(args.registration_commit)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        result = {'status': 'FAIL', 'baseline_commit': BASELINE, 'error': f'{type(error).__name__}: {error}'}
    result.update(started_utc=started, verified_utc=datetime.now(timezone.utc).isoformat(),
                  script_sha256=inspect_file(Path(__file__))['sha256'])
    write_new(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ('files', 'external_inputs', 'baseline_git_entries', 'diagnostic_input_scope')}, indent=2))
    raise SystemExit(result['status'] != 'PASS')
