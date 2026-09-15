"""Pure proposed control assembly; no IO, ranking, weights, PnL or admission.

Checks one caller-declared decision bundle for the four registered value_rev
cells. Supplied hashes, cohorts, scores and UTC millisecond clocks are assertions,
not verified source provenance. No interpretation of signal construction,
reversal sign, common-universe selection, lag policy or funding is inferred.
"""
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

SCOPE = 'readiness-only; pending registered interpretation'
CELLS = ('fees_tercile', 'fees_decile', 'revenue_tercile', 'revenue_decile')
REGISTERED_METRICS = {'fees': 'mcap_over_fees_90d', 'revenue': 'mcap_over_revenue_90d'}
ROLES = ('strategy', 'C1', 'C2')
ORIENTATIONS = ('high_is_long', 'low_is_long')


def _result(**fields):
    return {'scope': SCOPE, 'source_admission': False, 'empirical_admission': False, **fields}


def _clock(value):
    if type(value) is not int or not 0 <= value < 2**63:
        raise ValueError('explicit nonnegative UTC millisecond clock required')
    return value


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('explicit SHA256 reference required')
    return value


def _execution(value, decision):
    if not isinstance(value, dict) or set(value) != {'inputs_sha256', 'policy_sha256', 'lag_ms', 'action_ms'}:
        raise ValueError('exact common execution reference required')
    result = {name: _hash(value[name]) for name in ('inputs_sha256', 'policy_sha256')}
    result.update(lag_ms=_clock(value['lag_ms']), action_ms=_clock(value['action_ms']))
    if result['action_ms'] < decision:
        raise ValueError('action precedes declared decision')
    return result


def _cohort(value):
    if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 10000:
        raise ValueError('nonempty bounded explicit metric cohort required')
    if any(not isinstance(s, str) or not s or len(s) > 128 for s in value) or len(set(value)) != len(value):
        raise ValueError('unique bounded symbol identities required')
    return sorted(value)


def _number(value):
    if type(value) not in (str, int, float) or len(str(value)) > 128:
        raise ValueError('finite bounded numeric score required')
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('invalid numeric score') from exc
    if not number.is_finite() or number and not -308 <= number.adjusted() <= 308:
        raise ValueError('nonfinite or out-of-bound score')
    return str(number)


def assemble(cells, *, decision_ms, execution_ref):
    """Validate supplied parity, preserving all four cells and all three roles.

    Each cell declares cohort, breadth, decision_ms, execution_ref and signals.
    A signal declares the same four fields, orientation, score_source_sha256
    and scores mapping each required symbol to {value, available_ms}. Coverage
    must be exact: missing or extra names are unavailable, never intersected.
    The common reference represents the caller's complete calendar/return/
    funding/cost/capital-charge contract; its contents are not opened or proved.
    A successful result means declared alignment only, not registered semantics.
    """
    errors = []
    try:
        decision = _clock(decision_ms)
        execution = _execution(execution_ref, decision)
    except (ValueError, TypeError) as exc:
        decision = None; execution = None; errors.append(str(exc))
    if not isinstance(cells, dict):
        errors.append('explicit four-cell mapping required'); cells = {}
    elif set(cells) - set(CELLS):
        errors.append('unregistered cell identities supplied')
    output = {}
    for identity in CELLS:
        metric, breadth = identity.split('_')
        result = _result(id=identity, metric=metric, registered_metric=REGISTERED_METRICS[metric], breadth=breadth,
                         status='unavailable', cohort=None, decision_ms=decision,
                         execution_ref=execution, reasons=list(errors), signals={})
        supplied = cells.get(identity)
        cohort = None; signals = {}
        try:
            if not isinstance(supplied, dict) or set(supplied) != {'cohort', 'breadth', 'decision_ms', 'execution_ref', 'signals'}:
                raise ValueError('missing or malformed cell declaration')
            cohort = _cohort(supplied['cohort']); result['cohort'] = cohort
            if supplied['breadth'] != breadth:
                raise ValueError('cell breadth differs from registered identity')
            if _clock(supplied['decision_ms']) != decision:
                raise ValueError('cell decision differs from common clock')
            if _execution(supplied['execution_ref'], decision) != execution:
                raise ValueError('cell execution reference mismatch')
            signals = supplied['signals']
            if not isinstance(signals, dict) or set(signals) - set(ROLES):
                raise ValueError('only strategy/C1/C2 declarations permitted')
        except (ValueError, TypeError, KeyError) as exc:
            result['reasons'].append(str(exc)); signals = {}
        for role in ROLES:
            assembled = _result(role=role, status='unavailable', cohort=cohort,
                                breadth=breadth, decision_ms=decision,
                                execution_ref=execution, orientation=None,
                                score_source_sha256=None, declared_cohort=None, declared_execution_ref=None,
                                scores={s: {'status': 'unavailable', 'value': None, 'available_ms': None,
                                            'reason': 'required score not admitted'} for s in cohort or []}, reasons=[])
            try:
                if result['reasons']:
                    raise ValueError('cell declaration unavailable')
                signal = signals.get(role)
                required = {'cohort', 'breadth', 'decision_ms', 'execution_ref', 'orientation', 'score_source_sha256', 'scores'}
                if not isinstance(signal, dict) or set(signal) != required:
                    raise ValueError('exact signal declaration required')
                assembled['declared_cohort'] = _cohort(signal['cohort'])
                if assembled['declared_cohort'] != cohort:
                    raise ValueError('signal cohort differs; no shrinking or substitution')
                if signal['breadth'] != breadth or _clock(signal['decision_ms']) != decision:
                    raise ValueError('signal breadth/decision mismatch')
                assembled['declared_execution_ref'] = _execution(signal['execution_ref'], decision)
                if assembled['declared_execution_ref'] != execution:
                    raise ValueError('signal execution/lag reference mismatch')
                if signal['orientation'] not in ORIENTATIONS:
                    raise ValueError('explicit signal orientation required')
                assembled['orientation'] = signal['orientation']
                assembled['score_source_sha256'] = _hash(signal['score_source_sha256'])
                scores = signal['scores']
                if not isinstance(scores, dict):
                    raise ValueError('explicit required score mapping required')
                if set(scores) - set(cohort):
                    assembled['reasons'].append('extra score identities; no intersection')
                for symbol in cohort:
                    try:
                        row = scores.get(symbol)
                        if not isinstance(row, dict) or set(row) != {'value', 'available_ms'}:
                            raise ValueError('explicit score/availability required')
                        available = _clock(row['available_ms'])
                        assembled['scores'][symbol]['available_ms'] = available
                        if available > decision:
                            raise ValueError('score available after decision')
                        assembled['scores'][symbol] = {'status': 'declared_aligned', 'value': _number(row['value']), 'available_ms': available, 'reason': None}
                    except (ValueError, TypeError) as exc:
                        assembled['scores'][symbol]['reason'] = str(exc)
                        assembled['reasons'].append(symbol + ': ' + str(exc))
                if not assembled['reasons']:
                    assembled['status'] = 'declared_aligned'
            except (ValueError, TypeError, KeyError) as exc:
                assembled['reasons'].append(str(exc))
            result['signals'][role] = assembled
        if not result['reasons'] and all(r['status'] == 'declared_aligned' for r in result['signals'].values()):
            result['status'] = 'declared_aligned'
        else:
            result['reasons'].extend(role + ': required signal unavailable' for role in ROLES if result['signals'][role]['status'] != 'declared_aligned')
        output[identity] = result
    answer = _result(cells=output, registered_cell_count=4, reasons=errors,
                     status='declared_aligned' if all(c['status'] == 'declared_aligned' for c in output.values()) else 'unavailable',
                     provenance='Caller declarations only; no source, witness, policy approval or financial pipeline verified.')
    answer['assembly_sha256'] = hashlib.sha256(json.dumps(answer, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return answer
