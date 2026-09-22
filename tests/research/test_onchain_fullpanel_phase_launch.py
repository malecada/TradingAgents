"""Synthetic committed correction binding and no-premature-review contracts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

BASE = 'research/onchain-graph-2026-09-16/fullpanel'
FILE = Path(__file__).resolve().parents[2] / BASE / 'launch_phase_v2.py'
spec = importlib.util.spec_from_file_location('phase_launch_contract_tests', FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def bound(tmp_path, monkeypatch):
    root = tmp_path / 'coordinator';root.mkdir()
    execution = tmp_path / 'execution';execution.mkdir()
    here = root / BASE;here.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    def commit():
        subprocess.run(['git', 'add', '.'], cwd=root, check=True)
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'synthetic binding'], cwd=root, check=True)
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    review = b'Synthetic independent correction review.\n'
    (here / 'PHASE_CORRECTION_REVIEW.md').write_bytes(review)
    approval = dict(decision='approve-phase-serialization-correction', review_sha256=digest(review))
    (here / 'PHASE_CORRECTION_APPROVAL.json').write_text(json.dumps(approval))
    (here / 'check_final_phase_v2.py').write_text('# synthetic bound wrapper\n')
    (execution / 'claim.json').write_text('{}')
    files = {str(p.relative_to(root)):digest(p.read_bytes()) for p in here.iterdir()}
    contract = dict(execution_source='fdb33cf27ca97b8d32926f046be422d8b8b45b6f', execution_root=str(execution), compute_replay_allowed=False,
                    committed_files=files, execution_files={'claim.json':digest(b'{}')})
    (here / 'phase-correction.json').write_text(json.dumps(contract))
    source = commit()
    original = subprocess.check_output
    def git_output(args, **kwargs):
        if Path(kwargs.get('cwd', '.')) == execution and args == ['git', 'rev-parse', 'HEAD']:
            return contract['execution_source'] + '\n'
        return original(args, **kwargs)
    monkeypatch.setattr(m.subprocess, 'check_output', git_output)
    return root, execution, source, commit


def test_exact_committed_source_and_unchanged_ancestor_allowed(bound):
    root, execution, source, commit = bound
    contract, raw = m.validate_contract(root, source)
    assert contract['execution_root'] == str(execution)
    assert json.loads(raw) == contract
    (root / 'later-status.txt').write_text('No correction changes.\n');commit()
    assert m.validate_contract(root, source)[0] == contract


@pytest.mark.parametrize('kind', ['contract', 'wrapper', 'execution', 'short_source'])
def test_changed_binding_rejected(bound, kind):
    root, execution, source, _ = bound
    if kind == 'contract':
        path = root / BASE / 'phase-correction.json';path.write_bytes(path.read_bytes()+b' ')
    elif kind == 'wrapper':
        (root / BASE / 'check_final_phase_v2.py').write_text('# changed\n')
    elif kind == 'execution':
        (execution / 'claim.json').write_text('{"changed":true}')
    else:
        source = source[:8]
    with pytest.raises(ValueError):
        m.validate_contract(root, source)


def test_running_compute_cannot_open_review_receipt(bound, monkeypatch):
    root, execution, source, _ = bound
    (execution / BASE).mkdir(parents=True)
    monkeypatch.setattr(m, 'ROOT', root);monkeypatch.setattr(m, 'HERE', root / BASE)
    monkeypatch.setattr(sys, 'argv', ['launch_phase_v2.py', '--source', source])
    with pytest.raises(ValueError, match='unique compute terminal'):
        m.main()
    assert not (execution / BASE / 'independent-resource-v2.json').exists()


def test_prior_corrected_attempt_cannot_be_replayed(bound, monkeypatch):
    root, execution, source, _ = bound
    directory = execution / BASE;directory.mkdir(parents=True)
    run = execution / 'research_runs/eth-full-history-feature-panel-20260922';run.mkdir(parents=True)
    (run / 'complete.json').write_text('{}')
    (directory / 'resource.json').write_text(json.dumps(dict(source='fdb33cf27ca97b8d32926f046be422d8b8b45b6f')))
    (directory / 'independent-resource-v2.json').write_text('preserve failed/partial attempt')
    monkeypatch.setattr(m, 'ROOT', root);monkeypatch.setattr(m, 'HERE', root / BASE)
    monkeypatch.setattr(sys, 'argv', ['launch_phase_v2.py', '--source', source])
    with pytest.raises(FileExistsError):m.main()
    assert (directory / 'independent-resource-v2.json').read_text() == 'preserve failed/partial attempt'
