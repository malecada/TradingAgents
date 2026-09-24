"""Independent arithmetic, prediction-row checks and conservative completion gates.

Pure data only: no experiment execution, filesystem reads or model replay. Metric
and clock calculations deliberately do not import production metrics/calendars.
Evidence references are checked structurally; their bytes must be verified by the
caller. A passing row check is not proof of historical source availability or of
training-label provenance.
"""
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
import hashlib
import json
import math
from numbers import Integral, Real
import re


CRITERIA = frozenset(f'C{i:02d}' for i in range(1, 19))
PREDICTION_FIELDS = frozenset({
    'lane', 'asset', 'arm', 'fold_id', 'seed', 'decision_at', 'label_start',
    'label_end', 'max_input_available_at', 'y_true', 'probability_up',
    'predicted_price', 'checkpoint_hash',
})


def _number(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError('finite numeric scalar required')
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('finite numeric scalar required')
    return result


def _pair(first, second):
    try:
        a = tuple(_number(v) for v in first)
        b = tuple(_number(v) for v in second)
    except TypeError as error:
        raise ValueError('one-dimensional populations required') from error
    if not a or len(a) != len(b):
        raise ValueError('nonempty matched populations required')
    return a, b


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else 0.


def independent_classification(labels, probabilities):
    """Manual up-positive counts; p=0.5 predicts down; undefined ratios are zero.

    Macro/balanced denominators always include both classes, including an absent
    class, matching the frozen zero-division convention. Accumulation uses Python
    binary64 and math.fsum, not sklearn or the production metric implementation.
    """
    labels, probabilities = _pair(labels, probabilities)
    if any(y not in (0., 1.) for y in labels) or any(not 0 <= p <= 1 for p in probabilities):
        raise ValueError('binary labels and scalar probabilities in [0,1] required')
    tp = tn = fp = fn = 0
    for y, p in zip(labels, probabilities):
        if p > .5:
            if y == 1: tp += 1
            else: fp += 1
        elif y == 1: fn += 1
        else: tn += 1
    n = len(labels)
    up = (_ratio(tp, tp+fp), _ratio(tp, tp+fn), _ratio(2*tp, 2*tp+fp+fn))
    down = (_ratio(tn, tn+fn), _ratio(tn, tn+fp), _ratio(2*tn, 2*tn+fp+fn))
    positive, negative = tp+fn, tn+fp
    result = {'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn, 'N': n,
              'accuracy': (tp+tn)/n, 'balanced_accuracy': (up[1]+down[1])/2,
              'brier': math.fsum((p-y)**2 for y, p in zip(labels, probabilities))/n}
    for name, u, d in zip(('precision', 'recall', 'f1'), up, down):
        result[name+'_up'] = u
        result[name+'_macro'] = (u+d)/2
        result[name+'_weighted'] = (positive*u+negative*d)/n
    clipped = tuple(min(1-1e-15, max(1e-15, p)) for p in probabilities)
    result['log_loss'] = -math.fsum(math.log(p) if y == 1 else math.log1p(-p)
                                   for y, p in zip(labels, clipped))/n
    return result


def independent_regression(actual, predicted):
    """Price-unit errors; MAPE is a percentage with positive actual-price support."""
    actual, predicted = _pair(actual, predicted)
    if any(y <= 0 for y in actual):
        raise ValueError('MAPE requires positive actual prices')
    try:
        errors = tuple(abs(p-y) for y, p in zip(actual, predicted))
        mse = math.fsum(e*e for e in errors)/len(errors)
        result = {'MAE': math.fsum(errors)/len(errors), 'MSE': mse,
                  'RMSE': math.sqrt(mse),
                  'MAPE_percent': 100*math.fsum(e/y for e, y in zip(errors, actual))/len(errors)}
    except (OverflowError, ValueError) as error:
        raise ValueError('regression arithmetic overflow') from error
    if not all(math.isfinite(v) for v in result.values()):
        raise ValueError('nonfinite regression metric')
    return result


def compare_summary(reported, independently_computed, *, atol=1e-10, rtol=1e-8):
    """Exact metric membership and counts; float differences bounded by C13.

    Stricter tolerances are allowed. Widening the frozen tolerances is not.
    Returned differences are reported minus independently computed values.
    """
    atol, rtol = _number(atol), _number(rtol)
    if not 0 <= atol <= 1e-10 or not 0 <= rtol <= 1e-8:
        raise ValueError('tolerances exceed C13')
    if not isinstance(reported, Mapping) or not isinstance(independently_computed, Mapping):
        raise ValueError('metric mappings required')
    if not independently_computed or set(reported) != set(independently_computed):
        raise ValueError('summary metric membership mismatch')
    differences = {}
    for key, expected in independently_computed.items():
        reference, observed = _number(expected), _number(reported[key])
        difference = observed-reference
        if isinstance(expected, Integral):
            if not isinstance(reported[key], Integral) or reported[key] != expected:
                raise ValueError('integer count mismatch: '+str(key))
        elif abs(difference) > atol+rtol*abs(reference):
            raise ValueError('C13 metric mismatch: '+str(key))
        differences[key] = difference
    return {'passed': True, 'atol': atol, 'rtol': rtol, 'differences': differences}


def _utc(value, *, daily=False):
    if not isinstance(value, str) or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)', value):
        raise ValueError('explicit ISO UTC timestamp required')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('invalid timestamp') from error
    if daily and (result.hour, result.minute, result.second, result.microsecond) != (0, 0, 0, 0):
        raise ValueError('daily boundary must be midnight UTC')
    return result


def _identity(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_predictions(rows, *, required_decisions, test_start, test_end,
                         expected_lane, expected_asset, expected_arm,
                         expected_fold_id, expected_seed, task):
    """Validate one frozen daily prediction cell against its declared calendar.

    Both current lanes use input availability <= decision, label_start=decision
    and a one-day label horizon. A retrospective look-ahead diagnostic would need
    its own explicitly specified checker. Row ordering is immaterial; identities
    use sorted, normalized UTC timestamps. Checkpoint hashes must agree within a
    cell. This checks hash syntax only, not checkpoint bytes or fitted labels.
    """
    if task not in {'classification', 'regression'}:
        raise ValueError('unknown prediction task')
    if expected_lane not in {'paper_reconstruction', 'causal_audit'} or expected_asset not in {'ETH', 'BTC'}:
        raise ValueError('unsupported prediction lane/asset')
    if not isinstance(expected_arm, str) or not expected_arm or not isinstance(expected_fold_id, str) or not expected_fold_id:
        raise ValueError('arm and fold identity required')
    if type(expected_seed) is not int or expected_seed < 0:
        raise ValueError('integer seed required')
    start, end = _utc(test_start, daily=True), _utc(test_end, daily=True)
    if start >= end:
        raise ValueError('empty test interval')
    decisions = tuple(_utc(t, daily=True) for t in required_decisions)
    if not decisions or len(set(decisions)) != len(decisions):
        raise ValueError('nonempty unique required decision dates required')
    if any(not start <= t < end or t+timedelta(days=1) > end for t in decisions):
        raise ValueError('required decision outside test interval')
    expected_identity = {'lane': expected_lane, 'asset': expected_asset,
                         'arm': expected_arm, 'fold_id': expected_fold_id, 'seed': expected_seed}
    seen = set(); checkpoints = set(); normalized = []
    for supplied in rows:
        if is_dataclass(supplied) and not isinstance(supplied, type): supplied = asdict(supplied)
        if not isinstance(supplied, Mapping) or set(supplied) != PREDICTION_FIELDS:
            raise ValueError('prediction field membership mismatch')
        row = dict(supplied)
        if type(row['seed']) is not int or any(row[k] != v for k, v in expected_identity.items()):
            raise ValueError('prediction cell identity mismatch')
        decision = _utc(row['decision_at'], daily=True)
        label_start = _utc(row['label_start'], daily=True)
        label_end = _utc(row['label_end'], daily=True)
        available = _utc(row['max_input_available_at'])
        if not start <= decision < end or label_start != decision or label_end != decision+timedelta(days=1) or label_end > end:
            raise ValueError('prediction label/test clock mismatch')
        if available > decision:
            raise ValueError('input availability after decision')
        if decision in seen:
            raise ValueError('duplicate prediction decision')
        seen.add(decision)
        checkpoint = row['checkpoint_hash']
        if not isinstance(checkpoint, str) or re.fullmatch('[0-9a-f]{64}', checkpoint) is None:
            raise ValueError('invalid checkpoint SHA256')
        checkpoints.add(checkpoint)
        truth = _number(row['y_true'])
        if task == 'classification':
            p = _number(row['probability_up'])
            if truth not in (0., 1.) or not 0 <= p <= 1 or row['predicted_price'] is not None:
                raise ValueError('invalid classification prediction fields')
            row['probability_up'] = p
        else:
            prediction = _number(row['predicted_price'])
            if truth <= 0 or row['probability_up'] is not None:
                raise ValueError('invalid regression prediction fields')
            row['predicted_price'] = prediction
        row['y_true'] = truth
        for name, value in (('decision_at', decision), ('label_start', label_start),
                            ('label_end', label_end), ('max_input_available_at', available)):
            row[name] = value.isoformat().replace('+00:00', 'Z')
        normalized.append(row)
    if seen != set(decisions):
        raise ValueError('prediction decision denominator mismatch')
    if len(checkpoints) != 1:
        raise ValueError('mixed prediction checkpoint identities')
    normalized.sort(key=lambda row: row['decision_at'])
    return {'count': len(normalized), 'identity': _identity(normalized),
            'checkpoint_hash': next(iter(checkpoints)), 'cell': expected_identity,
            'scope': 'declared prediction membership and row clocks only; fitted-label and source-byte lineage not checked'}


def _disposition(record, allowed):
    if not isinstance(record, Mapping) or set(record)-{'status', 'scope', 'evidence', 'reason'}:
        raise ValueError('invalid criterion record fields')
    status, scope, evidence = (record.get(k) for k in ('status', 'scope', 'evidence'))
    if status not in allowed or not isinstance(scope, str) or not scope.strip():
        raise ValueError('explicit status and scope required')
    if not isinstance(evidence, (list, tuple)) or any(not isinstance(e, str) or not e.strip() for e in evidence):
        raise ValueError('evidence references must be a list of nonempty strings')
    if status in {'passed', 'matched', 'different'} and not evidence:
        raise ValueError('positive or numerical disposition requires evidence')
    if status != 'passed' and (not isinstance(record.get('reason'), str) or not record['reason'].strip()):
        raise ValueError('non-pass disposition requires a reason')
    return status, scope


def completion_status(records, *, scope, implementation_ids, paper_scope_ids,
                      numerical_agreement):
    """Evaluate explicit C01–C18 evidence without equating accuracy to completeness.

    The caller must freeze the implementation criterion subset before outcomes;
    it is echoed in the report. Full paper completion always needs every C01–C18
    record passed for scope='full_paper'. An initial milestone cannot establish
    full coverage. Evidence references are not proof that artifacts exist.
    """
    if not isinstance(records, Mapping) or set(records) != CRITERIA:
        raise ValueError('exact C01–C18 criterion denominator required')
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError('explicit evaluation scope required')
    implementation_ids, paper_scope_ids = set(implementation_ids), set(paper_scope_ids)
    if not implementation_ids or not implementation_ids <= CRITERIA:
        raise ValueError('nonempty registered implementation criteria required')
    if paper_scope_ids != CRITERIA:
        raise ValueError('full paper criteria cannot be narrowed')
    checked = {key: _disposition(record, {'passed', 'failed', 'blocked', 'pending', 'unavailable'})
               for key, record in records.items()}
    unresolved = lambda ids: sorted(key for key in ids if checked[key] != ('passed', scope))
    implementation_missing = unresolved(implementation_ids)
    paper_missing = unresolved(paper_scope_ids)
    numerical_status, numerical_scope = _disposition(numerical_agreement, {'matched', 'different', 'unavailable', 'pending'})
    agreement = None
    if numerical_scope == scope and numerical_status in {'matched', 'different'}:
        agreement = numerical_status == 'matched'
    return {'scope': scope, 'implementation_complete': not implementation_missing,
            'paper_scope_complete': scope == 'full_paper' and not paper_missing,
            'numerical_agreement': agreement, 'numerical_agreement_status': numerical_status,
            'implementation_ids': sorted(implementation_ids), 'paper_scope_ids': sorted(paper_scope_ids),
            'unresolved': {'implementation': implementation_missing, 'paper_scope': paper_missing},
            'evidence_verified': False,
            'qualification': 'mechanical disposition check; referenced evidence bytes require independent verification'}
