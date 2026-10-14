import json

import numpy as np
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b2 import s3source
from tradingagents.research.onchain_b3 import cli

A, B, C, E = ('0x' + c * 40 for c in 'abce')


def _day(day):
    rows = [(A, B, 1.0), (B, C, 2.0), (C, A, 1.0), (A, E, 3.0)]
    return pa.table({'hash': ['0x' + f'{abs(hash((day, i))) % 10**12:064x}' for i in range(len(rows))],
                     'block_timestamp': pa.array([0] * len(rows), pa.timestamp('ns')),
                     'from_address': [r[0] for r in rows], 'to_address': [r[1] for r in rows],
                     'value': [r[2] * 1e18 for r in rows], 'receipt_status': [1] * len(rows)})


def _setup(tmp_path, monkeypatch, fail=None):
    art, b2 = tmp_path / 'b3', tmp_path / 'b2'
    (b2 / 'labels').mkdir(parents=True)
    (b2 / 'labels' / 'labels.json').write_text(json.dumps({E: {'name': 'X', 'added': None, 'sources': ['spellbook']}}))
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli, 'B2', b2)

    def fake(day, *, scratch, **kw):
        if fail and day == fail[0]:
            raise fail[1]
        return _day(day), {'day': day, 'source': 'test', 'rows': 4}

    monkeypatch.setattr(s3source, 'read_day', fake)
    return art


def test_week_build_writes_summary_graph_and_keys(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03'])
    s = json.loads((art / 'weeks' / '2019-06-03.json').read_text())
    assert s['f1']['f1_transfers'] == 28 and 'f4_transitivity' in s['f4'] and len(s['receipts']) == 7
    assert np.load(art / 'keys' / '2019-06-03.npy').dtype == np.uint64 and (art / 'graphs' / '2019-06-03' / 'summary.json').exists()


def test_failures_are_recorded_and_isolated(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch, fail=('2019-06-05', ValueError('duplicate transaction hash in day')))
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-10'])
    assert 'duplicate' in json.loads((art / 'weeks' / '2019-06-03.failed.json').read_text())['error']
    assert (art / 'weeks' / '2019-06-10.json').exists()


def test_late_stages_refuse_incomplete_capture(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03'])
    for stage in (['history'], ['mcm', '--shard', '0/1'], ['features']):
        with pytest.raises(SystemExit, match='capture incomplete'):
            cli.main(stage)


def test_screen_never_overwrites_selection(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, 'STUDY', tmp_path)
    (tmp_path / 'selection.json').write_text('{"selected": []}')
    with pytest.raises(SystemExit, match='exists'):
        cli.main(['screen'])


def test_cli_import_does_not_load_torch():
    import subprocess, sys
    out = subprocess.run([sys.executable, '-c', 'import sys, tradingagents.research.onchain_b3.cli; print("torch" in sys.modules)'],
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == 'False'