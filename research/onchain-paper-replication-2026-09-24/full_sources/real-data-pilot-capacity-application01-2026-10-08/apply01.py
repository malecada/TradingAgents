"""Integer geometry from verified census/motif metadata; no numerical model."""
import ast
import hashlib
import json
import os
from pathlib import Path
import struct
import types

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
HERE = Path(__file__).resolve().parent


def read(path, expected=None):
    raw = path.read_bytes()
    if expected is not None and hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('selected metadata hash differs: ' + str(path))
    return json.loads(raw)


def header(path):
    before = path.stat()
    with path.open('rb') as stream:
        if stream.read(6) != b'\x93NUMPY':
            raise ValueError('NPY magic differs')
        version = stream.read(2)
        if version not in (b'\x01\x00', b'\x02\x00'):
            raise ValueError('unsupported bounded header')
        width = 2 if version[0] == 1 else 4
        size = struct.unpack('<H' if width == 2 else '<I', stream.read(width))[0]
        if not 0 < size <= 4096:
            raise ValueError('header exceeds bound')
        raw = stream.read(size)
        result = ast.literal_eval(raw.decode('latin1'))
        if os.fstat(stream.fileno()) != before or path.stat() != before:
            raise ValueError('header input changed')
    if result['descr'] != '<f8' or result['fortran_order']:
        raise ValueError('expected row-major float64 feature header')
    result['shape'] = list(result['shape'])
    result['header_sha256'] = hashlib.sha256(raw).hexdigest()
    result['file_bytes'] = before.st_size
    result['header_bytes'] = 8 + width + size
    return result


def main():
    inputs = read(BASE / 'real-data-pilot-census-input-review01-2026-10-08/CALLER_INPUTS02.json',
                  '255f70a8998f7c7217f467d1f0fab6cec39c3e78acb2bf4f9bcbf7ad7133adb1')
    census = read(ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/engineering/eth-seven-graph-weak-one-hop-census-20261008-01/results/SUMMARY01.json',
                  'db189e23d44799ef5656fd8b89b243d262127d73707640a1057e27452de019e7')
    dimensions = read(BASE / 'real-data-pilot-original-motif-dimensions01-2026-10-08/MOTIF_DIMENSIONS01.json',
                      '05a3d78114463bec74d1d507fb05c120d893c1d95b42a943fabc4db8944cf70d')
    if census['status'] != 'completed' or len(inputs) != 7 or dimensions['motif_count'] != 32:
        raise ValueError('complete exact census/motif metadata required')
    topology = {'hop_depth': 1, 'direction': 'weak', 'includes_center': True, 'graphs': []}
    observed = []
    for selected, result in zip(inputs, census['graphs'], strict=True):
        if selected['graph_hash'] != result['graph_hash'] or result['status'] != 'completed':
            raise ValueError('ordered census graph join differs')
        manifest_path = ROOT / selected['manifest']['path']
        manifest = read(manifest_path, selected['manifest']['sha256'])
        features = {name: header(manifest_path.parent / manifest['arrays'][name]['path'])
                    for name in ('node_features', 'edge_features')}
        n = result['node_count']; e = result['edge_count']
        for name, rows in (('node_features', n), ('edge_features', e)):
            item = features[name]
            if len(item['shape']) != 2 or item['shape'][0] != rows or item['shape'][1] < 1:
                raise ValueError('feature dimensions differ')
            if item['header_bytes'] + rows * item['shape'][1] * 8 != item['file_bytes'] or item['file_bytes'] != manifest['arrays'][name]['bytes']:
                raise ValueError('feature file extent differs')
        topology['graphs'].append({'graph_sha256': result['graph_hash'], 'nodes': n, 'edges': e,
            'node_features': features['node_features']['shape'][1], 'edge_features': features['edge_features']['shape'][1],
            'node_itemsize': 8, 'edge_itemsize': 8, 'maximum_cardinality': result['maximum_cardinality'],
            'maximum_center_index': result['maximum_center_index']})
        observed.append({'graph': result['graph_hash'], 'feature_headers': features,
                         'qualification': 'header/stat/extent only; no current feature body hash or writer exclusion'})
    dictionary_config = read(ROOT / 'research/onchain-paper-replication-2026-09-24/config/dictionary.json',
                             '1ff53e21bee55d6eacb0ea4273411f12e2b4987c15a9a5b493aa1f6db1c102ff')
    motifs = {'dictionary_sha256': dimensions['original_dictionary_json_sha256'],
              'dictionary_config_sha256': '1ff53e21bee55d6eacb0ea4273411f12e2b4987c15a9a5b493aa1f6db1c102ff',
              'representatives': [{'graph_sha256': m['representative_json_sha256'], 'motif_index': m['motif_index'],
                  'nodes': m['node_count'], 'edges': m['edge_count'], 'node_features': m['node_feature_width'],
                  'edge_features': m['edge_feature_width'], 'node_itemsize': 8, 'edge_itemsize': 8}
                 for m in dimensions['motifs']]}
    refs = read(BASE / 'real-data-pilot-final19-2026-10-08/INPUT_DRAFT01.json')['protocol']['references']
    policies = {name: read(ROOT / refs[name]['path'], refs[name]['sha256'])
                for name in ('compact_policy', 'mcm_policy', 'original_matching_config')}
    stage = policies['compact_policy']['stage_policy']; pair = stage['pair']; numeric = policies['mcm_policy']['numeric']
    limits = {'extraction_limit': dictionary_config['maximum_neighborhood_nodes'],
        'max_pair_entries': policies['original_matching_config']['max_pair_entries'],
        **{k: pair[k] for k in ('max_state_bytes', 'normalization_chunk_entries', 'hardening_buffer_bytes', 'max_score_buffer_bytes', 'max_checkpoint_bytes')},
        **{k: numeric[k] for k in ('max_buffer_bytes', 'max_output_bytes', 'max_numeric_bytes', 'edge_chunk')},
        'max_entries': policies['mcm_policy']['max_entries'], 'max_file_bytes': 4194304,
        'score_chunk_edges': pair['chunk_edges'], 'score_chunk_cells': stage['score_chunk_cells'],
        'log_chunk_events': stage['log']['chunk_events'], 'max_total_checkpoints': stage['schedule']['max_total_checkpoints']}
    helper_path = BASE / 'real-data-pilot-complete-neighborhood-capacity-preparation01-2026-10-08/successor02/capacity.py'
    body = helper_path.read_bytes()
    if hashlib.sha256(body).hexdigest() != '2d2f4f3e7b3804ce0721aefbdd822e8766d45da61afa30d8fce0b76788415315':
        raise ValueError('capacity source differs')
    module = types.ModuleType('capacity_preparation'); exec(compile(body, str(helper_path), 'exec'), module.__dict__)
    report = module.prepare(topology, motifs, expected_topology_sha256=module.digest(topology),
                            expected_motifs_sha256=module.digest(motifs), limits=limits)
    for filename, value in [('INPUTS01.json', {'topology': topology, 'motifs': motifs, 'limits': limits,
         'feature_header_observations': observed, 'motif_item_width_source': 'original_import_preparation.py:145-147 explicit float64',
         'motif_hash_kind': 'original canonical representative JSON witness; not a new typed scientific identity'}),
         ('CAPACITY01.json', report)]:
        with (HERE / filename).open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'reported_limits_satisfied': report['reported_limits_satisfied'],
                     'refusals': len(report['refusals']), 'execution_admitted': report['execution_admitted'],
                     'maxima': report['universal_component_envelopes']}, indent=2))


if __name__ == '__main__':
    main()
