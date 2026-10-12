from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3]
for name,path in [('admission.py','tradingagents/research/admission.py'),('lifecycle.py','tradingagents/research/lifecycle.py'),('compact_mcm_batched.py','tradingagents/research/onchain_replication/compact_mcm_batched.py')]:
 raw=(R/path).read_bytes();(P/('BASELINE_'+name)).write_bytes(raw);(P/name).write_bytes(raw)
p=P/'admission.py';s=p.read_text();helpers='''
# Selected history snapshots contain metadata only, never Git bodies/processes.
# Weak identity keys own independent snapshots; no state is accepted from callers.
from weakref import WeakKeyDictionary
import hmac
import os
import stat
import threading
import time
import math
_HISTORY = WeakKeyDictionary()
_HISTORY_BUSY = WeakKeyDictionary()
_HISTORY_MUTEX = threading.Lock()
_HISTORY_SEAL_KEY = os.urandom(32)
_HISTORY_MAX_RUNS = 512
_HISTORY_MAX_BODY = 8 * 1024**2
_HISTORY_MAX_BYTES = 64 * 1024**2


def _history_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _history_policy(value):
    if type(value) is dict and value.get('format') == 'bounded-claims-v2':
        if (set(value) != {'format', 'workers', 'max_audit_seconds'}
                or type(value['workers']) is not int or value['workers'] not in (1, 2)
                or type(value['max_audit_seconds']) is not int or value['max_audit_seconds'] != 300):
            raise ValueError('exact bounded history audit policy required')
        return value['workers'], 300
    return _claim_workers(value), None


def _history_frontier(root):
    folder = root / 'research_runs'
    if not folder.exists():
        return ()
    if folder.is_symlink() or folder.resolve() != folder:
        raise ValueError('canonical history directory required')
    children = []
    for child in folder.iterdir():
        if child.name.startswith('.'):
            continue
        children.append(child)
        if len(children) > _HISTORY_MAX_RUNS:
            raise ValueError('bounded history roster exceeded')
    rows = []; total = 0
    for child in sorted(children):
        identity(child.name, 'historical run')
        if child.is_symlink() or not child.is_dir() or child.resolve() != child:
            raise ValueError('canonical history child required')
        pins = []
        for name in ('claim.json', 'complete.json', 'failed.json'):
            path = child / name
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            except FileNotFoundError:
                if name == 'claim.json':
                    raise ValueError('partial run claim requires manual recovery; automatic reuse prohibited')
                pins.append(None); continue
            with os.fdopen(fd, 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError('regular history body required')
                raw = stream.read(min(_HISTORY_MAX_BODY, _HISTORY_MAX_BYTES-total)+1)
            total += len(raw)
            if len(raw) > _HISTORY_MAX_BODY or total > _HISTORY_MAX_BYTES:
                raise ValueError('bounded history metadata exceeded')
            pins.append(digest(raw))
        rows.append((child.name, *pins))
    return tuple(rows)


def _history_anchor(run, root, registration, experiment, source, design_source, raw, policy):
    from .lifecycle import ResearchRun
    if (type(run) is not ResearchRun or run.admission.root != root
            or run.directory != root / 'research_runs' / experiment
            or run.admission.experiment_id != experiment
            or run.admission.source != source or run.admission.design_source != design_source
            or run.admission.registration != registration
            or run.admission.registration_sha256 != digest(raw)
            or run.admission.spec != json.loads(raw)):
        raise ValueError('same genuine run history authority required')
    run._active()
    return _history_bytes((str(root), experiment, source, design_source, registration,
        digest(raw), run._claim_sha256, run.admission.bindings, run.admission.bindings_sha256,
        digest(_history_bytes(run.admission.experiment)), digest(_history_bytes(run.admission.inputs)), policy))


def _history_seal(state):
    return hmac.digest(_HISTORY_SEAL_KEY, _history_bytes(state), 'sha256')


def _history_prior(run, root, registration, experiment, source, design_source, raw, policy, force):
    workers, seconds = _history_policy(policy)
    if type(force) is not bool or seconds != 300:
        raise ValueError('explicit finite history force required')
    if run is None:
        # Startup retains a fresh original full sweep. No transferable seed.
        prior = claims(root) if workers == 1 else claims(root, workers=workers)
        if any(not any((root/'research_runs'/c['experiment_id']/n).exists()
                for n in ('complete.json','failed.json')) for c in prior):
            raise ValueError('another active run prohibits selected history mode')
        return prior
    anchor = _history_anchor(run,root,registration,experiment,source,design_source,raw,policy)
    owner = threading.get_ident()
    with _HISTORY_MUTEX:
        if run in _HISTORY_BUSY:
            raise ValueError('concurrent history snapshot use prohibited')
        _HISTORY_BUSY[run] = owner
    try:
        now = time.monotonic()
        if not math.isfinite(now) or now < 0:
            raise ValueError('finite monotonic history clock required')
        saved = _HISTORY.get(run)
        if saved is not None:
            state, seal = saved
            if not hmac.compare_digest(_history_seal(state), seal):
                raise ValueError('history snapshot seal differs')
            old_anchor, frontier, encoded, audited, last, thread = state
            if old_anchor != anchor.hex() or thread != owner:
                raise ValueError('history snapshot authority/thread differs')
            if now < last or audited > last:
                raise ValueError('history clock moved backwards')
        current = _history_frontier(root)
        if any(name != experiment and complete is None and failed is None
                for name, claim, complete, failed in current):
            raise ValueError('another active run prohibits selected history mode')
        if saved is None or force or now-audited >= seconds or current != frontier:
            prior = claims(root) if workers == 1 else claims(root, workers=workers)
            encoded = _history_bytes(prior).hex()
            if len(encoded) > 2*_HISTORY_MAX_BYTES:
                raise ValueError('bounded verified history exceeded')
            audited = now
        else:
            # Own claim's complete original Git/design verification stays fresh.
            own = _verify_claim_child(run.directory)
            prior = json.loads(bytes.fromhex(encoded))
            previous = next((c for c in prior if c['experiment_id'] == experiment), None)
            if _history_bytes(own) != _history_bytes(previous):
                raise ValueError('own verified claim changed')
        end = time.monotonic()
        if not math.isfinite(end) or end < now:
            raise ValueError('history clock moved backwards')
        if (_history_frontier(root) != current
                or _history_anchor(run,root,registration,experiment,source,design_source,raw,policy) != anchor):
            raise ValueError('history frontier/authority changed during verification')
        state = (anchor.hex(), current, encoded, audited, end, owner)
        _HISTORY[run] = (state, _history_seal(state))
        return prior
    except BaseException:
        _HISTORY.pop(run, None)
        raise
    finally:
        with _HISTORY_MUTEX:
            _HISTORY_BUSY.pop(run, None)

'''
s=s.replace('\n\n@dataclass(frozen=True)\nclass Admission:', '\n'+helpers+'\n@dataclass(frozen=True)\nclass Admission:')
s=s.replace('_own_claim=None) -> Admission:', '_own_claim=None, _history_run=None, _force_history=False) -> Admission:')
s=s.replace("claim_workers = (_claim_workers(spec['historical_claim_verification'])\n                     if 'historical_claim_verification' in spec else 1)","claim_workers, history_seconds = (_history_policy(spec['historical_claim_verification'])\n                     if 'historical_claim_verification' in spec else (1, None))\n    if type(_force_history) is not bool or (_history_run is not None and _own_claim != experiment):\n        raise ValueError('private history invocation differs')")
old='    prior = claims(root) if claim_workers == 1 else claims(root, workers=claim_workers)'
s=s.replace(old,"    if history_seconds is None:\n"+old+'\n' if False else "    if history_seconds is None:\n        prior = claims(root) if claim_workers == 1 else claims(root, workers=claim_workers)\n    else:\n        prior = _history_prior(_history_run, root, registration, experiment, source, design_source,\n            raw, spec['historical_claim_verification'], _force_history)")
p.write_text(s)
p=P/'lifecycle.py';s=p.read_text();s=s.replace('    def _check_source(self):','    def _check_source(self, *, force_history=False):')
s=s.replace('        with measure("source_admission"):\n            current = admit', '''        history_policy = self.admission.spec.get('historical_claim_verification')
        selected = type(history_policy) is dict and history_policy.get('format') == 'bounded-claims-v2'
        if type(force_history) is not bool:
            raise ValueError('Boolean history force required')
        history_args = {'_history_run': self, '_force_history': force_history} if selected else {}
        with measure("source_admission"):
            current = admit''')
s=s.replace('_own_claim=self.admission.experiment_id)', '_own_claim=self.admission.experiment_id, **history_args)')
s=s.replace('            try:\n                self._check_source()\n                self._check_inputs()', '            try:\n                if self.admission.spec.get("historical_claim_verification", {}).get("format") == "bounded-claims-v2":\n                    self._check_source(force_history=True)\n                else:\n                    self._check_source()\n                self._check_inputs()')
p.write_text(s)
p=P/'compact_mcm_batched.py';s=p.read_text();needle="        result=modules['driver'].drive(";i=s.index(needle)
s=s[:i]+'''        history_run=target.owner.bound._run
        if history_run.admission.spec.get('historical_claim_verification',{}).get('format')=='bounded-claims-v2':
            original_post_batch=post_batch
            def audited_post_batch(j,batch,token,original):
                history_run._check_source(force_history=True)
                if original_post_batch is not None:original_post_batch(j,batch,token,original)
            post_batch=audited_post_batch
'''+s[i:];p.write_text(s)
