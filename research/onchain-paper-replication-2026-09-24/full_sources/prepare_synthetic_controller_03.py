"""One isolated synthetic controller probe; preparation only, no launch/retry."""
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.research.test_lifecycle import registered, commit, git
from tests.research.onchain_replication.test_run import setup
from tests.research.onchain_replication.test_dataset import fixture
from tests.research.onchain_replication.test_feature_pipeline import configs
from tradingagents.research.onchain_replication.job import required_sources
from tradingagents.research.onchain_replication.job_payload import population_record
from tradingagents.research.onchain_replication.graph_store import save_graph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.registered_features import representation_descriptor
from tradingagents.research.onchain_replication.provenance import file_hash, canonical_bytes
from tradingagents.research.onchain_replication.environment import inventory


def main():
    target = Path('/tmp/onchain-paper-generic-job-synthetic-20260924-03')
    target.mkdir(exist_ok=False)
    reg, populations, plan = setup(registered.__wrapped__(target))
    _, spec, _ = reg
    experiment = spec['experiments'].pop('example-a')
    identity = 'controller-synthetic-20260924-03'
    spec['experiments'][identity] = experiment
    experiment['question'] = 'Isolated synthetic full-architecture controller ownership and closure; no financial result.'
    spec['families']['family-a']['attempt_budget'] = 1
    graphs, _, fold, _ = fixture()
    examples, scaler = populations['whole']
    required = {h for row in (*examples.train, *examples.test) for h in row.graph_hashes}
    # Retain the full declared synthetic training graph population for dictionary sampling.
    config = configs()
    config['dictionary'] = {**config['dictionary'], 'sample_count': 32, 'size': 32}
    from tradingagents.research.onchain_replication.provenance import utc
    centers = sum(len(g.node_ids) for g in graphs if utc(g.start_utc) >= utc(fold.train_start) and utc(g.available_at) < utc(fold.train_end))
    if centers < config['dictionary']['sample_count']:
        raise ValueError('synthetic dictionary population cannot satisfy frozen sample size')
    descriptor = representation_descriptor(graphs, examples, fold, 'proposed', 11, config)
    references = {}
    for i, graph in enumerate(graphs):
        path = save_graph(target/'graphs'/str(i), graph)
        name = 'graph_'+str(i)
        experiment['inputs'][name] = {'path': str(path.relative_to(target)), 'sha256': file_hash(path), 'dataset': 'sample'}
        references[graph_hash(graph)] = {'input': name}
    producer = {'descriptor': descriptor, 'graphs': references, 'max_entries': 100000,
                'max_array_bytes': 16*1024**2, 'binding_output': 'motif-binding.json', 'journal_output': 'motif-journal.json'}
    plan['cells'][0]['cell']['arm'] = 'proposed'
    plan['cells'][0]['representation'] = 'motif-11'
    plan['representations']['motif-11'] = {'output': 'motif-binding.json', 'failure_output': 'motif-status.json'}
    experiment['outputs'] += ['motif-binding.json', 'motif-journal.json', 'motif-status.json']
    payload = {'population_inputs': {'whole': 'population'}, 'batch_plan_input': 'batch_plan',
        'representation_jobs': {'motif-11': {'operation': 'produce', 'descriptor': descriptor,
            'plan_input': 'representation_plan', 'producer': 'motif-11', 'population': 'whole',
            'max_graph_payload_bytes': 16*1024**2}}}
    sources = sorted(required_sources())
    for relative in [*sources, 'uv.lock', 'pyproject.toml']:
        destination = target/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/relative, destination)
    policy = {'memory_max_bytes': 1536*1024**2, 'memory_high_bytes': 1280*1024**2,
              'reserve_bytes': 3*1024**3, 'start_reserve_bytes': 4608*1024**2,
              'disk_floor_bytes': 20*1024**3, 'disk_paths': [str(target)], 'wall_seconds': 300}
    job = {'schema_version': 1, 'kind': 'fit', 'resources': policy,
           'environment_input': 'environment', 'payload': payload}
    values = {'batch_plan': plan, 'population': population_record(examples, scaler),
              'representation_plan': {'schema_version': 1, 'producers': {'motif-11': producer}},
              'environment': inventory(target, include_torch=True), 'execution_job': job}
    for name, value in values.items():
        path = target/(name+'.json')
        path.write_bytes(canonical_bytes(value))
        experiment['inputs'][name] = {'path': path.name, 'sha256': file_hash(path), 'dataset': 'sample'}
    (target/'charter.md').write_text('Synthetic controller probe only. Deterministic toy two-node weekly graphs and periodic prices, 40 training and four test rows. One proposed motif32/MCM/GAT/attention-LSTM direction fit at one epoch, one independent SVM regression fit, and one deliberately unavailable cell. Dedicated fixture samples32 rather than production512; no empirical inference or tuning. One launch only, exact source and inputs committed before outcomes. 1536MiB memory ceiling, 1280MiB high, zero swap, two CPUs, 300 seconds, 3GiB host reserve, 20GiB disk floor. Verify exact three-cell denominator, ownership, empty cgroup, durable representations/checkpoints/predictions and independent metrics. Preserve every failure; never restart this identity.\n')
    experiment['charter']['sha256'] = file_hash(target/'charter.md')
    experiment['source_files'] = {p: file_hash(target/p) for p in sources}
    git(target, 'add', *sources, 'uv.lock', 'pyproject.toml')
    source = commit(target, spec)
    receipt = {'root': str(target), 'experiment': identity, 'source': source,
               'registration_sha256': file_hash(target/'registration.json'),
               'source_files': experiment['source_files'], 'resources': policy,
               'inputs': experiment['inputs'], 'synthetic_only': True,
               'launch_command': [str(ROOT/'.venv/bin/python'), '-B', '-m',
                   'tradingagents.research.onchain_replication.job', '--mode', 'launch',
                   '--root', str(target), '--registration', 'registration.json',
                   '--experiment', identity, '--source', source]}
    destination = ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/controller-synthetic-03-preparation.json'
    with destination.open('xb') as handle:
        handle.write(canonical_bytes(receipt))
    print(json.dumps({k: receipt[k] for k in ('root', 'experiment', 'source', 'registration_sha256')}))


if __name__ == '__main__':
    main()
