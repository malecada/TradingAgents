"""Fresh tiny actual-engine integration with compact history, not a fit job."""
import numpy as np
from tests.research.onchain_replication.test_mcm_score_stream import fixture, POLICY as MCM_POLICY
from tests.research.onchain_replication.test_compact_matcher import CONTEXT, POLICY, SCHEDULE
from tradingagents.research.onchain_replication.compact_pair_log import PairLog, verify
from tradingagents.research.onchain_replication.compact_matcher import CompactMatcher, scope
from tradingagents.research.onchain_replication.mcm_score_stream import MCMScoreStream


def test_actual_checkpoint_engine_to_mcm_stream_preserves_results_without_pair_directories(tmp_path):
    base, f, d, kernel = fixture()
    oracle = base.Scores(f.match)
    expected = f.m.mcm(f.g, d, f.match, **f.kw, score_pair=oracle)
    matcher = None
    stream = MCMScoreStream(tmp_path / 'stream', graph=f.g, dictionary=d,
        matching_config=f.match, workflow=f.kw['workflow'], backend=f.kw['backend'],
        owner='e' * 64, chunk_cells=4, compute=lambda p, a, b: matcher(p, a, b), lease=lambda: None)
    policy = POLICY | {'normalization_chunk_entries': 64}
    log = PairLog(tmp_path / 'matching', owner='e' * 64,
        scope=scope(f.match, CONTEXT, policy, stream.workload, SCHEDULE),
        limits={'chunk_events': 16, 'max_events': 100, 'max_pairs': 14, 'max_logical_bytes': 40000},
        max_iterations=f.match['max_iterations'], lease=lambda: None)
    matcher = CompactMatcher(log, config=f.match, context=CONTEXT, policy=policy,
        workload_sha256=stream.workload, schedule=SCHEDULE, lease=lambda: None)
    result = kernel.mcm(f.g, d, f.match, **f.kw, score_pair=stream,
        policy=MCM_POLICY, lease=lambda: None)
    stream_receipt = stream.finish(); ref = log.finish()
    proof = verify(tmp_path / 'matching', owner='e' * 64, scope=log.start['scope'],
        terminal_sha256=ref, lease=lambda: None)
    np.testing.assert_array_equal(result['mcm'], expected)
    assert stream_receipt['cells'] == 14 and proof['completed_pairs'] == 14
    assert proof['events'] == 28 and proof['chunks'] == 2 and proof['record_bytes'] == 4704
    assert proof['progress_events'] == 0
    assert not list((tmp_path / 'checkpoints').iterdir())
    assert not list(tmp_path.glob('**/owner.json')) and not list(tmp_path.glob('**/artifact-*'))
