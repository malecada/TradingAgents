"""One-use engineering timing; no motif sampling, MCM or financial outcomes."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    body = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    if len(body) > 1048576:
        raise ValueError('engineering receipt exceeds declared bound')
    with Path(path).open('xb') as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def verify(config, expected):
    if digest(HERE / 'registration01.json') != expected:
        raise ValueError('registration identity differs')
    for ref in config['sources']:
        if digest(ROOT / ref['path']) != ref['sha256']:
            raise ValueError('source identity differs: ' + ref['path'])
    if sys.version.split()[0] != '3.13.13':
        raise ValueError('pinned interpreter version differs')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['parent', 'worker'])
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--review-sha256')
    args = parser.parse_args()
    config = json.loads((HERE / 'registration01.json').read_bytes())
    verify(config, args.registration_sha256)
    output = ROOT / config['output_root']
    guard = output / 'guard'
    if args.mode == 'parent':
        if output.exists() or output.is_symlink():
            raise ValueError('engineering identity is already reserved; no relaunch')
        head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
        if head != args.source or not args.review or digest(args.review) != args.review_sha256:
            raise ValueError('committed source/review differs')
        review = json.loads(args.review.read_bytes())
        if review['decision'] != 'accepted' or review['registration_sha256'] != args.registration_sha256 or review['profile_sha256'] != digest(__file__):
            raise ValueError('exact engineering entry is not accepted')
        joined = config['sources'] + [dict(path=str((HERE / 'registration01.json').relative_to(ROOT)), sha256=args.registration_sha256), dict(path=str(args.review.relative_to(ROOT)), sha256=args.review_sha256)]
        for ref in joined:
            body = subprocess.check_output(['git', '-C', str(ROOT), 'cat-file', 'blob', head + ':' + ref['path']])
            if hashlib.sha256(body).hexdigest() != ref['sha256']:
                raise ValueError('source/config/review is not committed exactly')
        output.mkdir(parents=True, exist_ok=False)
        write(output / 'claim.json', dict(identity=config['identity'], source=head, registration=args.registration_sha256, review=args.review_sha256, started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), family=config['family'], allowance=1, financial_credit=False, scientific_owner=None))
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'worker', '--registration-sha256', args.registration_sha256, '--source', head]
        from tradingagents.research.onchain_replication.resources import guarded_run
        try:
            state = guarded_run(command, cwd=output, receipt_dir=guard, memory_max_bytes=config['limits']['memory_max_bytes'], memory_high_bytes=config['limits']['memory_high_bytes'], reserve_bytes=config['limits']['reserve_bytes'], start_reserve_bytes=config['limits']['startup_bytes'], disk_paths=(ROOT, output), disk_floor_bytes=config['limits']['disk_floor_bytes'], wall_seconds=config['limits']['wall_seconds'], storage_budget={'root':str(output), 'limits':config['storage_limits']}, native_unit_limits={'file_size_bytes':config['limits']['file_size_bytes']})
            complete = state['phase'] == 'complete' and state['child_exit_code'] == 0
            write(output / 'terminal.json', dict(identity=config['identity'], disposition='COMPLETE' if complete else 'FAILED', guard=state, financial_credit=False, scientific_owner=None))
            return 0 if complete else 1
        except BaseException as error:
            write(output / 'parent-failed.json', dict(identity=config['identity'], error=repr(error), disposition='FAILED', financial_credit=False))
            raise
    from tradingagents.research.onchain_replication.resources import assert_guarded_worker
    command = list(sys.orig_argv)
    assert_guarded_worker(guard, command, required_paths=(ROOT, output), wall_seconds=config['limits']['wall_seconds'], memory_max_bytes=config['limits']['memory_max_bytes'], memory_high_bytes=config['limits']['memory_high_bytes'], disk_floor_bytes=config['limits']['disk_floor_bytes'])
    if not (output / 'claim.json').is_file():
        raise ValueError('engineering claim absent')
    manifest = ROOT / config['graph']['path']
    source_paths = [manifest] + [manifest.parent / item['path'] for item in config['graph']['arrays'].values()]
    stat_fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    before = {str(p):[getattr(p.stat(), name) for name in stat_fields] for p in source_paths}
    from tradingagents.research.onchain_replication.graph_store import load_graph
    from tradingagents.research.onchain_replication.neighborhoods import graph_hash, node_order_hash
    candidate_path = ROOT / config['candidate']['path']
    spec = importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._engineering_hash_candidate', candidate_path)
    candidate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = candidate
    spec.loader.exec_module(candidate)
    measurements = []
    graph = None
    try:
        start = time.perf_counter()
        graph = load_graph(manifest, config['graph']['sha256'], resident=True)
        measurements.append(dict(phase='load_authentication_including_one_legacy_hash', seconds=time.perf_counter()-start))
        write(output / 'phase01.json', measurements[-1])
        for number, (name, operation) in enumerate([('legacy_graph_hash', graph_hash), ('candidate_graph_hash', candidate.graph_hash)], 2):
            start = time.perf_counter()
            actual = operation(graph)
            elapsed = time.perf_counter()-start
            cell = dict(phase=name, seconds=elapsed, digest=actual, expected=config['graph']['graph_hash'], matches=actual==config['graph']['graph_hash'], payload_bytes=config['graph']['payload_bytes'], payload_bytes_per_second=config['graph']['payload_bytes']/elapsed)
            measurements.append(cell)
            write(output / ('phase%02d.json' % number), cell)
            if not cell['matches']:
                raise ValueError('canonical graph identity differs')
        start = time.perf_counter()
        order = node_order_hash(graph.node_ids)
        measurements.append(dict(phase='node_order_hash', seconds=time.perf_counter()-start, digest=order))
        write(output / 'phase04.json', measurements[-1])
        after = {str(p):[getattr(p.stat(), name) for name in stat_fields] for p in source_paths}
        if after != before:
            raise ValueError('original graph metadata changed during profile')
        write(output / 'result.json', dict(identity=config['identity'], measurements=measurements, nodes=len(graph.node_ids), edges=int(graph.edge_index.shape[1]), graph=config['graph'], original_metadata_unchanged=True, timing_order='one load with implicit legacy hash, one explicit legacy hash, one candidate hash, one node-order hash; warm serial observations', financial_credit=False, qualification='Hash timing only. Payload throughput uses original NPY file bytes, including headers; it is not emitted JSON throughput. No MCM throughput, seven-graph lease capacity, full callbacks, training or financial fit evidence.'))
        return 0
    except BaseException as error:
        write(output / 'worker-failed.json', dict(identity=config['identity'], error=repr(error), completed_phases=measurements, disposition='FAILED', financial_credit=False))
        raise


if __name__ == '__main__':
    sys.exit(main())
