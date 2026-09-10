"""Verify prior artifacts and original stores without rerunning financial work."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASELINE = 'd9d6a3ede6d80f4c46024ea27b296860e51cd7db'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    frozen = ['data', 'scripts', 'tradingagents/accounting.py', 'tradingagents/xsect',
              'docs/audit', 'docs/reevaluation', 'docs/data-recovery', 'docs/settlement-evidence']
    subprocess.run(['git', 'diff', '--exit-code', BASELINE, '--', *frozen], cwd=ROOT, check=True)
    recovery = json.loads((ROOT / 'docs/data-recovery/verification/final-manifest.json').read_text())
    settlement = json.loads((ROOT / 'docs/settlement-evidence/verification/final-manifest.json').read_text())
    verified = {}
    for row in recovery['files'] + settlement['files']:
        if Path(row['path']).name == '.ledger.lock':
            continue
        assert digest(ROOT / row['path']) == row['sha256'], row['path']
        verified[row['path']] = row['sha256']
    for filename, expected in recovery['referenced_external_original_inputs'].items():
        assert digest(Path(filename)) == expected, filename
    ledger = ROOT / 'data/predlab/trial_ledger.jsonl'
    ledger_sha = digest(ledger)
    assert ledger_sha == '710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791'
    source = ['tradingagents/event_accounting.py', 'tests/test_event_accounting.py']
    output = {
        'status': 'PASS', 'baseline': BASELINE,
        'prior_local_artifacts_verified': len(verified),
        'external_original_inputs_verified': len(recovery['referenced_external_original_inputs']),
        'frozen_paths_unchanged': frozen,
        'financial_ledger': {'sha256': ledger_sha, 'bytes': ledger.stat().st_size, 'new_rows': 0},
        'new_financial_runs': 0, 'historical_terminal_prices_admitted': 0,
        'source_sha256': {p: digest(ROOT / p) for p in source},
        'script_sha256': digest(Path(__file__)),
    }
    (Path(__file__).parent / 'preservation.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
