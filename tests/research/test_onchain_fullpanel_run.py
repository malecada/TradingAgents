"""Synthetic process-boundary runner checks with the real exact-hash append."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

HERE = Path(__file__).resolve().parents[2]/'research/onchain-graph-2026-09-16/fullpanel'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


with patch.dict(sys.modules, {name: load('runner_test_'+name, HERE/(name+'.py')) for name in ['admission', 'hash_audit', 'source']}):
    runner = load('fullpanel_run_test', HERE/'run.py')


class Run:
    def __init__(self, root):
        self.directory = root/'run'
        (self.directory/'outputs').mkdir(parents=True)
        self.publications = []

    def write_json(self, name, value):
        runner.storage.atomic_json(self.directory/'outputs'/name, value)
        self.publications.append(name)

    def read(self, name):
        return json.loads((self.directory/'outputs'/name).read_bytes())


def setup(root, monkeypatch, *, duplicate=False, failure=None, wrong_digest=False, unavailable=None):
    (root/runner.BASE).mkdir(parents=True)
    dates = ['2022-01-01', '2022-01-02', '2022-01-03']
    plan = dict(dates=dates, hash_root=str(root/'hashes'), expected_rows={d: 1 for d in dates},
                expected_total_rows=3, expected_hash_bytes=96, expected_graph_unavailable=[dates[0], dates[-1]],
                limits=dict(min_free_bytes=0, max_scratch_bytes=1024**2, max_derived_bytes=10*1024**2, max_hash_bytes=1024**2))
    run = Run(root)
    calls = []
    def command(command, check, cwd):
        assert check and cwd == root
        args = {command[i]: command[i+1] for i in range(3, len(command), 2)}
        if command[2].endswith('/day.py'):
            date = args['--date']
            calls.append(('extract', date))
            if date == failure:
                raise subprocess.CalledProcessError(1, command)
            index = dates.index(date)
            value = (1 if duplicate else index+1).to_bytes(32, 'big')
            path = root/args['--phase']
            path.parent.mkdir(parents=True)
            meta = runner.storage.write_blob(path.parent/'hashes.zst', value)
            meta.update(path=str((path.parent/'hashes.zst').relative_to(root)), hashes=1)
            edge = date in plan['expected_graph_unavailable'] or date == unavailable
            source = dict(date=date, status='complete', integrity={'rows': 1},
                          activity=dict(events=1, nodes=2, directed_pairs=1), transaction_hashes=[meta], prefix=[])
            count = dict(status='unavailable' if edge else 'complete', reason='boundary unavailable' if edge else None,
                         features=dict(local40_sums=[0]*40, overlap_node_count=2, nonzero_nodes=0))
            runner.storage.atomic_json(path, dict(date=date, source=source, count=count))
        else:
            path = root/args['--phase']
            phase = json.loads(path.read_bytes())
            calls.append(('check', phase['date']))
            meta = phase['source']['transaction_hashes'][0]
            raw = runner.storage.read_blob(root/meta['path'], meta)
            report = dict(date=phase['date'], passed=True, phase_sha256=runner.sha(path), source_rows=1,
                          count_verified=phase['count']['status']=='complete', source_hash_digest='0'*64 if wrong_digest else hashlib.sha256(raw).hexdigest())
            runner.storage.atomic_json(Path(args['--report']), report)
    monkeypatch.setattr(runner.subprocess, 'run', command)
    # Tiny temporary fixtures do not require an empirical disk reservation.
    monkeypatch.setattr(runner.hash_audit, 'FREE_FLOOR_BYTES', 0)
    return run, plan, calls


def test_publication_and_hash_receipt_precede_cleanup_edges_preserved(tmp_path, monkeypatch):
    run, plan, calls = setup(tmp_path, monkeypatch)
    original = runner.cleanup_day
    cleanups = []
    def checked_cleanup(root, scratch, manifest):
        date = scratch.name
        output = run.read('day-'+date+'.json')
        assert output['independent']['passed']
        assert output['hash_append']['stream_sha256'] == output['independent']['source_hash_digest']
        index = plan['dates'].index(date)
        receipt = root/runner.BASE/'artifacts/hash-receipts'/f'day-{index:04d}.json'
        assert json.loads(receipt.read_bytes()) == output['hash_append']
        assert output['scratch_manifest'] == manifest
        cleanups.append(date)
        original(root, scratch, manifest)
    monkeypatch.setattr(runner, 'cleanup_day', checked_cleanup)
    cells = runner.execute(tmp_path, plan, run)
    summary = run.read('summary.json')
    assert summary['source_days'] == 3 and summary['graph_days'] == 1
    assert summary['expected_boundary_only'] and summary['stopped'] is None
    assert len(cells) == 7 and cells[-1]['status'] == 'complete'
    assert cleanups == plan['dates']
    assert len(calls) == 6
    assert (tmp_path/'hashes/00.bin').stat().st_size == 96
    assert run.read('day-2022-01-01.json')['source']['status'] == 'complete'
    assert not list((tmp_path/runner.BASE/'artifacts/scratch').iterdir())


def test_process_failure_stops_remaining_population(tmp_path, monkeypatch):
    run, plan, calls = setup(tmp_path, monkeypatch, failure='2022-01-02')
    cells = runner.execute(tmp_path, plan, run)
    assert calls == [('extract', '2022-01-01'), ('check', '2022-01-01'), ('extract', '2022-01-02')]
    assert len(cells) == 7
    assert run.read('day-2022-01-03.json')['source']['status'] == 'unavailable'
    assert run.read('hash-audit.json')['checked_days'] == 1
    assert not any(row['source_admitted'] for row in run.read('panel.json')['days'])
    assert (tmp_path/'hashes/00.bin').stat().st_size == 32


def test_global_duplicates_block_all_source_and_graph_rows(tmp_path, monkeypatch):
    run, plan, _ = setup(tmp_path, monkeypatch, duplicate=True)
    runner.execute(tmp_path, plan, run)
    result = run.read('hash-audit.json')
    assert result['rows'] == 3 and result['unique'] == 1 and result['duplicate_excess'] == 2
    assert not result['admitted']
    assert all(not row['source_admitted'] and not row['graph_admitted'] for row in run.read('panel.json')['days'])
    assert run.read('day-2022-01-02.json')['count']['status'] == 'complete'
    assert (tmp_path/'hashes/00.bin').exists()


def test_hash_digest_mismatch_preserves_scratch_and_stops(tmp_path, monkeypatch):
    run, plan, calls = setup(tmp_path, monkeypatch, wrong_digest=True)
    runner.execute(tmp_path, plan, run)
    assert len(calls) == 2
    output = run.read('day-2022-01-01.json')
    assert 'appended stream' in output['source']['reason']
    assert (tmp_path/output['preserved_phase']).exists()
    assert (tmp_path/'hashes/day-0000.json').exists()
    assert not (tmp_path/runner.BASE/'artifacts/cleanup/2022-01-01.json').exists()
    assert run.read('hash-audit.json')['status'] == 'unavailable'


def test_unexpected_graph_unavailability_retains_published_day_and_arrays(tmp_path, monkeypatch):
    run, plan, calls = setup(tmp_path, monkeypatch, unavailable='2022-01-02')
    runner.execute(tmp_path, plan, run)
    assert len(calls) == 4
    day = run.read('day-2022-01-02.json')
    assert day['source']['status'] == 'complete' and day['independent']['passed']
    assert (tmp_path/runner.BASE/'artifacts/scratch/2022-01-02/phase.json').exists()
    cleanup = json.loads((tmp_path/runner.BASE/'artifacts/cleanup/2022-01-02.json').read_bytes())
    assert cleanup['released'] is False
    assert 'unexpected graph' in run.read('summary.json')['stopped']


@pytest.mark.parametrize('change', ['namespace', 'altered', 'extra', 'symlink'])
def test_cleanup_refuses_unregistered_or_changed_files(tmp_path, change):
    scratch = tmp_path/runner.BASE/'artifacts/scratch/2022-01-01'
    scratch.mkdir(parents=True)
    (scratch/'evidence').write_bytes(b'fixed')
    manifest = runner.old.artifact_manifest(tmp_path, scratch)
    if change == 'namespace':
        wrong = tmp_path/'outside'
        scratch.rename(wrong)
        scratch = wrong
    elif change == 'altered':
        (scratch/'evidence').write_bytes(b'other')
    elif change == 'extra':
        (scratch/'unlisted').write_bytes(b'extra')
    else:
        (scratch/'evidence').unlink()
        target = tmp_path/'original'
        target.write_bytes(b'fixed')
        (scratch/'evidence').symlink_to(target)
    with pytest.raises(ValueError):
        runner.cleanup_day(tmp_path, scratch, manifest)
    assert scratch.exists() and (scratch/'evidence').exists()
