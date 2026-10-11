"""Failure injection on synthetic fits only; no retained empirical inputs."""
from dataclasses import asdict, replace
import errno
import json
from pathlib import Path

import pytest
import torch

from tests.research.test_lifecycle import registered, start
from tests.research.onchain_replication.test_dataset import fixture
from tests.research.onchain_replication.test_evaluation import CONFIG, bind_examples
from tests.research.onchain_replication.test_training import CFG, P, batch
from tradingagents.research.onchain_replication import evaluation, training
from tradingagents.research.onchain_replication.dataset import build_examples, fit_scaler
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest


class Unprintable(RuntimeError):
    def __str__(self):
        raise ValueError('formatting failed')


def fail_here(primary, tracebacks):
    try:
        raise primary
    except BaseException:
        tracebacks.append(primary.__traceback__)
        raise


def assert_primary(caught, primary, tracebacks):
    assert caught is primary
    chain = []
    tb = caught.__traceback__
    while tb is not None:
        chain.append(tb)
        tb = tb.tb_next
    assert tracebacks[0] in chain


def evaluation_case(registered, arm):
    graphs, prices, fold, config = fixture()
    examples = build_examples(graphs, prices, fold, config)
    examples = replace(examples, train=examples.train[:40],
        train_hash=digest(canonical_bytes([asdict(x) for x in examples.train[:40]])),
        test=examples.test[:2],
        test_mask_hash=digest(canonical_bytes([x.decision_at for x in examples.test[:2]])))
    scaler = fit_scaler(examples, prices, fold)
    cell = dict(id='sum', arm=arm, task='direction', seed=11, fold='2024',
                variant='full', lane='algorithm', asset='ETH')
    config = {**CFG, 'epochs': 1}
    registered = bind_examples(registered, examples, scaler)
    provenance = {**P, 'source_commit': registered[2], 'input_hash': examples.train_hash,
        'config_hash': digest(canonical_bytes({'model': CONFIG, 'training': config,
            'cell': cell, 'feature_binding': {}, 'scaler': asdict(scaler)}))}
    return registered, (cell, examples, scaler, {}, CONFIG, config, provenance), {
        'expected_test_mask': examples.test_mask_hash, 'feature_binding': {},
        'example_binding_input': 'examples'}


@pytest.mark.parametrize('publication_fails', [False, True])
def test_first_batch_primary_survives_both_reporting_paths(registered, monkeypatch, publication_fails):
    registered, args, kwargs = evaluation_case(registered, 'lstm')
    primary = Unprintable()
    tracebacks, attempts, retained = [], [], {}
    reserve = training._reserve

    def reserve_with_retained_evidence(*a, **kw):
        directory = reserve(*a, **kw)
        checkpoint = directory/'retained-checkpoint.bin'
        checkpoint.write_bytes(b'previous durable checkpoint')
        for path in (checkpoint, directory/'claim.json'):
            retained[path] = path.read_bytes()
        return directory

    factory = evaluation.batch_factory
    def failing_factory(*a, **kw):
        original = factory(*a, **kw)
        if a[2] is args[1].train:
            return lambda indices: fail_here(primary, tracebacks)
        return original

    immutable = training._immutable
    def publish(path, value):
        if path.name == 'failed.json':
            attempts.append(path)
            if publication_fails:
                raise OSError(errno.ENOSPC, 'injected full disk')
        immutable(path, value)

    monkeypatch.setattr(training, '_reserve', reserve_with_retained_evidence)
    monkeypatch.setattr(evaluation, 'batch_factory', failing_factory)
    monkeypatch.setattr(training, '_immutable', publish)
    monkeypatch.setattr(evaluation, '_immutable', publish)
    with start(registered) as run:
        try:
            evaluation.evaluate_cell(run, *args, **kwargs)
        except BaseException as caught:
            assert_primary(caught, primary, tracebacks)
        else:
            pytest.fail('training failure was suppressed')
        assert len(attempts) == 2 and len(set(attempts)) == 2
        assert all(path.read_bytes() == raw for path, raw in retained.items())
        if publication_fails:
            assert all(not p.exists() for p in attempts)
            assert sum('OSError' in note for note in primary.__notes__) == 2
        else:
            values = [json.loads(p.read_bytes()) for p in attempts]
            assert all('unprintable exception' in value['reason'] for value in values)
            assert values[0]['type'] == 'Unprintable'


def test_failure_after_real_checkpoint_preserves_checkpoint_and_primary(registered, monkeypatch):
    primary = RuntimeError('after completed batch')
    tracebacks, retained = [], {}
    def interrupt(epoch, batch_number, checkpoint):
        retained[checkpoint] = checkpoint.read_bytes()
        fail_here(primary, tracebacks)
    immutable = training._immutable
    def publish(path, value):
        if path.name == 'failed.json':
            raise OSError(errno.ENOSPC, 'injected full disk')
        immutable(path, value)
    monkeypatch.setattr(training, '_immutable', publish)
    with start(registered) as run:
        try:
            training.fit_cell(run, 'sum', {**P, 'source_commit': run.admission.source},
                lambda: torch.nn.Linear(2, 1), batch, 2, 'regression', 11, CFG,
                after_batch=interrupt)
        except BaseException as caught:
            assert_primary(caught, primary, tracebacks)
        else:
            pytest.fail('post-checkpoint failure was suppressed')
        assert len(retained) == 1
        assert all(path.read_bytes() == raw for path, raw in retained.items())
        assert not list(next(iter(retained)).parents[2].glob('complete.json'))


@pytest.mark.parametrize('phase', ['fit', 'prediction'])
@pytest.mark.parametrize('publication_fails', [False, True])
def test_svm_failure_attempts_independent_markers_without_overwriting_completion(
        registered, monkeypatch, phase, publication_fails):
    from sklearn.svm import SVC
    registered, args, kwargs = evaluation_case(registered, 'svm')
    primary = Unprintable()
    tracebacks, attempts = [], []
    def failure(*a, **kw):
        fail_here(primary, tracebacks)
    monkeypatch.setattr(SVC, 'fit' if phase == 'fit' else 'decision_function', failure)
    immutable = evaluation._immutable
    def publish(path, value):
        if path.name == 'failed.json':
            attempts.append(path)
            if publication_fails:
                raise OSError(errno.ENOSPC, 'injected full disk')
        immutable(path, value)
    monkeypatch.setattr(evaluation, '_immutable', publish)
    with start(registered) as run:
        try:
            evaluation.evaluate_cell(run, *args, **kwargs)
        except BaseException as caught:
            assert_primary(caught, primary, tracebacks)
        else:
            pytest.fail('SVM failure was suppressed')
        fit_root = registered[0]/'research_artifacts/onchain_fit_cells'
        complete = list(fit_root.glob('*/example-a/complete.json'))
        failed = list(fit_root.glob('*/example-a/failed.json'))
        assert len(complete) == (phase == 'prediction')
        assert len(failed) == (phase == 'fit' and not publication_fails)
        if phase == 'fit':
            assert any(p.is_relative_to(fit_root) for p in attempts)
        else:
            assert all(not p.is_relative_to(fit_root) for p in attempts)
        assert any(not p.is_relative_to(fit_root) for p in attempts)


def test_reporting_and_cleanup_continue_even_when_secondary_note_fails():
    from tradingagents.research.onchain_replication.failure_reporting import record_failure
    class NoNotes(RuntimeError):
        def add_note(self, note):
            raise RuntimeError('note storage failed')
    primary = NoNotes('original')
    tracebacks, actions = [], []
    def broken_publication():
        actions.append('publish')
        raise OSError(errno.ENOSPC, 'full disk')
    def broken_cleanup():
        actions.append('cleanup')
        raise KeyboardInterrupt('cleanup interrupted')
    try:
        try:
            fail_here(primary, tracebacks)
        except BaseException as error:
            record_failure(error, (broken_publication, broken_cleanup, lambda: actions.append('last')))
            raise
    except BaseException as caught:
        assert_primary(caught, primary, tracebacks)
    assert actions == ['publish', 'cleanup', 'last']
