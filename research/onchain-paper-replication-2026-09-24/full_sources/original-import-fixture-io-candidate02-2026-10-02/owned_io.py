"""Owned IO cleanup only; pure stdlib, no numerical or authority imports."""
import os
import sys
from contextlib import contextmanager

def _require(value,message):
    if not value:raise ValueError(message)

class CleanupFailure(BaseException):
    """An owned close was uncertain; stop the worker, never retry its fd integer."""

_UNSET = object()

def _fatal(error):
    return (isinstance(error,MemoryError) or not isinstance(error,Exception)) and not isinstance(error,CleanupFailure)

def _flatten(errors):
    # Only owned cleanup wrappers carry this tuple; retain actual fatal objects.
    result=[];seen=set();pending=list(reversed(errors))
    while pending:
        error=pending.pop()
        if id(error) in seen:continue
        seen.add(id(error))
        if isinstance(error,CleanupFailure) and hasattr(error,'failures'):
            pending.extend(reversed(error.failures))
        else:result.append(error)
    return result

def _cleanup(actions,*,primary=_UNSET):
    """Close every owned resource once; first actual fatal outranks uncertainty."""
    if primary is _UNSET:primary=sys.exception()
    failures=[]
    for close in actions:
        try:close()
        except BaseException as error:failures.append(error)
    if not failures:return
    causes=_flatten(([primary] if primary is not None else [])+failures)
    selected=next((error for error in causes if _fatal(error)),None)
    if selected is not None:
        others=[error for error in causes if error is not selected]
        for error in others:selected.add_note('owned cleanup evidence: '+type(error).__name__)
        if selected is primary:return
        if others:
            if selected.__cause__ is not None and all(selected.__cause__ is not e for e in others):others.append(selected.__cause__)
            selected.__cause__=others[0] if len(others)==1 else BaseExceptionGroup('prior body/cleanup evidence',others)
        raise selected
    failure=CleanupFailure('score storage cleanup unresolved; worker must stop')
    failure.failures=tuple(causes)
    failure.__cause__=causes[0] if len(causes)==1 else BaseExceptionGroup('body/cleanup failures',causes)
    raise failure

def _close_after_failure(close,primary):
    _cleanup((close,),primary=primary)

def _release(close):
    _cleanup((close,))

@contextmanager
def _closing(value):
    try:yield value
    finally:_release(value.close)

@contextmanager
def _opened(path,mode):
    _require(mode in ('rb','xb'),'explicit immutable file mode required')
    flags=os.O_NOFOLLOW|os.O_CLOEXEC
    flags|=(os.O_RDONLY|os.O_NONBLOCK) if mode=='rb' else (os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    fd=os.open(path,flags,0o600);stream=None
    try:
        stream=os.fdopen(fd,mode,closefd=False)
        yield stream
    finally:
        _cleanup((() if stream is None else (stream.close,))+(lambda:os.close(fd),))

def _read_path(path,limit):
    with _opened(path,'rb') as stream:
        raw=stream.read(limit+1)
        _require(len(raw)<=limit,'immutable metadata bound exceeded')
        return raw
