from pathlib import Path
P=Path(__file__).resolve().parent;p=P/'admission.py';s=p.read_text();(P/'RAW_admission01.py').write_text(s)
i=s.index('\ndef _history_prior(')
helper='''
def _history_scan(root, workers, previous=None, *, force=False, own=None):
    """Bounded metadata calculation, not an admission grant or reusable token.

    Production callers supply previous only after genuine run/seal verification.
    The standalone benchmark may retain this tuple but cannot insert it into a run.
    """
    if type(force) is not bool or type(workers) is not int or workers not in (1, 2):
        raise ValueError('finite history scan policy required')
    now = time.monotonic()
    if not math.isfinite(now) or now < 0:
        raise ValueError('finite monotonic history clock required')
    if previous is not None:
        frontier, encoded, audited, last = previous
        if now < last or audited > last:
            raise ValueError('history clock moved backwards')
    current = _history_frontier(root)
    if any(name != own and complete is None and failed is None
            for name, claim, complete, failed in current):
        raise ValueError('another active run prohibits selected history mode')
    full = previous is None or force or now-audited >= 300 or current != frontier
    if full:
        prior = claims(root) if workers == 1 else claims(root, workers=workers)
        encoded = _history_bytes(prior).hex()
        if len(encoded) > 2*_HISTORY_MAX_BYTES:
            raise ValueError('bounded verified history exceeded')
        audited = now
    else:
        prior = json.loads(bytes.fromhex(encoded))
        if own is not None:
            # Own claim's complete original Git/design verification stays fresh.
            verified = _verify_claim_child(root/'research_runs'/own)
            original = next((c for c in prior if c['experiment_id'] == own), None)
            if _history_bytes(verified) != _history_bytes(original):
                raise ValueError('own verified claim changed')
    end = time.monotonic()
    if not math.isfinite(end) or end < now:
        raise ValueError('history clock moved backwards')
    if _history_frontier(root) != current:
        raise ValueError('history frontier changed during verification')
    return (current, encoded, audited, end), prior, full

'''
s=s[:i]+helper+s[i:]
a=s.index('    try:\n        now = time.monotonic()',s.index('def _history_prior'))
b=s.index('\n\n@dataclass',a)
s=s[:a]+'''    primary = None
    try:
        saved = _HISTORY.get(run)
        previous = None
        if saved is not None:
            state, seal = saved
            if not hmac.compare_digest(_history_seal(state), seal):
                raise ValueError('history snapshot seal differs')
            old_anchor, previous, thread = state
            if old_anchor != anchor.hex() or thread != owner:
                raise ValueError('history snapshot authority/thread differs')
        snapshot, prior, full = _history_scan(root, workers, previous, force=force, own=experiment)
        if _history_anchor(run,root,registration,experiment,source,design_source,raw,policy) != anchor:
            raise ValueError('history authority changed during verification')
        state = (anchor.hex(), snapshot, owner)
        _HISTORY[run] = (state, _history_seal(state))
        return prior
    except BaseException as error:
        primary = error
        try:
            _HISTORY.pop(run, None)
        except BaseException as cleanup:
            _claim_failure_note(primary, 'history invalidation failed', cleanup)
        raise
    finally:
        try:
            with _HISTORY_MUTEX:
                _HISTORY_BUSY.pop(run, None)
        except BaseException as cleanup:
            if primary is not None:
                _claim_failure_note(primary, 'history release failed', cleanup)
            else:
                try:
                    _HISTORY.pop(run, None)
                except BaseException as invalidation:
                    _claim_failure_note(cleanup, 'history invalidation failed', invalidation)
                raise
''' +s[b:]
p.write_text(s)
