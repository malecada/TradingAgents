"""Metadata-only preservation for the fixed factor risk-policy comparison."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = '3202d7982c47bb1472a8f3eb43a0851fd37b1480'
KEY = 'risk_policy_2026_09_10'
GATES = 'data/predlab/gates.json'
LEDGER = 'data/predlab/trial_ledger.jsonl'
LEDGER_BYTES = 569325
LEDGER_ROWS = 748
LEDGER_SHA = '4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601'
ENGINE = 'scripts/baseline_strategy_v2.py'
ENGINE_ARCHIVE = 'docs/risk-policy-2026-09-10/original/baseline_strategy_v2.py'
APPEND_ONLY = ('THESIS_FINDINGS.md', 'docs/audit/corrections.jsonl')
MUTABLE = {GATES, LEDGER, ENGINE, *APPEND_ONLY}
EXTERNAL_MANIFEST = 'docs/diagnostics-2026-09-10/verification/baseline-input-manifest.json'

_spec = importlib.util.spec_from_file_location('prior_risk_policy_preservation',
    ROOT/'docs/diagnostics-2026-09-10/verification/verify_preservation.py')
_prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prior)
inspect_file, require_match, write_new, git = (_prior.inspect_file,
    _prior.require_match, _prior.write_new, _prior.git)
safe_local, check_tree, check_external = _prior.safe_local, _prior.check_tree, _prior.check_external
append_suffix, merge_receipts = _prior.append_suffix, _prior.merge_receipts


def digest(data):
    return hashlib.sha256(data).hexdigest()


def baseline_bytes(path, commit=BASELINE):
    return git('show', f'{commit}:{path}')


def gate_additions(before, after, registered=None):
    additions = set(after)-set(before)
    if set(before)-set(after) or additions-{KEY}:
        raise ValueError('gate keys changed beyond the single declared addition')
    if any(after[key] != value for key, value in before.items()):
        raise ValueError('prior gate object changed')
    if registered is not None and (additions != {KEY} or after.get(KEY) != registered):
        raise ValueError('registered risk-policy gate missing or changed')
    return sorted(additions)


def check_engine(root, original):
    archive = safe_local(root, ENGINE_ARCHIVE)
    actual_archive = inspect_file(archive)
    if actual_archive['sha256'] != digest(original) or actual_archive['bytes'] != len(original):
        raise ValueError('original engine archive differs from fixed baseline bytes')
    current = inspect_file(safe_local(root, ENGINE))
    return {'path': ENGINE, 'baseline_commit': BASELINE, 'baseline_bytes': len(original),
            'baseline_sha256': digest(original), 'current': current,
            'archive': {'path': ENGINE_ARCHIVE, **actual_archive},
            'archive_byte_identical': True, 'changed': current['sha256'] != digest(original),
            'qualification': 'This is the sole permitted existing executable edit. '
                'Hook semantics and control parity require separate source/result review.'}


def ledger_prefix(before, after, *, phase):
    suffix = append_suffix(before, after, 'financial ledger')
    if not before.endswith(b'\n') or (suffix and not suffix.endswith(b'\n')):
        raise ValueError('financial ledger records require newline boundaries')
    lines = suffix.splitlines()
    if any(not line.strip() for line in lines):
        raise ValueError('blank financial ledger append record')
    if phase == 'baseline' and suffix:
        raise ValueError('financial ledger must be unchanged before execution')
    if phase == 'final' and len(lines) != 72:
        raise ValueError('final financial ledger requires exactly 72 appended records')
    if phase not in ('baseline', 'final'):
        raise ValueError('unknown preservation phase')
    rows = [json.loads(line) for line in lines]
    return {'path': LEDGER, 'prefix_bytes': len(before), 'prefix_sha256': digest(before),
            'prefix_rows': len(before.splitlines()), 'prefix_byte_identical': True,
            'current_bytes': len(after), 'current_sha256': digest(after),
            'current_rows': len(before.splitlines())+len(lines), 'new_rows': len(lines),
            'append_sha256': digest(suffix), '_rows': rows}


def check_ledger_cells(rows, gate):
    """Validate identities/status denominators, without interpreting numerical metrics."""
    cells = gate['cells']
    variants, coins = gate['variants'], gate['coins']
    if (len(rows) != 72 or len(cells) != 72 or gate['expected_identities'] != 72
            or len({c['id'] for c in cells}) != 72
            or set(variants) != {'primary','zero_execution','double_execution','zero_funding'}
            or coins != ['bitcoin','ethereum']):
        raise ValueError('registered nested identity denominator changed')
    counts = {kind: {'complete': 0, 'unavailable': 0}
              for kind in ('cell','variant','index','sleeve','shadow')}
    def status(item, where, kind):
        if not isinstance(item, dict) or item.get('status') not in ('complete','unavailable'):
            raise ValueError(f'missing or unknown status: {where}')
        value = item['status']
        if value == 'unavailable' and not (isinstance(item.get('reason'), str) and item['reason'].strip()):
            raise ValueError(f'unavailable status requires an explicit reason: {where}')
        counts[kind][value] += 1
        return value
    for row, cell in zip(rows, cells, strict=True):
        expected_config = {k:cell[k] for k in ('configuration','arm','sizing','reentry')}
        if (row.get('experiment') != KEY or row.get('cell') != cell['id']
                or row.get('config') != expected_config):
            raise ValueError(f'ledger identity/order/config differs from registered cell: {cell["id"]}')
        metrics = row.get('metrics', {})
        cs = status(metrics, cell['id'], 'cell')
        nested = metrics.get('variants')
        if not isinstance(nested, dict) or set(nested) != set(variants):
            raise ValueError(f'missing or extra variant identity: {cell["id"]}')
        required = []
        for variant, item in nested.items():
            where = f'{cell["id"]}/{variant}'
            vs = status(item, where, 'variant')
            sleeves = item.get('sleeves')
            if not isinstance(sleeves, dict) or set(sleeves) != set(coins):
                raise ValueError(f'missing or extra sleeve identity: {where}')
            ss = [status(sleeves[coin], f'{where}/{coin}', 'sleeve') for coin in coins]
            ix = status(item.get('index'), f'{where}/index', 'index')
            if ix == 'complete' and 'unavailable' in ss:
                raise ValueError(f'incomplete sleeves promoted to complete index: {where}')
            if vs == 'complete' and 'unavailable' in [*ss, ix]:
                raise ValueError(f'incomplete children promoted to complete variant: {where}')
            required.append(vs)
        required.append(status(metrics.get('log_shadow'), f'{cell["id"]}/log_shadow', 'shadow'))
        if cs == 'complete' and 'unavailable' in required:
            raise ValueError(f'incomplete children promoted to complete cell: {cell["id"]}')
    return {'identities': len(rows), 'ordered_cell_ids': [c['id'] for c in cells],
            **{f'{kind}_statuses': count for kind,count in counts.items()},
            'qualification': 'Identity and explicit availability only; no numerical metric validation.'}


def tracked_baseline():
    if git('rev-parse', '--show-object-format').strip() != b'sha1':
        raise ValueError('unsupported Git object format')
    frozen = {}
    for entry in git('ls-tree', '-r', '-l', '-z', BASELINE).split(b'\0'):
        if not entry: continue
        meta, name = entry.split(b'\t', 1)
        mode, kind, oid, size = meta.decode().split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError(f'unsupported baseline entry: {name.decode()}')
        frozen[name.decode()] = {'git_blob': oid, 'bytes': int(size)}
    if not (MUTABLE | {EXTERNAL_MANIFEST}).issubset(frozen):
        raise ValueError('baseline inventory does not contain every required input')
    return frozen


def verify(*, registration_commit=None, phase='baseline'):
    frozen = tracked_baseline()
    files = check_tree(ROOT, frozen, MUTABLE)
    old_gate = json.loads(baseline_bytes(GATES))
    current_gate = json.loads(safe_local(ROOT, GATES).read_text())
    registered = None
    if registration_commit is not None:
        if not re.fullmatch(r'[0-9a-f]{40}', registration_commit):
            raise ValueError('registration commit requires the full forty-hex identifier')
        registered = json.loads(baseline_bytes(GATES, registration_commit))[KEY]
    additions = gate_additions(old_gate, current_gate, registered)
    if phase == 'final' and registered is None:
        raise ValueError('final verification requires exact committed registration')
    appends = []
    for name in APPEND_ONLY:
        before = baseline_bytes(name); after = safe_local(ROOT, name).read_bytes()
        suffix = append_suffix(before, after, name)
        if name.endswith('.jsonl'):
            for line in suffix.splitlines():
                if line.strip(): json.loads(line)
        appends.append({'path': name, 'baseline_bytes': len(before), 'baseline_sha256': digest(before),
                        'appended_bytes': len(suffix), 'current_sha256': digest(after)})
    before = baseline_bytes(LEDGER)
    if len(before) != LEDGER_BYTES or len(before.splitlines()) != LEDGER_ROWS or digest(before) != LEDGER_SHA:
        raise ValueError('fixed financial-ledger baseline identity mismatch')
    ledger = ledger_prefix(before, safe_local(ROOT, LEDGER).read_bytes(), phase=phase)
    if phase == 'final':
        ledger['nested_denominators'] = check_ledger_cells(ledger['_rows'], registered)
    ledger.pop('_rows')
    engine = check_engine(ROOT, baseline_bytes(ENGINE))
    receipts = json.loads(baseline_bytes(EXTERNAL_MANIFEST))['external_inputs']
    if len(receipts) != 270 or len({r['path'] for r in receipts}) != 270:
        raise ValueError('original external input denominator differs from 270')
    external = check_external(receipts)
    gates = [{'path': name, 'entries': len(json.loads(baseline_bytes(name)))}
             for name in sorted(frozen) if Path(name).name == 'gates.json']
    return {'status': 'PASS', 'phase': phase, 'baseline_commit': BASELINE,
            'registration_commit': registration_commit,
            'baseline_tracked_files': len(frozen), 'baseline_byte_identical_files': len(files),
            'permitted_mutable_paths': sorted(MUTABLE), 'engine_preservation': engine,
            'prior_gate_files': gates, 'prior_gate_objects_unchanged': sum(r['entries'] for r in gates),
            'new_gate_keys': additions, 'registered_gate_checked': registered is not None,
            'registered_gate_sha256': digest(json.dumps(registered,sort_keys=True,separators=(',', ':')).encode()) if registered is not None else None,
            'append_only_checks': appends, 'financial_ledger': ledger,
            'external_original_inputs_verified': len(external), 'external_inputs': external,
            'files': files, 'baseline_git_entries': [{'path': name, **meta} for name,meta in sorted(frozen.items())],
            'financial_statistics_computed': False, 'network_requests': 0, 'old_evidence_write_operations': 0,
            'qualification': 'Prior byte preservation and metadata identity only; external originals are '
              'opaque hash streams. New economic outputs require independent numerical review. '
              'The one permitted existing engine hook is not authenticated as correct by its exception. '
              'Final Git inclusion and execution admission require separate verification.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['baseline','final'], default='baseline')
    parser.add_argument('--registration-commit')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = (args.output or OUT/('baseline-input-manifest.json' if args.phase == 'baseline' else 'preservation-final.json')).absolute()
    if output.parent.resolve() != OUT or output.suffix != '.json' or output.exists():
        parser.error('output must be a new JSON file inside this verification directory')
    started = datetime.now(timezone.utc).isoformat()
    result = verify(registration_commit=args.registration_commit, phase=args.phase)
    result.update(started_utc=started, verified_utc=datetime.now(timezone.utc).isoformat(),
                  script_sha256=inspect_file(Path(__file__))['sha256'])
    write_new(output, result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','external_inputs','baseline_git_entries')},indent=2))
