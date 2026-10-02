"""Prepare environment/workspace/parent bindings without admission or arrays."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
STUDY = ROOT / 'research/onchain-paper-replication-2026-09-24'
INITIAL = 'eth-paper-neural-resource-20261002-01'
PARENT = 'eth-paper-resource-pilot-20260924-02'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


for path in (ROOT / 'research_runs' / INITIAL,
             ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/runs' / INITIAL,
             ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/sources' / INITIAL):
    assert not path.exists() and not path.is_symlink()

# Same public inventory fields as environment.inventory, without importing the
# concurrently edited execution/lifecycle modules. No model is constructed.
import torch
environment = {
    'python': platform.python_version(), 'cpu_count': os.cpu_count(),
    'lock_sha256': sha(ROOT / 'uv.lock'),
    'packages': {p: importlib.metadata.version(p) for p in
                 ('numpy', 'scipy', 'pyarrow', 'torch', 'scikit-learn')},
    'cuda_available': torch.cuda.is_available(), 'torch_version': torch.__version__,
    'cuda_build': torch.version.cuda}
save('environment.json', environment)
common = subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=ROOT, text=True).strip()
save('execution-workspace.json', {
    'root': str(ROOT), 'ledger': str((ROOT / 'research_runs').resolve()),
    'artifacts': str((ROOT / 'research_artifacts').resolve()),
    'git_common': str((ROOT / common).resolve())})

claim_path = ROOT / 'research_runs' / PARENT / 'claim.json'
terminal_path = claim_path.with_name('failed.json')
claim = json.loads(claim_path.read_bytes())
terminal = json.loads(terminal_path.read_bytes())
assert claim['experiment_id'] == terminal['experiment_id'] == PARENT
assert terminal['status'] == 'failed' and terminal['claim_sha256'] == sha(claim_path)
original = json.loads((OUT.parent / 'gate-template.draft.json').read_bytes())
assert claim['family'] == original['registry_template']['families']['paper']
save('parent-experiment.json', claim['experiment'])
budget = STUDY / 'full_sources/budget-extension-62-2026-10-02'
review = json.loads((budget / 'review.json').read_bytes())
assert review['decision'] == 'accepted' and review['extension_sha256'] == sha(budget / 'extension.json')
save('bindings01.json', {
    'schema_version': 1, 'execution_admitted': False, 'namespace_reserved': False,
    'experiment_id': INITIAL, 'parent': PARENT,
    'environment': pin(OUT / 'environment.json'),
    'execution_workspace': pin(OUT / 'execution-workspace.json'),
    'parent_experiment': pin(OUT / 'parent-experiment.json'),
    'parent_claim': pin(claim_path), 'parent_terminal': pin(terminal_path),
    'cumulative_budget_extension': {'extension': pin(budget / 'extension.json'),
                                    'review': pin(budget / 'review.json')},
    'allocation': pin(budget / 'allocation.json'),
    'environment_inventory_source': pin(ROOT / 'tradingagents/research/onchain_replication/environment.py'),
    'qualification': 'Metadata bindings only. Compare environment/workspace against accepted final runtime before use. Parent remains byte-equivalent to its immutable claim. No model, arrays, full admission, source freeze or empirical execution.',
    'remaining': ['accepted physical route and exact limits', 'final charter/job/gate',
                  'committed complete source and runtime closure',
                  'independent final gate review and fresh host/admission checks']})
print('PASS: environment/workspace and exact immutable parent metadata prepared; accepted budget pins joined; prospective namespaces absent; no model/array/admission execution.')
