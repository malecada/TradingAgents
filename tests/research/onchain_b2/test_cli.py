import json

import pyarrow as pa

from tradingagents.research.onchain_b2 import cli, s3source

A, B, E = '0x' + 'a' * 40, '0x' + 'b' * 40, '0x' + 'e' * 40


def _day(day):
    return pa.table({'hash': ['0x' + f'{hash(day) % 10**10:064x}'], 'block_timestamp': pa.array([0], pa.timestamp('ns')),
                     'from_address': [A], 'to_address': [B], 'value': [1e18], 'receipt_status': [1]})


def _setup(tmp_path, monkeypatch, fail_day=None):
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    (tmp_path / 'labels').mkdir()
    (tmp_path / 'labels' / 'labels.json').write_text(json.dumps({E: {'name': 'X', 'added': None, 'sources': ['spellbook']}}))

    def fake_read(day, *, scratch, **kw):
        if day == fail_day:
            raise s3source.DayUnavailable(day, ['boom'])
        return _day(day), {'day': day, 'source': 'test', 'rows': 1}

    monkeypatch.setattr(s3source, 'read_day', fake_read)


def test_weeks_stage_builds_and_skips(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-10', '--workers', '1'])
    s = json.loads((tmp_path / 'weeks' / '2019-06-03.json').read_text())
    assert s['f1']['f1_transfers'] == 7 and len(s['receipts']) == 7 and (tmp_path / 'graphs' / '2019-06-03' / 'summary.json').exists()
    m = (tmp_path / 'weeks' / '2019-06-03.json').stat().st_mtime
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03', '--workers', '1'])
    assert (tmp_path / 'weeks' / '2019-06-03.json').stat().st_mtime == m


def test_unavailable_day_marks_week_and_continues(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, fail_day='2019-06-05')
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-10', '--workers', '1'])
    bad = json.loads((tmp_path / 'weeks' / '2019-06-03.unavailable.json').read_text())
    assert bad['day'] == '2019-06-05' and not (tmp_path / 'weeks' / '2019-06-03.json').exists()
    assert (tmp_path / 'weeks' / '2019-06-10.json').exists()


def test_stale_graph_without_summary_is_rebuilt(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    (tmp_path / 'graphs' / '2019-06-03').mkdir(parents=True)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03', '--workers', '1'])
    assert (tmp_path / 'weeks' / '2019-06-03.json').exists() and (tmp_path / 'graphs' / '2019-06-03' / 'x.npy').exists()

def test_any_week_error_is_isolated_and_recorded(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    real = s3source.read_day

    def bad(day, *, scratch, **kw):
        if day == '2019-06-05':
            raise ValueError('duplicate transaction hash in day')
        return real(day, scratch=scratch, **kw)

    monkeypatch.setattr(s3source, 'read_day', bad)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-10', '--workers', '1'])
    failed = json.loads((tmp_path / 'weeks' / '2019-06-03.failed.json').read_text())
    assert 'duplicate transaction hash' in failed['error'] and 'Traceback' in failed['traceback']
    assert (tmp_path / 'weeks' / '2019-06-10.json').exists()
    log = [json.loads(l) for l in (tmp_path / 'logs' / 'weeks.jsonl').read_text().splitlines()]
    assert any(e.get('status') == 'failed' for e in log) and all('peak_rss_mb' in e for e in log if e.get('event') == 'week')


def test_success_clears_stale_markers(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    (tmp_path / 'weeks').mkdir()
    (tmp_path / 'weeks' / '2019-06-03.unavailable.json').write_text('{}')
    (tmp_path / 'weeks' / '2019-06-03.failed.json').write_text('{}')
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03', '--workers', '1'])
    assert not (tmp_path / 'weeks' / '2019-06-03.unavailable.json').exists() and not (tmp_path / 'weeks' / '2019-06-03.failed.json').exists()


def test_week_status_reasons(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    (tmp_path / 'weeks').mkdir()
    (tmp_path / 'mcm').mkdir()
    (tmp_path / 'weeks' / 'w1.unavailable.json').write_text(json.dumps({'day': 'd1'}))
    (tmp_path / 'weeks' / 'w2.failed.json').write_text(json.dumps({'error': 'ValueError()'}))
    (tmp_path / 'weeks' / 'w3.json').write_text('{}')
    (tmp_path / 'weeks' / 'w4.json').write_text('{}')
    (tmp_path / 'mcm' / 'w4.npy').write_bytes(b'')
    assert cli.week_status('w1') == 'unavailable: d1' and cli.week_status('w2') == 'failed: ValueError()'
    assert cli.week_status('w3') == 'no_mcm' and cli.week_status('w4') is None and cli.week_status('w5') == 'not_built'


def test_pool_uses_fresh_forkserver_workers(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    seen = {}

    class FakePool:
        def __init__(self, n, **kw):
            seen.update(n=n, **kw)
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def map(self, fn, jobs):
            return [fn(j) for j in jobs]

    monkeypatch.setattr(cli, 'ProcessPoolExecutor', FakePool)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03', '--workers', '2'])
    assert seen['n'] == 2 and seen['max_tasks_per_child'] == 1 and seen['mp_context'].get_start_method() == 'forkserver'


def test_broken_pool_is_logged_and_exits(tmp_path, monkeypatch):
    import pytest
    from concurrent.futures.process import BrokenProcessPool
    _setup(tmp_path, monkeypatch)

    class DeadPool:
        def __init__(self, *a, **k):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def map(self, fn, jobs):
            raise BrokenProcessPool('worker killed')

    monkeypatch.setattr(cli, 'ProcessPoolExecutor', DeadPool)
    with pytest.raises(SystemExit):
        cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03', '--workers', '2'])
    assert '"pool_broken"' in (tmp_path / 'logs' / 'weeks.jsonl').read_text()


def test_cli_import_does_not_load_torch():
    import subprocess, sys
    out = subprocess.run([sys.executable, '-c', 'import sys, tradingagents.research.onchain_b2.cli; print("torch" in sys.modules)'],
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == 'False'


def test_screen_refuses_to_overwrite_selection(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    monkeypatch.setattr(cli, 'STUDY', tmp_path)
    (tmp_path / 'selection.json').write_text('{"selected": []}')
    with pytest.raises(SystemExit, match='exists'):
        cli.main(['screen'])


def test_holdout_is_one_shot(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    monkeypatch.setattr(cli, 'STUDY', tmp_path)
    (tmp_path / 'screen').mkdir()
    (tmp_path / 'screen' / 'holdout.lock.json').write_text('{}')
    with pytest.raises(SystemExit, match='already opened'):
        cli.main(['holdout'])
