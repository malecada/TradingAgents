"""Queued finite synthetic qualification, not Admission or empirical authority.

Root executes once only after pilot34 is terminal, its outcome is accepted and
recovered, and the exact candidate sources have passed independent review.
Uses the real sealed EdgeOwner, immutable edge features, and the unchanged
reference kernel; no original graphs, motif samples, labels or checkpoints.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
UNIT = Path('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/onchain-replication-fe7cc2c021214ecd95832df0cf59b482.service')
RUN = ROOT/'research_runs/eth-paper-real-data-end-to-end-resource-20261011-34'
PACKAGE = 'tradingagents.research.onchain_replication'


def require(value, message):
    if not value:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def pinned(path, expected):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    require(0 < len(raw) <= 4*1024**2 and hashlib.sha256(raw).hexdigest() == expected, 'source pin differs')
    return path


def load(name, path):
    require(name not in sys.modules, 'qualification module already loaded')
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, 'source loader unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner', required=True)
    parser.add_argument('--owner-sha256', required=True)
    parser.add_argument('--kernel', required=True)
    parser.add_argument('--kernel-sha256', required=True)
    parser.add_argument('--baseline-sha256', required=True)
    parser.add_argument('--policy', required=True)
    parser.add_argument('--policy-sha256', required=True)
    args = parser.parse_args()
    # Refusal before any new case namespace or numerical/native import.
    require(not UNIT.exists() and any((RUN/name).is_file() for name in ('complete.json', 'failed.json')), 'pilot34 remains active or terminal unknown')
    require(os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize >= 10*1024**3, '10 GiB disk floor')
    owner_path = pinned(args.owner, args.owner_sha256)
    kernel_path = pinned(args.kernel, args.kernel_sha256)
    baseline_path = pinned(ROOT/'tradingagents/research/onchain_replication/matching_annealing.py', args.baseline_sha256)
    policy_path = pinned(args.policy, args.policy_sha256)
    selected = json.loads(policy_path.read_bytes())
    out = Path(__file__).resolve().parent/'attempt01'
    out.mkdir(mode=0o700, exist_ok=False)
    started = time.monotonic()
    phases = []
    checks = []
    failure = None
    failed = False
    primary = None
    secondary = []
    owner = lease = None
    result_path = out/'RESULT01.json'
    try:
        resource.setrlimit(resource.RLIMIT_FSIZE, (4*1024**2, 4*1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (50, 55))
        resource.setrlimit(resource.RLIMIT_AS, (1536*1024**2, 1536*1024**2))
        os.sched_setaffinity(0, {0, 1})
        for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            os.environ[key] = '1'
        sys.path.insert(0, str(ROOT))
        import numpy as np
        import scipy
        from tradingagents.research.onchain_replication import matching_annealing as original
        from tradingagents.research.onchain_replication import matching_reference
        from tradingagents.research.onchain_replication.contracts import AttributedGraph
        require(Path(original.__file__).resolve() == baseline_path, 'original kernel path differs')
        owner_module = load(PACKAGE+'._qualification_edge_owner', owner_path)
        candidate = load(PACKAGE+'._qualification_edge_kernel', kernel_path)
        owner = owner_module.EdgeOwner(selected, numpy=np, scipy=scipy, agreement=matching_reference.agreement)
        phases.append({'phase': 'actual-sealed-owner-borrow', 'elapsed_seconds': time.monotonic()-started})
        lease = owner.borrow(object())
        owner.current()
        lease.current()
        # Real borrow refusal and expiry; no synthetic authority is introduced.
        try:
            owner.borrow(object())
        except ValueError:
            checks.append('concurrent-borrow-refused')
        else:
            raise AssertionError('concurrent borrow accepted')
        # The active-borrow refusal precedes acquisition and leaves the original
        # successful lease available. Keep exactly one actual native owner.
        config = dict(alpha=1., beta0=1., beta_final=30., beta_rate=.075,
                      max_iterations=50, normalization_iterations=1,
                      solver='algorithm1_literal', max_pair_entries=1024)

        def immutable(array):
            return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)

        def graph(bad=False):
            edges = np.arange(18, dtype=np.float64).reshape(9, 2)/32
            if bad:
                edges[5, 0] = 1e200
            return AttributedGraph(('a', 'b', 'c'), immutable(np.zeros((3, 2))),
                                   immutable(np.array([(i, j) for i in range(3) for j in range(3)], dtype=np.int64).T.copy()),
                                   immutable(edges), '0'*64, 'a')

        def equal(left, right):
            require(set(left) == set(right), 'state keys differ')
            for key in left:
                a, b = left[key], right[key]
                if type(a) is np.ndarray:
                    require(a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(), 'state array differs: '+key)
                else:
                    require(a == b, 'state metadata differs: '+key)

        counts = {'accepted': 0, 'declined': 0}

        def fill(*values):
            accepted = lease.fill(*values)
            counts['accepted' if accepted else 'declined'] += 1
            return accepted

        a, b = graph(), graph()
        require(not a.edge_features.flags.writeable and not b.edge_features.flags.writeable, 'fixture fails native eligibility')
        x = original.create(a, b, config, max_state_bytes=4096)
        y = original.create(a, b, config, max_state_bytes=4096)
        baseline_seconds = accelerated_seconds = current_seconds = 0.
        for index in range(512):
            original.check(x, a, b, config)
            candidate.check(y, a, b, config)
            start = time.monotonic()
            u = original._advance_checked(x, a, b, config, max_operations=32)
            baseline_seconds += time.monotonic()-start
            start = time.monotonic()
            lease.current()
            current_seconds += time.monotonic()-start
            start = time.monotonic()
            v = candidate._advance_checked(y, a, b, config, max_operations=32, edge_chunk_fill=fill)
            accelerated_seconds += time.monotonic()-start
            lease.current()
            require(u == v, 'logical operation count differs')
            equal(x, y)
            if x['phase'] == 'done':
                break
        else:
            raise AssertionError('finite 512-advance bound exhausted')
        require(counts['accepted'] > 0, 'no actual native chunk was used')
        left, right = original.harden(x['M']), candidate.harden(y['M'])
        require(np.array_equal(left, right), 'assignment differs')
        require(original.score_assignment(a, b, left, config) == candidate.score_assignment(a, b, right, config), 'score differs')
        checks.append({'completed_advances': index+1, 'chunks': counts,
                       'all_boundary_states_bitwise_equal': True,
                       'assignment_and_score_equal': True,
                       'baseline_kernel_seconds': baseline_seconds,
                       'candidate_kernel_seconds': accelerated_seconds,
                       'one_of_two_current_checks_seconds': current_seconds,
                       'representative_real_data_speedup': None})
        a, b = graph(), graph(True)
        x = original.create(a, b, config, max_state_bytes=4096)
        y = original.create(a, b, config, max_state_bytes=4096)
        original._advance_checked(x, a, b, config, max_operations=10)
        candidate._advance_checked(y, a, b, config, max_operations=10)
        errors = []
        for state, engine, kwargs in ((x, original, {}), (y, candidate, {'edge_chunk_fill': fill})):
            try:
                engine._advance_checked(state, a, b, config, max_operations=32, **kwargs)
            except BaseException as error:
                errors.append((type(error).__name__, str(error)))
        require(len(errors) == 2 and errors[0] == errors[1] and errors[0][0] == 'OverflowError', 'late original error differs or missing')
        equal(x, y)
        checks.append({'late_original_error': errors[0], 'prefix_cursor': x['cursor'], 'prefix_state_equal': True})
        lease.close()
        try:
            lease.current()
        except ValueError:
            checks.append('expired-borrow-refused')
        else:
            raise AssertionError('expired borrow accepted')
    except BaseException as error:
        failed = True
        primary = error
        try:
            failure = {'type': type(error).__name__, 'message': str(error),
                       'notes': list(getattr(error, '__notes__', ()))}
        except BaseException as reporting_error:
            secondary.append(reporting_error)
    finally:
        for value in (lease, owner):
            if value is None:
                continue
            try:
                value.close()
            except BaseException as error:
                failed = True
                if primary is None:
                    primary = error
                else:
                    secondary.append(error)
                try:
                    record = {'type': type(error).__name__, 'message': str(error)}
                    if failure is None:
                        failure = record
                    else:
                        failure.setdefault('cleanup_errors', []).append(record)
                except BaseException as reporting_error:
                    secondary.append(reporting_error)
        try:
            result = {'identity': 'edge-owner-and-kernel-qualification-20261011-02',
                      'status': 'FAILED' if failed else 'PASS_FINITE_SYNTHETIC',
                      'checks': checks, 'phases': phases, 'failure': failure,
                      'reporting_errors': [type(error).__name__ for error in secondary],
                      'elapsed_seconds': time.monotonic()-started,
                      'ru_maxrss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      'actual_genuine_scientific_owner': None, 'actual_financial_trial': None,
                      'whole_graph_capacity': None, 'whole_pilot_complete': False}
            with result_path.open('xb') as handle:
                handle.write(encoded(result))
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException as reporting_error:
            failed = True
            if primary is None:
                primary = reporting_error
            else:
                secondary.append(reporting_error)
        if primary is not None:
            for reporting_error in secondary:
                try:
                    BaseException.add_note(primary, 'qualification reporting failure: '+repr(reporting_error))
                except BaseException:
                    pass
            raise primary
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
