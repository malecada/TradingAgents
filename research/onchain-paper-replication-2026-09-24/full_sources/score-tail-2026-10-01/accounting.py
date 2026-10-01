"""Static completed-score storage arithmetic; no arrays or outcomes read."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / 'native-resource-admission-2026-10-01/inputs02.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    inputs = json.loads(INPUT.read_text()); rows = []
    # A prospective arithmetic example, not an adopted execution configuration.
    chunk_cells = 65536
    for graph in inputs['graphs']:
        cells = graph['mcm_pair_evaluations']; chunks = (cells + chunk_cells - 1) // chunk_cells
        assert cells == graph['nodes'] * 32
        rows.append({'week': graph['week'], 'cells': cells, 'chunks': chunks,
            'retained_tail_record_bytes': 80 * cells, 'batch_payload_bytes': 8 * cells,
            'metadata_allowance_bytes': (4 * chunks + 4) * 8192,
            'logical_completed_score_bound': 88 * cells + (4 * chunks + 4) * 8192})
    source = ['tradingagents/research/onchain_replication/' + name for name in
              ('score_tail.py', 'score_batches.py', 'mcm_score_stream.py')]
    result = {'kind': 'static_arithmetic_only', 'execution_admitted': False,
        'input_sha256': sha(INPUT), 'source_sha256': {name: sha(ROOT / name) for name in source},
        'prospective_chunk_cells': chunk_cells, 'rows': rows,
        'totals': {field: sum(row[field] for row in rows) for field in (
            'cells', 'chunks', 'retained_tail_record_bytes', 'batch_payload_bytes',
            'metadata_allowance_bytes', 'logical_completed_score_bound')},
        'excludes': ['filesystem allocation overhead', 'original pair journals and checkpoints',
            'live matching state', 'graph and dictionary storage', 'guard and application logs',
            'other run outputs', 'predecessor evidence'],
        'qualification': 'Not measured physical disk, RSS, runtime, IOPS or a purchase requirement. '
            'Current stream wraps the existing callback; old per-pair artifacts remain.'}
    with (HERE / 'accounting01.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(result['totals'], sort_keys=True))
