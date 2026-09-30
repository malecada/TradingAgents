"""Guarded sequential verification of two saved legacy graphs; never rebuilds."""
import argparse
import os
import time

from arrays import verify
from release import (ROOT, RECEIPT, source_check, live_guard, load_metadata,
                     unchanged, write_new, require, reserve_dir)


def main(source):
    output = RECEIPT/'payload'
    reserve_dir(output)  # any existing partial/terminal refuses
    write_new(output/'started.json', {'pid':os.getpid(),'source_commit':source})
    started = time.monotonic()
    try:
        binding = source_check(source)
        live_guard(source, binding)
        metadata, signatures = load_metadata()
        summaries = []
        for graph in metadata['graphs']:
            live_guard(source, binding); unchanged(signatures)
            expected_bytes = sum(a['declared_bytes'] for a in graph['arrays'])
            result = verify(ROOT/graph['manifest']['path'],
                            expected_manifest_sha256=graph['manifest']['sha256'],
                            expected_array_bytes=expected_bytes, max_array_bytes=562558280)
            require(result['graph_hash'] == graph['graph_hash'] and result['nodes'] == graph['nodes']
                    and result['directed_edges'] == graph['directed_edges']
                    and result['admitted_transactions'] == graph['metadata']['admitted_count']
                    and result['array_mappings_closed'], 'verified graph summary mismatch')
            live_guard(source, binding); unchanged(signatures)
            result.update(week=graph['week'], status='complete', manifest_sha256=graph['manifest']['sha256'])
            write_new(output/(graph['week']+'.json'), result)
            summaries.append(result)
        require(source_check(source) == binding, 'final source binding mismatch')
        live_guard(source, binding); unchanged(signatures)
        write_new(output/'complete.json', {
            'status':'complete', 'source_commit':source,'bindings_sha256':binding,
            'graphs':summaries,'historical_dispositions':metadata['historical_dispositions'],
            'elapsed_seconds':time.monotonic()-started,'empirical_trials':0,
            'qualification':'Independent saved-array identity, structure and aggregate conservation only. Original FAILED pilot and all109 historical cells retained. Raw transactions, values, uniqueness and exclusion semantics not independently audited. No fit, rebuild, sample or future reuse admission.'})
    except BaseException as exc:
        write_new(output/'failed.json', {'status':'failed','type':type(exc).__name__,
                  'reason':str(exc),'source_commit':source,'elapsed_seconds':time.monotonic()-started})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    main(parser.parse_args().source)
