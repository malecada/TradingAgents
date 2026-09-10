"""Offline preservation checks; only a new verification report is written."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = '78c89363a402edad752732396a47770b3d13fb1b'
FROZEN = ('data', 'docs/audit', 'docs/reevaluation', 'docs/data-recovery',
          'docs/settlement-evidence', 'docs/event-accounting', 'docs/operations')
MANIFESTS = tuple(f'docs/{name}/verification/final-manifest.json' for name in
                  ('data-recovery', 'settlement-evidence', 'event-accounting', 'operations'))
EXTERNAL_ROOTS = tuple(ROOT.parent / name / 'data' for name in
                       ('TradingAgents', 'TradingAgents-predlab'))
LEDGER = 'data/predlab/trial_ledger.jsonl'
LEDGER_SHA = '710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791'


def inspect_file(path):
    path = Path(path)
    before = path.stat()
    sha = hashlib.sha256()
    blob = hashlib.sha1(f'blob {before.st_size}\0'.encode())
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
            blob.update(chunk)
    after = path.stat()
    stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if stamp(before) != stamp(after):
        raise ValueError(f'file changed during hashing: {path}')
    return {'bytes': before.st_size, 'sha256': sha.hexdigest(), 'git_blob': blob.hexdigest()}


def require_match(actual, expected, label):
    for key in ('sha256', 'bytes', 'git_blob'):
        if key in expected and actual[key] != expected[key]:
            raise ValueError(f'{key} mismatch: {label}')


def write_new(path, payload):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(payload, indent=2, sort_keys=True) + '\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def local_path(relative):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'nonlocal evidence path: {relative}')
    full = ROOT / path
    if not full.resolve().is_relative_to(ROOT):
        raise ValueError(f'evidence escapes checkout: {relative}')
    return full


def verify():
    if git('rev-parse', '--show-object-format').strip() != b'sha1':
        raise ValueError('unsupported Git object format')
    frozen = {}
    for entry in git('ls-tree', '-r', '-l', '-z', BASELINE, '--', *FROZEN).split(b'\0'):
        if not entry:
            continue
        meta, raw_path = entry.split(b'\t', 1)
        mode, kind, oid, size = meta.decode().split()
        relative = raw_path.decode()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError(f'unsupported prior evidence entry: {relative}')
        frozen[relative] = {'git_blob': oid, 'bytes': int(size)}
    if not frozen:
        raise ValueError('baseline evidence tree is empty')

    cache = {}
    def inspect(path):
        key = str(path)
        if key not in cache:
            cache[key] = inspect_file(path)
        return cache[key]

    inventory = {}
    for relative, expected in sorted(frozen.items()):
        actual = inspect(local_path(relative))
        require_match(actual, expected, relative)
        inventory[relative] = {'path': relative, **actual}

    manifests, manifest_checks, omitted, locks = {}, [], [], []
    reference_checks = 0
    for relative in MANIFESTS:
        # Its baseline Git blob was independently verified before trusting paths.
        if relative not in frozen:
            raise ValueError(f'manifest is absent from baseline: {relative}')
        manifest = json.loads(local_path(relative).read_text())
        manifests[relative] = manifest
        verified = 0
        for row in manifest['files']:
            filename = row['path']
            if Path(filename).name == '.ledger.lock':
                locks.append({'path': filename, 'reason': 'operational lock; not immutable evidence'})
                continue
            # Historic operational source versions remain recorded in their old
            # manifests; current funding implementation may intentionally differ.
            event_source = (relative == MANIFESTS[2] and filename in
                            ('tradingagents/event_accounting.py', 'tests/test_event_accounting.py'))
            if filename not in frozen and not event_source:
                omitted.append({'manifest': relative, 'path': filename,
                                'reason': 'historical operational source/reference; current bytes not asserted'})
                continue
            actual = inspect(local_path(filename))
            require_match(actual, row, filename)
            inventory[filename] = {'path': filename, **actual}
            verified += 1
        reference_checks += verified
        manifest_checks.append({'path': relative, 'sha256': inspect(local_path(relative))['sha256'],
                                'file_references_verified': verified})

    recovery = manifests[MANIFESTS[0]]
    external = []
    for filename, expected in sorted(recovery['referenced_external_original_inputs'].items()):
        path = Path(filename)
        if not any(path.resolve().is_relative_to(root.resolve()) for root in EXTERNAL_ROOTS):
            raise ValueError(f'external input is outside original data roots: {filename}')
        actual = inspect(path)
        require_match(actual, {'sha256': expected}, filename)
        external.append({'path': filename, 'bytes': actual['bytes'], 'sha256': actual['sha256']})

    prior_results = recovery['prior_five_results'] + [recovery['bounded_correction_result']]
    for row in prior_results:
        require_match(inspect(local_path(row['path'])), row, row['path'])
    gates = []
    for filename in sorted(frozen):
        if Path(filename).name == 'gates.json':
            entries = json.loads(local_path(filename).read_text())
            gates.append({'path': filename, 'entries': len(entries),
                          'sha256': inspect(local_path(filename))['sha256'],
                          'byte_identical_to_baseline': True})
    if not gates:
        raise ValueError('no prior gate files found')
    ledger = inspect(local_path(LEDGER))
    require_match(ledger, {'sha256': LEDGER_SHA, 'bytes': 428150}, LEDGER)
    ledger_rows = [json.loads(line) for line in local_path(LEDGER).read_text().splitlines() if line.strip()]
    return {
        'status': 'PASS', 'baseline_commit': BASELINE,
        'scope': 'Byte preservation of prior evidence and original inputs; no financial reconstruction.',
        'baseline_evidence_paths': list(FROZEN), 'baseline_evidence_files_verified': len(frozen),
        'prior_local_artifacts_verified': len(inventory),
        'prior_local_artifact_bytes': sum(row['bytes'] for row in inventory.values()),
        'manifest_checks': manifest_checks, 'manifest_file_references_verified': reference_checks,
        'historical_operational_source_checks_omitted': omitted, 'operational_locks_excluded': locks,
        'external_original_inputs_verified': len(external),
        'external_original_input_bytes': sum(row['bytes'] for row in external),
        'prior_results': prior_results, 'prior_gate_files': gates,
        'prior_gate_entries_verified': sum(row['entries'] for row in gates),
        'financial_ledger': {'path': LEDGER, 'sha256': ledger['sha256'],
                             'bytes': ledger['bytes'], 'rows': len(ledger_rows), 'new_rows': 0},
        'new_financial_runs': 0, 'financial_statistics_computed': False,
        'network_requests': 0, 'remote_mutations': 0,
        'original_input_write_operations': 0, 'old_evidence_write_operations': 0,
        'qualification': 'Local byte availability only; this does not certify future Git inclusion or runtime readiness.',
        'files': list(inventory.values()), 'external_original_inputs': external,
    }


class PreservationChecks(unittest.TestCase):
    def test_known_bytes_match_sha256_and_git_blob(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture'
            path.write_bytes(b'abc')
            actual = inspect_file(path)
            self.assertEqual(actual['bytes'], 3)
            self.assertEqual(actual['sha256'], 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
            self.assertEqual(actual['git_blob'], hashlib.sha1(b'blob 3\0abc').hexdigest())

    def test_changed_hash_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'sha256'):
            require_match({'sha256': 'changed', 'bytes': 3}, {'sha256': 'original', 'bytes': 3}, 'fixture')

    def test_changed_length_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'bytes'):
            require_match({'sha256': 'same', 'bytes': 2}, {'sha256': 'same', 'bytes': 3}, 'fixture')

    def test_report_cannot_overwrite_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            path.write_bytes(b'original evidence')
            with self.assertRaises(FileExistsError):
                write_new(path, {'status': 'PASS'})
            self.assertEqual(path.read_bytes(), b'original evidence')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output', type=Path, default=OUT / 'preservation.json')
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=[__file__])
    else:
        output = args.output.resolve()
        if output.parent != OUT or output.suffix != '.json':
            parser.error('output must be a new JSON file in this verification directory')
        if output.exists():
            parser.error('output already exists; choose a new filename to preserve prior reports')
        started = datetime.now(timezone.utc).isoformat()
        try:
            result = verify()
        except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
            result = {'status': 'FAIL', 'baseline_commit': BASELINE,
                      'error': f'{type(error).__name__}: {error}'}
        result.update(started_utc=started, verified_utc=datetime.now(timezone.utc).isoformat(),
                      script_sha256=inspect_file(Path(__file__))['sha256'])
        write_new(output, result)
        print(json.dumps({k: v for k, v in result.items()
                          if k not in ('files', 'external_original_inputs',
                                       'historical_operational_source_checks_omitted')}, indent=2))
        raise SystemExit(0 if result['status'] == 'PASS' else 1)
