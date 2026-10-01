"""Fresh tiny synthetic MCM adapter cases, not historical job reruns."""
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
SOURCES = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def fixture():
    base = load('stream_synthetic_fixture', SOURCES / 'pair-workload-2026-09-30/test_workload.py')
    f = base.Tests(); f.setUp()
    dictionary = f.fit(base.Scores(f.match))['dictionary']
    kernel = load('stream_kernel', SOURCES / 'mcm-array-kernel-2026-10-01/kernel.py')
    return base, f, dictionary, kernel


def stream(tmp_path, f, d, compute):
    from tradingagents.research.onchain_replication.mcm_score_stream import MCMScoreStream
    return MCMScoreStream(tmp_path / 'stream', graph=f.g, dictionary=d,
        matching_config=f.match, workflow=f.kw['workflow'], backend=f.kw['backend'],
        owner='e' * 64, chunk_cells=4, compute=compute, lease=lambda: None)


POLICY = {'schema_version': 1, 'max_buffer_bytes': 100000, 'edge_chunk': 2,
          'max_output_bytes': 56, 'max_numeric_bytes': 100056}


def test_actual_mcm_kernel_preserves_all_scalar_values_purposes_and_final_float32(tmp_path):
    base, f, d, kernel = fixture(); expected_calls = base.Scores(f.match)
    expected = f.m.mcm(f.g, d, f.match, **f.kw, score_pair=expected_calls)
    actual_calls = base.Scores(f.match); sink = stream(tmp_path, f, d, actual_calls)
    result = kernel.mcm(f.g, d, f.match, **f.kw, score_pair=sink, policy=POLICY, lease=lambda: None)
    receipt = sink.finish()
    np.testing.assert_array_equal(result['mcm'], expected)
    assert result['mcm'].dtype == np.float32
    assert actual_calls.asked == expected_calls.asked and len(actual_calls.computed) == 14
    from tradingagents.research.onchain_replication import score_tail
    recovered = []; purposes = []
    for index in range(receipt['chunks']):
        link = json.loads((tmp_path / f'stream/seal-{index:012d}.json').read_text())
        ref = link['tail_terminal_sha256']
        got = score_tail.verify(tmp_path / f'stream/tails/tail-{index:012d}',
            scope=sink.scope, owner='e' * 64, terminal_sha256=ref, lease=lambda: None)
        recovered.extend(got['values'])
        purposes.extend(bytes(row).hex() for row in got['purpose_hashes'])
    assert purposes == [base.cache_key(p) for p in expected_calls.asked]
    exact = np.array([expected_calls.saved[key]['score'] for key in purposes], dtype='<f8')
    assert np.array(recovered, dtype='<f8').tobytes() == exact.tobytes()
    np.testing.assert_array_equal(np.array(recovered, dtype=np.float32).reshape(7, 2), expected)
    assert receipt['cells'] == 14 and receipt['chunks'] == 4


def test_matcher_failure_preserves_tail_and_blocks_further_compute(tmp_path):
    base, f, d, kernel = fixture(); calls = []
    def fail(p, a, b):
        calls.append(p)
        raise RuntimeError('synthetic matcher cleanup failed')
    sink = stream(tmp_path, f, d, fail)
    with pytest.raises(RuntimeError, match='cleanup'):
        kernel.mcm(f.g, d, f.match, **f.kw, score_pair=sink, policy=POLICY, lease=lambda: None)
    assert len(calls) == 1
    with pytest.raises(ValueError): sink(calls[0], None, None)
    assert len(calls) == 1
    assert (tmp_path / 'stream/tails/tail-000000000000/records.bin').stat().st_size == 0
    assert not (tmp_path / 'stream/complete.json').exists()


def test_wrong_occurrence_rejected_before_matcher_dispatch(tmp_path):
    base, f, d, kernel = fixture(); seen = base.Scores(f.match)
    f.m.mcm(f.g, d, f.match, **f.kw, score_pair=seen)
    sink = stream(tmp_path, f, d, lambda *args: pytest.fail('wrong-order matcher called'))
    with pytest.raises(ValueError): sink(seen.asked[1], None, None)
    sink.close()


@pytest.mark.parametrize('target', ['batch', 'link'])
def test_late_completion_mutation_cannot_return_success(tmp_path, target):
    base, f, d, kernel = fixture(); sink = stream(tmp_path, f, d, base.Scores(f.match))
    kernel.mcm(f.g, d, f.match, **f.kw, score_pair=sink, policy=POLICY, lease=lambda: None)
    def lease():
        if (tmp_path / 'stream/complete.json').exists():
            path = tmp_path / ('stream/batches/chunk-000000000000.bin' if target == 'batch'
                else 'stream/seal-000000000000.json')
            path.write_bytes(b'x' * path.stat().st_size)
    sink.lease = lease
    with pytest.raises(ValueError): sink.finish()


def test_late_seal_link_lease_mutation_refuses_callback_success(tmp_path):
    base, f, d, kernel = fixture(); calls = base.Scores(f.match)
    sink = stream(tmp_path, f, d, calls)
    def lease():
        if (tmp_path / 'stream/seal-000000000000.json').exists():
            (tmp_path / 'stream/batches/chunk-000000000000.bin').write_bytes(b'x' * 32)
    sink.lease = lease
    with pytest.raises(ValueError):
        kernel.mcm(f.g, d, f.match, **f.kw, score_pair=sink, policy=POLICY, lease=lambda: None)
    assert len(calls.computed) == 4
