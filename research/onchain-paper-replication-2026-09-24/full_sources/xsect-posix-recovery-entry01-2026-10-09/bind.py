"""Bind actual completed evidence once; no transport, claim or reconstruction."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
F = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'


def ref(path):
    body = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(body),
            'sha256': hashlib.sha256(body).hexdigest()}


def main():
    draft = json.loads((HERE / 'CONTRACT_DRAFT01.json').read_bytes())
    backup = F / 'real-data-pilot-xsect-preservation03-2026-10-08'
    native = F / 'real-data-pilot-final22-2026-10-08'
    draft['backup_complete_ref'] = ref(backup / 'COMPLETE01.json')
    draft['backup_terminal_ref'] = ref(backup / 'ROOT_TERMINAL01.json')
    draft['native_terminal_ref'] = ref(native / 'ROOT_TERMINAL01.json')
    draft['native_final_ref'] = ref(ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/runs' /
                                    draft['native_identity'] / 'guard/final.json')
    draft['selection'] = []
    for index in range(draft['expected_batches']):
        base = backup / 'batches' / f'batch-{index:04d}'
        draft['selection'].append({'index': index,
              'receipt_ref': ref(base / 'complete.json'),
              'manifest_ref': ref(base / 'manifest.json')})
    draft['status'] = 'READY'
    scope = {'__name__': 'xsect_restore_binding', '__file__': str(HERE / 'restore.py')}
    exec(compile((HERE / 'restore.py').read_bytes(), str(HERE / 'restore.py'), 'exec'), scope)
    scope['validate_selection'](draft)
    scope['eligibility'](draft, draft['restore_allocation_bound_bytes'])
    scope['emit'](HERE / 'CONTRACT_FINAL01.json', draft)
    print('Actual completed backup and terminal evidence bound; independent release still required.')


if __name__ == '__main__':
    main()
