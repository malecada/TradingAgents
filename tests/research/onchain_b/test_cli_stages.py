import json

import pyarrow as pa

from tradingagents.research.onchain_b import cli
from tradingagents.research.onchain_b import weekly as W


def test_build_graphs_writes_week_and_skips_existing(tmp_path, monkeypatch):
    A, B = '0x' + 'a' * 40, '0x' + 'b' * 40
    day = pa.table({'hash': ['0x' + '1' * 64], 'block_timestamp': pa.array([0], pa.timestamp('ns')),
                    'from_address': [A], 'to_address': [B], 'value': [1e18], 'receipt_status': [1]})
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    monkeypatch.setattr(cli, '_read_day_tables', lambda week, scratch: [day] * 7)
    cli.main(['build-graphs', '--weeks', '2022-01-03', '--k', '10'])
    g = W.load(tmp_path / 'graphs' / '2022-01-03')
    assert g.n == 2 and g.summary['k_effective'] == 2 and len(g.summary['day_counters']) == 7
    mtime = (tmp_path / 'graphs' / '2022-01-03' / 'summary.json').stat().st_mtime
    cli.main(['build-graphs', '--weeks', '2022-01-03', '--k', '10'])       # second run must skip
    assert (tmp_path / 'graphs' / '2022-01-03' / 'summary.json').stat().st_mtime == mtime
    log = [json.loads(line) for line in (tmp_path / 'logs' / 'build-graphs.jsonl').read_text().splitlines()]
    assert any(e.get('event') == 'week_done' for e in log) and any(e.get('event') == 'week_skip' for e in log)
    assert all('rss_mb' in e for e in log)


def test_every_stage_caps_torch_threads(tmp_path, monkeypatch):
    import torch
    torch.set_num_threads(8)
    seen = {}
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    monkeypatch.setattr(cli, 'calibrate', lambda args: seen.setdefault('threads', torch.get_num_threads()))
    cli.main(['calibrate'])
    assert seen['threads'] == 2


def test_dictionary_weeks_are_exactly_the_training_weeks():
    # spec §10: dictionary sampling never reads a week first used by a 2024 decision (2023-12-25 is test-only)
    from tradingagents.research.onchain_b import calendar as cal
    used = sorted({cal.available_week(t) for d in cal.decision_dates('train') for t in cal.window(d)})
    weeks = cli._training_weeks()
    assert weeks == used and len(weeks) == 103 and weeks[-1] == '2023-12-18'
    assert '2023-12-25' not in weeks


def test_build_graphs_refuses_without_frozen_k(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    monkeypatch.setattr(cli.config, 'load', lambda name: {'paper_scale': {'K': None}} if name == 'graph' else {})
    with pytest.raises(SystemExit, match='not frozen'):
        cli.main(['build-graphs', '--weeks', '2022-01-03'])
