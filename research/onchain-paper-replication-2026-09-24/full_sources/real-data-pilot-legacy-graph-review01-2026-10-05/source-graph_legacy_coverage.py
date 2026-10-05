"""Fixed legacy pilot02 metadata evidence; no modern producer proof is invented.

The caller supplies its genuine run.read_input. This pure validator creates no
lifecycle authority and does not read files or decode graph arrays.
"""
import hashlib
import json
from datetime import datetime, timedelta

# phase_source and run_source pins match git show SOURCE:<original path> byte-for-byte.
SOURCE = 'c6b568d4b1c177ab94ac37fbad462c2decc721c0'
EXPERIMENT = 'eth-paper-resource-pilot-20260924-02'
WEEK = '2022-06-13'
KIND = 'legacy-pilot02-source-evidence'
EVIDENCE = {'artifact_index': {'path': 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/postmortem/artifact-index.json',
                    'sha256': '208d00df2c42441ee512ca31011bed336de75282a3c492fd88f4994c3c3d3f59'},
 'cell': {'path': 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/cell-007.json',
          'sha256': '7922b9cb48fc4f72c0ba008e3de4161e67934c655853f21001baa37873a27a27'},
 'cell_ledger': {'path': 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/postmortem/cell-ledger.json',
                 'sha256': '09750888389e7bba366818aa4134ae07e72f6fdeeb4af59594e7f0f627cc3e5c'},
 'claim': {'path': 'research_runs/eth-paper-resource-pilot-20260924-02/claim.json',
           'sha256': '05d769f6f50a65c2cf3eeed569077eb84e3871b1e7c23ad3504eed461a0565ca'},
 'day_20220613': {'path': 'research/onchain-paper-replication-2026-09-24/pilot/source-maps-v2/2022-06-13.json',
                  'sha256': '89a337e96f886bcf0cc076562d4bbe7ee9f58ee55ce0034e792577911bcf04b3'},
 'day_20220614': {'path': 'research/onchain-paper-replication-2026-09-24/pilot/source-maps-v2/2022-06-14.json',
                  'sha256': 'd20442fbcb8b455fed90d1390ec56bc24e5d3b2bd369e96b785c79c789b80ad7'},
 'day_20220615': {'path': 'research/onchain-paper-replication-2026-09-24/pilot/source-maps-v2/2022-06-15.json',
                  'sha256': '238fb121b282dce970ca7cbdaff102769a11817ebe42cfac16b85e5584dfc6f7'},
 'day_20220616': {'path': 'research/onchain-paper-replication-2026-09-24/pilot/source-maps-v2/2022-06-16.json',
                  'sha256': '3c221307faaa331561d8251630874befc885872e1f06e9fed2821141999edc5d'},
 'day_20220617': {'path': 'research/onchain-paper-replication-2026-09-24/pilot/source-maps-v2/2022-06-17.json',
                  'sha256': '42afe182bbf8e9a3689008a01f65ea43e986602c03ad058e89a37c72d3de4151'},
 'day_20220618': {'path': 'research/onchain-paper-replication-2026-09-24/pilot/source-maps-v2/2022-06-18.json',
                  'sha256': 'a9eaea951a39f052cfc75dc87b80427ef60688653fb1cdef18fcbbf3426cafe2'},
 'day_20220619': {'path': 'research/onchain-paper-replication-2026-09-24/pilot/source-maps-v2/2022-06-19.json',
                  'sha256': '6f97d58f35f84c7e302b22b9076819a5ed14f94175037d6ec57d9d7bf72119a2'},
 'graph_config': {'path': 'research/onchain-paper-replication-2026-09-24/config/graph.json',
                  'sha256': 'c91f8eeb1d317a310ef0f90f40a78ccf60bdd2437532f5e909f7dfd079d7fc20'},
 'graph_manifest': {'path': 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/2022-06-13/decode_graph/graph/manifest.json',
                    'sha256': 'a7599cb4dce5a3d7b01614fe097026e70d48ecd63bb1c25518ccb05f41204d59'},
 'intent': {'path': 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/2022-06-13/decode_graph/intent.json',
            'sha256': '85501afe7fe78693d0da8a0cff4d0fa8264d0a2e061ca5952bfd6a48183cd836'},
 'phase_source': {'path': 'research/onchain-paper-replication-2026-09-24/pilot_successor_02/phase.py',
                  'sha256': '0bc95f7e33d97485cd9e2fba6802dde168c26aa162b987ef762f9e28ee3a1522'},
 'result': {'path': 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/2022-06-13/decode_graph/result.json',
            'sha256': '8b9b85b369f9e590fcfb2f02fa4faeae34cacac091b637e57c54ea5004814e18'},
 'run_source': {'path': 'research/onchain-paper-replication-2026-09-24/pilot_successor_02/run.py',
                'sha256': '90dc7fc1fb6780174502e395db073d27c511a30aea8762ea968f256e4820c5e6'},
 'source_index': {'path': 'research/onchain-paper-replication-2026-09-24/pilot_successor_02/source-index.json',
                  'sha256': '18f2548bdec2602995935d951075162537b6369b8bf18647cdc7a96962cffc1a'},
 'terminal': {'path': 'research_runs/eth-paper-resource-pilot-20260924-02/failed.json',
              'sha256': '3d318717ff7adecb0f07b9db6f3d1bd2e24e0c77705c3e07062cd4b075f8d7f2'}}


def _require(condition, message):
    if not condition:
        raise ValueError('legacy graph evidence: ' + message)


def verify_legacy_coverage(proof, graph, manifest_sha, read_input):
    """Consume exactly the fixed 19 independently registered original bodies."""
    _require(isinstance(proof, dict) and set(proof) == {'schema_version', 'kind', 'roles'}
             and type(proof['schema_version']) is int and proof['schema_version'] == 2
             and proof['kind'] == KIND, 'proof schema differs')
    roles = proof['roles']
    _require(isinstance(roles, dict) and set(roles) == set(EVIDENCE), 'role denominator differs')
    _require(all(isinstance(v, str) and v for v in roles.values())
             and len(set(roles.values())) == len(roles), 'roles must be unique names')
    values = {}
    for name, expected in EVIDENCE.items():
        raw = read_input(roles[name])
        _require(type(raw) is bytes and len(raw) <= 2 * 1024**2, 'bounded body required')
        _require(hashlib.sha256(raw).hexdigest() == expected['sha256'], name + ' body differs')
        if not name.endswith('_source'):
            values[name] = json.loads(raw)
    claim, terminal = values['claim'], values['terminal']
    _require(claim['experiment_id'] == terminal['experiment_id'] == EXPERIMENT
             and claim['source'] == claim['design_source'] == SOURCE
             and terminal['status'] == 'failed' and terminal['output_sha256'] == {}
             and terminal['claim_sha256'] == EVIDENCE['claim']['sha256'], 'parent closure differs')
    index_ref = claim['inputs']['source_index']
    _require(index_ref['path'] == EVIDENCE['source_index']['path']
             and index_ref['sha256'] == EVIDENCE['source_index']['sha256'], 'original index binding differs')
    intent, result, cell = values['intent'], values['result'], values['cell']
    _require(intent['source_commit'] == SOURCE and intent['phase'] == 'decode_graph'
             and intent['week'] == WEEK, 'phase intent differs')
    # Original absolute keys are historical evidence; relocation does not rewrite them.
    original_root = intent['artifacts'].removesuffix('/research_artifacts/onchain-paper-replication-2026-09-24/pilot-02')
    _require(original_root != intent['artifacts'], 'original artifact root differs')
    original_path = lambda name: original_root + '/' + EVIDENCE[name]['path']
    for name in ['source_index', 'graph_config'] + [f'day_202206{d}' for d in range(13, 20)]:
        _require(intent['bindings'][original_path(name)] == EVIDENCE[name]['sha256'], 'intent input differs')
    _require(result['status'] == cell['status'] == 'complete'
             and result['week'] == cell['week'] == WEEK
             and result['phase'] == cell['phase'] == 'decode_graph'
             and cell['id'] == 'decode_graph-' + WEEK and cell['worker_exit_code'] == 0
             and result['details'] == cell['details'], 'completed component differs')
    ledger = [v for v in values['cell_ledger'] if v['id'] == cell['id']]
    _require(ledger == [cell], 'closed component ledger differs')
    for name in ['graph_manifest', 'intent', 'result', 'cell']:
        _require(values['artifact_index'][original_path(name)]['sha256'] == EVIDENCE[name]['sha256'],
                 'postmortem artifact join differs')
    manifest = values['graph_manifest']; metadata = manifest['metadata']
    _require(manifest_sha == EVIDENCE['graph_manifest']['sha256']
             == result['details']['graph_manifest_sha256']
             and result['details']['graph_manifest'] == original_path('graph_manifest'), 'graph manifest differs')
    for field in ['asset', 'start_utc', 'end_utc', 'available_at', 'graph_config_hash', 'raw_count', 'admitted_count']:
        _require(getattr(graph, field) == metadata[field], 'graph ' + field + ' differs')
    _require(list(graph.source_hashes) == metadata['source_hashes']
             and dict(graph.exclusion_counts) == metadata['exclusion_counts'], 'graph source/exclusions differ')
    # Match the project's canonical configuration hash without numerical imports.
    config_hash = hashlib.sha256(json.dumps(values['graph_config'], sort_keys=True,
                                            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    _require(config_hash == metadata['graph_config_hash'], 'graph configuration differs')
    week = values['source_index']['weeks'][WEEK]; members = week['members']
    _require(week['status'] == 'complete' and week['expected_members'] == len(members) == 7
             and week['start_utc'] == metadata['start_utc'] and week['end_utc'] == metadata['end_utc'],
             'week interval differs')
    for offset, member in enumerate(members):
        start = datetime(2022, 6, 13) + timedelta(days=offset)
        name = f'day_202206{13 + offset}'
        _require(member['start_utc'] == start.isoformat() + 'Z'
                 and member['end_utc'] == (start + timedelta(days=1)).isoformat() + 'Z'
                 and member['path'] == original_path(name)
                 and member['sha256'] == EVIDENCE[name]['sha256']
                 and member['format'] == 'projected_zstd'
                 and type(member['expected_rows']) is int and member['expected_rows'] > 0,
                 'daily coverage differs')
    _require(sorted(m['sha256'] for m in members) == sorted(metadata['source_hashes'])
             and sum(m['expected_rows'] for m in members) == week['expected_rows']
             == result['details']['rows'] == result['details']['raw_count'] == graph.raw_count,
             'coverage counts/source hashes differ')
    return {'schema_version': 2, 'kind': KIND, 'parent_status': 'failed',
            'graph_cell_status': 'complete', 'modern_producer_plan_present': False, 'claim_sha256': EVIDENCE['claim']['sha256'],
            'source_index_sha256': EVIDENCE['source_index']['sha256'],
            'graph_manifest_sha256': manifest_sha, 'member_count': 7}
