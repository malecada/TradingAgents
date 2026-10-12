"""Opt-in scalar, exclusive wall/CPU timings; never execution authority."""
from contextlib import contextmanager
from contextvars import ContextVar
import math
import threading
import time

FORMAT='exclusive-wall-cpu-v1'
PHASES=frozenset(('entry','source_admission','role_read','lease_full',
    'lease_fingerprint','lease_live','module_auth','source_read','source_compile',
    'backend_setup','pair_numeric','state_scan','row_extraction','authority_boundary','cache_key','checkpoint',
    'checkpoint_inventory','offload','storage_scan','publication'))
NUMERIC_COUNTS=frozenset(('agreement_scalar_chunks','agreement_numpy_chunks',
    'agreement_native_chunks','agreement_fallback_chunks','agreement_scalar_entries',
    'agreement_numpy_entries','agreement_native_entries','chunk_lt8_calls',
    'chunk_8to255_calls','chunk_256to1023_calls','chunk_1024_calls',
    'cache_hit_chunks','cache_hit_entries','cache_allocations','cache_allocated_bytes','cache_released_bytes'))
_ACTIVE=ContextVar('onchain_phase_totals',default=None)


class PhaseTotals:
    def __init__(self,*,wall_clock=time.monotonic,cpu_clock=time.process_time):
        self.wall_clock=wall_clock;self.cpu_clock=cpu_clock
        self._phases={};self._counts={};self._stack=[];self._thread=None;self.invalid_measurements=0

    def _row(self,name):
        if name not in PHASES:raise ValueError('unknown timing phase')
        return self._phases.setdefault(name,dict(calls=0,failures=0,wall_seconds=0.,cpu_seconds=0.,bytes=0))

    def _now(self):
        values=(self.wall_clock(),self.cpu_clock())
        if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in values):
            raise ValueError('invalid phase clock')
        return values

    @contextmanager
    def measure(self,name):
        row=self._row(name);thread=threading.get_ident()
        if self._thread is not None and self._thread!=thread:
            raise ValueError('phase collector cannot span threads')
        start=self._now();frame=[name,start,0.,0.];self._stack.append(frame);self._thread=thread
        primary=None
        try:yield
        except BaseException as error:
            primary=error;raise
        finally:
            self._stack.pop()
            if not self._stack:self._thread=None
            row['calls']+=1;row['failures']+=int(primary is not None)
            try:
                end=self._now();wall=end[0]-start[0];cpu=end[1]-start[1]
                if wall<frame[2]-1e-9 or cpu<frame[3]-1e-9:
                    raise ValueError('backward or inconsistent phase clock')
                row['wall_seconds']+=max(0.,wall-frame[2]);row['cpu_seconds']+=max(0.,cpu-frame[3])
                if self._stack:
                    self._stack[-1][2]+=wall;self._stack[-1][3]+=cpu
            except BaseException as secondary:
                self.invalid_measurements+=1
                if primary is None:raise
                try:primary.add_note('phase timing unavailable: '+type(secondary).__name__)
                except BaseException:pass

    def add_bytes(self,name,count):
        if type(count) is not int or not 0<=count<2**127:raise ValueError('invalid phase byte count')
        self._row(name)['bytes']+=count

    def add_count(self,name,count):
        """Finite scalar observations only; no graph or arbitrary label retained."""
        if name not in NUMERIC_COUNTS:raise ValueError('unknown numeric count')
        if type(count) is not int or not 0<=count<2**127:raise ValueError('invalid numeric count')
        total=self._counts.get(name,0)+count
        if total>=2**127:raise ValueError('numeric count overflow')
        self._counts[name]=total

    def snapshot(self):
        if self._stack:raise ValueError('active phase snapshot unavailable')
        return {'format':FORMAT,'phases':{k:dict(v) for k,v in sorted(self._phases.items())},
            'numeric_counts':dict(sorted(self._counts.items())),
            'invalid_measurements':self.invalid_measurements,'counters':'cumulative/exclusive/process-local',
            'authority':False}


@contextmanager
def activate(totals):
    if type(totals) is not PhaseTotals:raise ValueError('actual phase collector required')
    previous=_ACTIVE.get()
    if previous is not None and previous is not totals:raise ValueError('nested phase collector replaced')
    token=_ACTIVE.set(totals)
    try:yield totals
    finally:_ACTIVE.reset(token)


@contextmanager
def measure(name):
    totals=_ACTIVE.get()
    if totals is None:yield
    else:
        with totals.measure(name):yield


def add_bytes(name,count):
    totals=_ACTIVE.get()
    if totals is not None:totals.add_bytes(name,count)


def add_count(name,count):
    totals=_ACTIVE.get()
    if totals is not None:totals.add_count(name,count)


def current_snapshot():
    """Cumulative batch-boundary observation, never a completion receipt."""
    totals=_ACTIVE.get()
    return None if totals is None else totals.snapshot()


def run_profiled(operation,publish):
    """Publish scalar timings on success/failure; retain the original fatal.

    The first admission selecting this instrumentation and this final timing
    publication are outside the measurement. No Run or authority is created.
    """
    totals=PhaseTotals()
    with activate(totals):
        try:result=operation()
        except BaseException as primary:
            from .failure_reporting import record_failure
            record_failure(primary,(lambda:publish(totals.snapshot()),))
            raise
    publish(totals.snapshot())
    return result
