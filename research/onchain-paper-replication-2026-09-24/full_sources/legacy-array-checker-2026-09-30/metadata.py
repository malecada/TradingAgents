"""Legacy FAILED-claim joins using compact metadata only; no array loader.

The caller must bind preparation bytes and this module in a committed release.
validate is pure: raw_objects contains only the 31 prepared compact receipts.
"""
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

CLAIM = 'eth-paper-resource-pilot-20260924-02'
SOURCE = 'c6b568d4b1c177ab94ac37fbad462c2decc721c0'
STUDY = 'research/onchain-paper-replication-2026-09-24/'
CONFIG = STUDY + 'config/graph.json'
NAMES = {'node_ids', 'node_features', 'edge_index', 'edge_features', 'edge_aggregates'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def validate(prep, raw_objects, config_raw, original_root):
    require(prep['schema_version'] == 1 and prep['original_claim'] == CLAIM
            and prep['original_terminal'] == 'failed' and prep['arrays_read'] is False
            and prep['new_empirical_claims'] == 0, 'preparation identity')
    require(len(raw_objects) == len(prep['files']) == 31
            and set(raw_objects) == set(prep['files']), 'compact inventory')
    objects = {}
    for name, raw in raw_objects.items():
        p = Path(name)
        require(not p.is_absolute() and '..' not in p.parts and p.suffix == '.json', 'compact path')
        entry = prep['files'][name]
        require(entry['path'] == name and len(raw) == entry['bytes'] <= 65536
                and sha(raw) == entry['sha256'], 'compact byte/hash binding')
        objects[name] = json.loads(raw)

    def one(suffix):
        names = [name for name in objects if name.endswith(suffix)]
        require(len(names) == 1, 'ambiguous compact receipt ' + suffix)
        return names[0], objects[names[0]]

    def h(name):
        return prep['files'][name]['sha256']

    def relative(path):
        p = Path(path)
        if p.is_absolute():
            p = p.relative_to(original_root)
        require('..' not in p.parts, 'source path traversal')
        return str(p)

    cn, claim = one('/claim.json'); tn, terminal = one('/failed.json')
    ln, ledger = one('/cell-ledger.json'); _, closure = one('/closure.json')
    gn, guard = one('/pilot-02-guard/final.json')
    _, observer = one('/pilot-02-guard/observer.json')
    _, owner = one('/pilot-02-supervisor/owner.json')
    sn, index = one('/source-index.json')
    require(claim['experiment_id'] == terminal['experiment_id'] == CLAIM
            and claim['source'] == SOURCE and terminal['status'] == 'failed'
            and terminal['claim_sha256'] == h(cn), 'original failed claim')
    require(closure['identity'] == CLAIM and closure['status'] == 'failed'
            and closure['source_commit'] == observer['source'] == owner['source'] == SOURCE
            and closure['terminal_sha256'] == observer['terminal_sha256'] == h(tn)
            and closure['cell_ledger_sha256'] == observer['observer_ledger_sha256'] == h(ln),
            'closure identities')
    require(guard['phase'] == 'failed' and guard['cleanup_verified'] is True
            and closure['cleanup_verified'] is True and observer['cgroup_empty'] is True
            and observer['status'] == 'failed', 'historical cleanup')
    require(guard['owner_identity']['supervisor_pid'] == owner['pid']
            and guard['owner_identity']['nonce'] == owner['nonce'], 'original owner')
    guard_original = 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02-guard/final.json'
    require(observer['guard_receipt_hashes'][str(Path(original_root)/guard_original)] == h(gn),
            'observer guard binding')
    require(closure['members'][guard_original] == prep['files'][gn], 'retained guard binding')
    declared_cells = claim['experiment']['cells']
    require(len(ledger) == closure['cells'] == len(declared_cells) == 109
            and len({c['id'] for c in ledger}) == 109
            and {c['id'] for c in ledger} == set(declared_cells), 'complete historical denominator')
    dispositions = dict(Counter(c['status'] for c in ledger))
    require(dispositions == closure['dispositions'] == prep['historical_dispositions']
            == {'complete':7, 'unavailable':102}, 'historical dispositions')
    inputs = claim['experiment']['inputs']

    def input_hash(path):
        entries = [v for v in inputs.values() if relative(v['path']) == path]
        require(len(entries) == 1, 'original input membership ' + path)
        return entries[0]['sha256']

    require(input_hash(sn) == h(sn) and sha(config_raw) == input_hash(CONFIG), 'index/config binding')
    config_hash = sha(encode(json.loads(config_raw)))
    require([g['week'] for g in prep['graphs']] == ['2022-01-03', '2022-06-13'], 'legacy graph membership')
    total = 0
    for graph in prep['graphs']:
        week = graph['week']; mn = graph['manifest']['path']; rn = graph['result']['path']
        cvn = graph['coverage']['path']; manifest = objects[mn]; result = objects[rn]; coverage = objects[cvn]
        require(all(graph[key] == prep['files'][graph[key]['path']]
                    for key in ('manifest', 'result', 'coverage')), 'graph references')
        intent_name = str(Path(rn).parent/'intent.json'); intent = objects[intent_name]
        require(intent['phase'] == result['phase'] == 'decode_graph'
                and intent['week'] == result['week'] == week
                and intent['source_commit'] == SOURCE and result['status'] == 'complete', 'complete phase identity')
        for name in (mn, rn, intent_name):
            retained = closure['members'][name]
            require(retained['bytes'] == prep['files'][name]['bytes']
                    and retained['sha256'] == h(name), 'historical retained phase')
        cell, = [c for c in ledger if c['id'] == 'decode_graph-' + week]
        require(cell['status'] == 'complete' and cell['worker_exit_code'] == 0
                and cell['phase'] == 'decode_graph' and cell['week'] == week
                and cell['details'] == result['details'], 'complete ledger/phase join')
        details = result['details']; meta = manifest['metadata']
        require(meta == graph['metadata'] and manifest['graph_hash'] == graph['graph_hash'], 'graph metadata')
        require(meta['asset'] == coverage['asset'] == 'ETH'
                and coverage['claim_sha256'] == h(cn)
                and coverage['graph_manifest_sha256'] == details['graph_manifest_sha256'] == h(mn)
                and relative(details['graph_manifest']) == mn, 'graph manifest joins')
        require(meta['graph_config_hash'] == coverage['graph_config_hash'] == config_hash
                and intent['bindings'][str(Path(original_root)/CONFIG)] == sha(config_raw), 'graph config identity')
        require(meta['start_utc'] == coverage['week'] == week + 'T00:00:00Z'
                and meta['end_utc'] == coverage['end_utc'], 'graph interval')
        start = datetime.fromisoformat(meta['start_utc'])
        require(datetime.fromisoformat(meta['end_utc']) == start + timedelta(days=7)
                and datetime.fromisoformat(meta['available_at']) == start + timedelta(days=8), 'graph interval lengths')
        for field in ('raw_count', 'admitted_count', 'exclusion_counts'):
            require(meta[field] == details[field], 'graph counts ' + field)
        require(details['rows'] == meta['raw_count']
                and meta['raw_count'] == meta['admitted_count'] + sum(meta['exclusion_counts'].values())
                and details['nodes'] == graph['nodes'] and details['edges'] == graph['directed_edges'], 'graph dimensions/counts')
        source = index['weeks'][week]; members = source['members']
        require(source['expected_members'] == len(members) == len(coverage['members']) == 7
                and source['expected_rows'] == meta['raw_count']
                and source['end_utc'] == meta['end_utc']
                and coverage['plan_sha256'] == h(sn)
                and intent['bindings'][str(Path(original_root)/sn)] == h(sn), 'source index joins')
        previous = meta['start_utc']
        for member, covered in zip(members, coverage['members'], strict=True):
            name = relative(member['path'])
            require(member['start_utc'] == covered['start_utc'] == previous
                    and datetime.fromisoformat(member['end_utc']) == datetime.fromisoformat(previous) + timedelta(days=1), 'daily continuity')
            previous = member['end_utc']
            require(all(member[k] == covered[k] for k in ('end_utc', 'sha256', 'expected_rows'))
                    and member['sha256'] == h(name) == input_hash(name)
                    and intent['bindings'][member['path']] == h(name)
                    and covered['source_input'] == 'source_index'
                    and covered['source_manifest_sha256'] == h(sn), 'daily provenance joins')
        require(previous == meta['end_utc'] and sum(m['expected_rows'] for m in members) == meta['raw_count']
                and sorted(m['sha256'] for m in members) == meta['source_hashes'], 'weekly membership/counts')
        require(set(manifest['arrays']) == NAMES and len(graph['arrays']) == 5
                and {a['name'] for a in graph['arrays']} == NAMES, 'array membership')
        graph_bytes = 0
        for array in graph['arrays']:
            name = array['name']; entry = manifest['arrays'][name]
            require(entry['path'] == name + '.npy'
                    and array['path'] == str(Path(mn).parent/entry['path'])
                    and array['declared_sha256'] == entry['sha256']
                    and array['declared_bytes'] == array['observed_stat_bytes'] == entry['bytes']
                    and array['body_read'] is False and array['hash_verified'] is False, 'array declaration join')
            graph_bytes += entry['bytes']
        require(details['graph_bytes'] == graph_bytes + prep['files'][mn]['bytes'], 'original graph extents')
        total += graph_bytes
    require(total == prep['array_bytes_declared'] == 1037092456, 'total declared extents')
    return {'historical_dispositions':dispositions, 'graphs':prep['graphs'],
            'array_bytes_declared':total, 'arrays_read':False,
            'qualification':'Compact producer/closure joins only; array and raw semantics remain unverified.'}
