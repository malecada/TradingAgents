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