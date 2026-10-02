"""Check the reviewed budget projection only; no full admission or claim."""
from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def read_bound(reference):
    path = ROOT / reference['path']
    assert path.resolve().is_relative_to(ROOT)
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == reference['sha256']
    return raw


extension = json.loads((OUT / 'extension.json').read_bytes())
reference = {'extension': pin(OUT / 'extension.json'), 'review': pin(OUT / 'review.json')}
assert reference['review']['sha256'] == '0bae2075a5ab7133fc76541576f48afdb33e7a647835ef9053ae2dcaf5921985'
relevant = []
for path in sorted((ROOT / 'research_runs').glob('*/claim.json')):
    claim = json.loads(path.read_bytes())
    if claim['family']['mechanism_id'] == extension['base_family']['mechanism_id']:
        relevant.append(claim)
source = ROOT / 'tradingagents/research/budget_extensions.py'
spec = importlib.util.spec_from_file_location('budget_projection_only', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ceiling = module.effective_budget(
    ROOT, extension['program_id'], extension['initial_experiment'],
    {'cumulative_budget_extension': reference}, extension['base_family'],
    relevant, read_bound)
assert ceiling == 62
paths = [ROOT / 'research_runs' / extension['initial_experiment'],
         ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/runs' / extension['initial_experiment'],
         ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/sources' / extension['initial_experiment']]
assert all(not p.exists() and not p.is_symlink() for p in paths)
with (OUT / 'check01.json').open('x') as stream:
    json.dump({'budget_projection_ceiling': ceiling, 'same_mechanism_claim_count': len(relevant),
               'consumed_before': extension['base_family']['prior_attempts'] + len(relevant),
               'budget_references': reference, 'allocation': extension['allocation'],
               'implementation': pin(source), 'execution_admitted': False,
               'namespace_reserved': False,
               'qualification': 'Real effective_budget metadata call only. Source/design-commit binding and complete admit/ResearchRun were not invoked. Allocation category sublimits still require explicit future gate and substantive review.'},
              stream, sort_keys=True, indent=2)
    stream.write('\n')
print('PASS: actual effective_budget returns62 for exact accepted extension/review/allocation and16 current claims; all3 prospective namespaces remain absent; no full admission or execution.')
