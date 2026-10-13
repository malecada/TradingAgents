"""One arm-seed fit: deterministic, chronological batches, per-epoch checkpoints, one-shot test predictions."""
from __future__ import annotations

import json
import os
import random
import tempfile
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.checkpoint import checkpoint

from . import calendar as cal
from . import config
from . import data as Dt
from . import model as M
from . import prices as P
from .runlog import Log

ARMS = ('full', 'lstm', 'gru', 'hlstm', 'svm')


def _replace_atomically(target: Path, write):
    """Write through a temp file in the same directory, then os.replace onto the target."""
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix='.tmp-')
    os.close(fd)
    try:
        write(tmp)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed % 2 ** 32)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def permute_labels(examples_, seed):
    """Permute training targets once (chance control); decision dates and inputs stay in place."""
    rng = np.random.Generator(np.random.PCG64(seed))
    order = sorted(range(len(examples_)), key=lambda k: examples_[k].decision)
    targets = [examples_[k].target for k in order]
    perm = rng.permutation(len(targets))
    out = []
    for pos, k in enumerate(order):
        e = examples_[k]
        out.append(Dt.Example(e.decision, e.step_days, e.step_weeks, e.closes, targets[perm[pos]]))
    return out


def encode_weeks(model, store, weeks, constant=False):
    """Encode each distinct week once per batch; activation checkpointing bounds memory to one graph."""
    vectors = {}
    for w in sorted(set(weeks)):
        if constant:
            vectors[w] = torch.zeros(32)
            continue
        mcm, ei = store.tensors(w)
        vectors[w] = checkpoint(model.encoder, mcm, ei, use_reentrant=False)
    return vectors


def _graph_tensor(vectors, batch_weeks):
    return torch.stack([torch.stack([vectors[w] for w in ws]) for ws in batch_weeks])


def _loss(task, out, targets):
    if task == 'classification':
        return torch.nn.functional.cross_entropy(out, targets.long())
    return ((out.squeeze(-1) - targets) ** 2).mean()


def _predict(task, out):
    return out.argmax(1).tolist() if task == 'classification' else out.squeeze(-1).tolist()


def _forward(arm, model, store, b, constant):
    if arm == 'full':
        vec = encode_weeks(model, store, [w for ws in b.weeks for w in ws], constant)
        return model(b.prices, _graph_tensor(vec, b.weeks))
    return model(b.prices)


def fit(arm, task, seed, out_dir, store=None, epochs=None, diag=None, prices=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log = Log(out_dir / 'fit.jsonl')
    tcfg, mcfg = config.load('training'), config.load('model')
    epochs = tcfg['epochs'] if epochs is None else epochs
    prices = P.load_prices() if prices is None else prices
    train_days = cal.decision_dates('train')
    scaler = P.Scaler().fit(prices, sorted({t for d in train_days for t in cal.window(d)}))
    train = Dt.examples('train', prices, scaler, task)
    test = Dt.examples('test', prices, scaler, task)
    if diag == 'label_permutation':
        train = permute_labels(train, tcfg['label_permutation_seed'])
    constant = diag == 'constant_graph'
    set_seed(seed)
    if arm == 'svm':
        from sklearn.svm import SVC, SVR
        X = np.stack([e.closes for e in train])
        y = np.array([e.target for e in train])
        Xt = np.stack([e.closes for e in test])
        svm_cfg = mcfg['baselines']['svm']
        cls = SVC if task == 'classification' else SVR
        m = cls(kernel=svm_cfg['kernel'], C=svm_cfg['C'], gamma=svm_cfg['gamma']).fit(X, y)
        preds = m.predict(Xt).tolist()
        result = {'arm': arm, 'task': task, 'seed': seed, 'epochs_done': 0, 'final_train_loss': float('nan')}
    else:
        model = M.FullModel(task, mcfg) if arm == 'full' else M.PriceModel(arm, task, mcfg)
        opt = torch.optim.Adam(model.parameters(), lr=tcfg['lr'], betas=tuple(tcfg['betas']))
        start = 0
        ck = out_dir / 'checkpoint.pt'
        if ck.exists():
            state = torch.load(ck, weights_only=False)
            model.load_state_dict(state['model'])
            opt.load_state_dict(state['opt'])
            start = state['epoch']
            torch.set_rng_state(state['rng'])
            np.random.set_state(state['np_rng'])
            random.setstate(state['py_rng'])
        loss_value = float('nan')
        for epoch in range(start, epochs):
            model.train()
            t = time.time()
            total, n = 0.0, 0
            for b in Dt.batches(train, tcfg['batch_size']):
                opt.zero_grad()
                out = _forward(arm, model, store, b, constant)
                loss = _loss(task, out, b.targets)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), tcfg['grad_clip_norm'])
                opt.step()
                total += loss.item() * len(b.decisions)
                n += len(b.decisions)
            loss_value = total / n
            state = {'model': model.state_dict(), 'opt': opt.state_dict(), 'epoch': epoch + 1,
                     'rng': torch.get_rng_state(), 'np_rng': np.random.get_state(), 'py_rng': random.getstate()}
            def _save(path, state=state):
                with open(path, 'wb') as fh:          # file handle: torch rejects dot-prefixed temp names
                    torch.save(state, fh)
            _replace_atomically(ck, _save)
            log.event(event='epoch', epoch=epoch + 1, train_loss=loss_value, seconds=round(time.time() - t, 1))
        model.eval()
        preds = []
        with torch.no_grad():
            for b in Dt.batches(test, tcfg['batch_size']):
                preds += _predict(task, _forward(arm, model, store, b, constant))
        result = {'arm': arm, 'task': task, 'seed': seed, 'epochs_done': epochs, 'final_train_loss': loss_value}
    records = []
    for e, p in zip(test, preds):
        target = e.target if task == 'classification' else scaler.inverse(e.target)
        pred = p if task == 'classification' else scaler.inverse(p)
        records.append({'decision': e.decision.isoformat(), 'pred': float(pred), 'target': float(target)})
    summary = json.dumps({**result, 'diag': diag, 'n_train': len(train), 'n_test': len(test)}, indent=1)
    _replace_atomically(out_dir / 'result.json', lambda path: Path(path).write_text(summary))
    # predictions.json is the completion marker for cli fit: written last
    _replace_atomically(out_dir / 'predictions.json', lambda path: Path(path).write_text(json.dumps(records)))
    log.event(event='done', **result)
    return result
