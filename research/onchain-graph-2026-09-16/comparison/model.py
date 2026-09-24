"""Pure matched daily classification; callers supply admitted data and frozen folds.

No acquisition, persistence, tuning, economic accounting, or empirical entry point.
Feature clocks are per-column ``<feature>__available_at`` timestamps in UTC.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier


MODEL_PARAMS = dict(n_estimators=100, max_depth=3, num_leaves=7,
                    learning_rate=0.05, min_child_samples=30, reg_lambda=1,
                    n_jobs=2, deterministic=True, force_col_wise=True,
                    verbosity=-1, random_state=42)


class AuditFitError(RuntimeError):
    """Durable fit recording failed; stop the whole evaluation without retry."""


def _utc(values):
    parsed = pd.to_datetime(values, utc=True, errors="raise")
    if pd.isna(parsed).any():
        raise ValueError("missing timestamp")
    return parsed


def validate_panel(panel, feature_sets):
    """Return copied panel and row-level common admission, never impute.

    Missing features/labels and late availability are common-row exclusions.
    Malformed labels/clocks or duplicates are contract failures. One forecast
    per UTC day is required.
    """
    if set(feature_sets) != {"M0", "M1", "M2"}:
        raise ValueError("exactly M0/M1/M2 required")
    sets = [list(feature_sets[m]) for m in ("M0", "M1", "M2")]
    if any(not s or len(s) != len(set(s)) for s in sets):
        raise ValueError("nonempty unique feature sets required")
    if not set(sets[0]) < set(sets[1]) < set(sets[2]):
        raise ValueError("feature sets must be strictly nested")
    frame = panel.copy().reset_index(drop=True)
    for name in ("decision_at", "label_start", "label_end"):
        frame[name] = _utc(frame[name])
    if frame.decision_at.dt.floor("D").duplicated().any():
        raise ValueError("duplicate forecast day")
    if not frame.decision_at.is_monotonic_increasing:
        raise ValueError("panel must be chronological")
    if ((frame.label_start < frame.decision_at) |
            (frame.label_end <= frame.label_start)).any():
        raise ValueError("invalid label interval")
    if (~frame.y.dropna().isin([0, 1])).any():
        raise ValueError("labels must be binary or missing")
    reasons = [[] for _ in range(len(frame))]
    for name in sets[2]:
        clock = pd.to_datetime(frame[name + "__available_at"], utc=True, errors="raise")
        for i in np.flatnonzero((clock > frame.decision_at).to_numpy()):
            reasons[i].append("late:" + name)
        values = pd.to_numeric(frame[name], errors="raise").to_numpy(dtype=float)
        for i in np.flatnonzero(~np.isfinite(values) | clock.isna().to_numpy()):
            reasons[i].append("missing:" + name)
    for i in np.flatnonzero(frame.y.isna().to_numpy()):
        reasons[i].append("missing:y")
    admission = frame[["decision_at"]].copy()
    admission["exclusion_reasons"] = [tuple(r) for r in reasons]
    admission["included"] = [not r for r in reasons]
    return frame, admission


def binary_metrics(y, probabilities):
    """Binary metrics; clipping only for log loss, class 1 at p >= .5."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(probabilities, dtype=float)
    if (y.ndim != 1 or p.shape != y.shape or not len(y) or
            not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or
            ((p < 0) | (p > 1)).any()):
        raise ValueError("nonempty binary labels and finite probabilities required")
    predicted = p >= .5
    clipped = np.clip(p, 1e-15, 1-1e-15)
    recalls = [float((predicted[y == c] == c).mean()) for c in (0, 1) if (y == c).any()]
    return dict(n=len(y), accuracy=float((predicted == y).mean()),
                balanced_accuracy=float(np.mean(recalls)) if len(recalls) == 2 else None,
                log_loss=float((-y*np.log(clipped)-(1-y)*np.log1p(-clipped)).mean()),
                brier=float(((p-y)**2).mean()))


def run_comparison(panel, feature_sets, folds, *, purge_gap="0D", audit_fit=None):
    """One expanding fit per frozen [start,end) fold, common rows for all models.

    Training labels must end no later than fold start minus purge_gap. No
    within-fold refitting. Missing test rows retain explicit admission records.
    Errors abort instead of returning an apparently complete partial comparison.
    """
    frame, admission = validate_panel(panel, feature_sets)
    gap = pd.Timedelta(purge_gap)
    if pd.isna(gap) or gap < pd.Timedelta(0):
        raise ValueError("purge gap must be nonnegative")
    if not folds:
        raise ValueError("at least one frozen fold required")
    predictions, counts = [], []
    last_end = None
    seen = set()
    for fold in folds:
        ident = fold["id"]
        start, end = _utc(pd.Series([fold["start"], fold["end"]]))
        if ident in seen or start >= end or (last_end is not None and start < last_end):
            raise ValueError("unique chronological nonoverlapping folds required")
        seen.add(ident)
        last_end = end
        train_candidate = (frame.decision_at < start) & (frame.label_end <= start-gap)
        test_candidate = (frame.decision_at >= start) & (frame.decision_at < end)
        train = frame.loc[train_candidate & admission.included]
        test = frame.loc[test_candidate & admission.included]
        if train.y.nunique() != 2 or test.empty:
            raise ValueError(f"fold {ident}: both training classes and test rows required")
        result = test[["decision_at", "label_start", "label_end", "y"]].copy()
        result["fold"] = ident
        # Majority tie policy is fixed to class zero; baseline probabilities are
        # degenerate and log-loss clipping follows the same metric convention.
        result["majority_probability"] = float(train.y.mean() > .5)
        for name in ("M0", "M1", "M2"):
            learner = LGBMClassifier(**MODEL_PARAMS)
            columns = list(feature_sets[name])
            learner.fit(train[columns], train.y.astype(int))
            if audit_fit is not None:
                try:
                    audit_fit(ident, name, learner, train, test)
                except Exception as exc:
                    raise AuditFitError(f"fit checkpoint failed: {type(exc).__name__}: {exc}") from exc
            p = learner.predict_proba(test[columns])[:, list(learner.classes_).index(1)]
            binary_metrics(test.y, p)  # Fail closed on malformed learner output.
            result[name + "_probability"] = p
        counts.append(dict(fold=ident, train_candidates=int(train_candidate.sum()),
                           train_included=len(train), test_candidates=int(test_candidate.sum()),
                           test_included=len(test), train_label_cutoff=start-gap))
        predictions.append(result)
    combined = pd.concat(predictions, ignore_index=True)
    metrics = []
    for ident, group in combined.groupby("fold", sort=False):
        for name in ("M0", "M1", "M2", "majority"):
            metrics.append(dict(fold=ident, model=name,
                                **binary_metrics(group.y, group[name+"_probability"])))
    pooled = {name: binary_metrics(combined.y, combined[name+"_probability"])
              for name in ("M0", "M1", "M2", "majority")}
    return dict(predictions=combined, metrics=pd.DataFrame(metrics), pooled_metrics=pooled,
                admission=admission, folds=pd.DataFrame(counts),
                model_params=dict(MODEL_PARAMS))


def paired_loss_summary(predictions, *, block_days=14, resamples=2000, seed=42):
    """Paired Brier/log-loss differences and moving-block percentile CI.

    Negative difference favours the augmented model. Require consecutive days;
    non-circular overlapping blocks have exactly block_days observations. Gaps
    must be reported rather than silently changing the meaning of a day block.
    """
    if not isinstance(block_days, int) or block_days < 1 or not isinstance(resamples, int) or resamples < 1:
        raise ValueError("positive integer block_days and resamples required")
    dates = _utc(predictions.decision_at).dt.floor("D")
    if dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise ValueError("unique chronological prediction days required")
    if len(dates) < block_days or not (dates.diff().iloc[1:] == pd.Timedelta(days=1)).all():
        raise ValueError("bootstrap requires uninterrupted daily predictions and at least one full block")
    y = predictions.y.to_numpy(dtype=float)
    losses = {}
    for model in ("M0", "M1", "M2"):
        p = predictions[model + "_probability"].to_numpy(dtype=float)
        binary_metrics(y, p)
        q = np.clip(p, 1e-15, 1-1e-15)
        losses[model] = dict(brier=(p-y)**2, log_loss=-y*np.log(q)-(1-y)*np.log1p(-q))
    blocks = [np.arange(start, start+block_days) for start in range(len(y)-block_days+1)]
    rng = np.random.default_rng(seed)
    daily = predictions[["decision_at", "fold"]].copy()
    summaries = {}
    # Identical sampled indices for every model contrast and loss.
    samples = []
    for _ in range(resamples):
        indices = []
        while len(indices) < len(y):
            indices.extend(blocks[int(rng.integers(len(blocks)))])
        samples.append(np.asarray(indices[:len(y)]))
    for newer, older in (("M1", "M0"), ("M2", "M1")):
        for loss in ("brier", "log_loss"):
            key = f"{newer}-{older}:{loss}"
            differences = losses[newer][loss]-losses[older][loss]
            daily[key] = differences
            means = np.asarray([differences[s].mean() for s in samples])
            summaries[key] = dict(mean=float(differences.mean()),
                                  ci95=[float(v) for v in np.quantile(means, [.025, .975])])
    return dict(daily=daily, summaries=summaries, block_days=block_days,
                resamples=resamples, seed=seed, n=len(y))


def evaluate(panel, *, audit_fit=None):
    """Protocol-bound evaluation of caller-supplied admitted rows; no data I/O.

    The adjacent preparation config fixes the sample, arms, folds and inference.
    It is not lifecycle admission. Failed folds remain explicit; successful
    predictions remain available without presenting partial inference as full.
    """
    config = json.loads(Path(__file__).with_name("config.json").read_text())
    if config["model"]["params"] != MODEL_PARAMS:
        raise ValueError("config/model parameter mismatch")
    decisions = pd.to_datetime(panel.decision_at, utc=True, errors="raise")
    selected = panel.loc[(decisions >= pd.Timestamp(config["decisions"]["start"])) &
                         (decisions < pd.Timestamp(config["decisions"]["end_exclusive"]))].copy()
    selected["decision_at"] = pd.to_datetime(selected.decision_at, utc=True)
    label_start = pd.to_datetime(selected.label_start, utc=True, errors="raise")
    label_end = pd.to_datetime(selected.label_end, utc=True, errors="raise")
    if ((selected.decision_at != selected.decision_at.dt.floor("D")).any() or
            not (label_start == selected.decision_at).all() or
            not (label_end == selected.decision_at+pd.Timedelta(days=1)).all()):
        raise ValueError("protocol requires midnight decisions and exact one-day labels")
    # Validate supplied chronology before inserting explicitly missing days.
    validate_panel(selected, config["feature_sets"])
    expected_decisions = pd.date_range(config["decisions"]["start"], config["decisions"]["end_exclusive"],
                                       freq="D", inclusive="left")
    selected = selected.set_index("decision_at").reindex(expected_decisions)
    selected.index.name = "decision_at"
    selected = selected.reset_index()
    selected["label_start"] = selected.decision_at
    selected["label_end"] = selected.decision_at+pd.Timedelta(days=1)
    frame, admission = validate_panel(selected, config["feature_sets"])
    outputs, attempts = [], []
    for fold in config["folds"]:
        try:
            result = run_comparison(frame, config["feature_sets"], [fold], purge_gap=config["purge_gap"], audit_fit=audit_fit)
        except AuditFitError:
            raise
        except Exception as exc:
            attempts.append(dict(fold=fold["id"], status="failed", error=f"{type(exc).__name__}: {exc}"))
        else:
            outputs.append(result)
            attempts.append(dict(fold=fold["id"], status="complete", error=None))
    predictions = pd.concat([r["predictions"] for r in outputs], ignore_index=True) if outputs else pd.DataFrame()
    monthly, pooled = [], {}
    for attempt in attempts:
        group = predictions.loc[predictions.fold == attempt["fold"]] if len(predictions) else predictions
        difference = None
        if len(group):
            difference = (binary_metrics(group.y, group.M2_probability)["log_loss"] -
                          binary_metrics(group.y, group.M1_probability)["log_loss"])
        monthly.append(dict(**attempt, n=len(group), M2_minus_M1_log_loss=difference))
    if len(predictions):
        pooled = {name: binary_metrics(predictions.y, predictions[name+"_probability"])
                  for name in ("M0", "M1", "M2", "majority")}
    bootstrap = config["bootstrap"]
    required = pd.date_range(bootstrap["required_start"], bootstrap["required_end_exclusive"], freq="D", inclusive="left")
    actual = pd.DatetimeIndex(predictions.decision_at) if len(predictions) else pd.DatetimeIndex([], tz="UTC")
    missing = required.difference(actual)
    inference = dict(status="unavailable", reason="all 366 daily 2024 predictions required", missing_dates=missing.tolist())
    screening = dict(status="unavailable", supported=None)
    if actual.equals(required) and all(a["status"] == "complete" for a in attempts):
        try:
            paired = paired_loss_summary(predictions, block_days=bootstrap["block_days"],
                                         resamples=bootstrap["resamples"], seed=bootstrap["seed"])
            inference = dict(status="available", result=paired, missing_dates=[])
            negative_months = sum(m["M2_minus_M1_log_loss"] < 0 for m in monthly)
            upper = paired["summaries"][config["screening"]["primary"]]["ci95"][1]
            supported = (upper < config["screening"]["ci95_upper_strictly_below"] and
                         negative_months >= config["screening"]["monthly_negative_minimum"])
            screening = dict(status="available", supported=bool(supported), negative_months=negative_months)
        except Exception as exc:
            inference = dict(status="unavailable", reason=f"{type(exc).__name__}: {exc}",
                             error_type="inference_failed", missing_dates=[])
            screening = dict(status="unavailable", supported=None)
    return dict(predictions=predictions, admission=admission, attempts=pd.DataFrame(attempts),
                monthly=pd.DataFrame(monthly), pooled_metrics=pooled,
                fold_metrics=pd.concat([r["metrics"] for r in outputs], ignore_index=True) if outputs else pd.DataFrame(),
                counts=pd.concat([r["folds"] for r in outputs], ignore_index=True) if outputs else pd.DataFrame(),
                inference=inference, screening=screening)
