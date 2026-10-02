"""Bounded descriptor-owned import metadata; no stream wrappers or FD retry."""
import hashlib
import os
from pathlib import Path
import stat
from . import original_dictionary as original,score_batches as io
LIMIT=65536


def require(value,message):
    if not value:raise ValueError(message)


def signature(value):
    return tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))


def _root(root,fd):
    require(root.resolve()==root and not root.is_symlink(),'import metadata root redirected')
    before=root.stat();opened=os.fstat(fd)
    require(stat.S_ISDIR(opened.st_mode) and (before.st_dev,before.st_ino)==(opened.st_dev,opened.st_ino),'import metadata parent rejoined incorrectly')
    return opened


def _name(name):
    require(type(name) is str and name not in ('','.','..') and '/' not in name and '\x00' not in name,'single metadata leaf required')


def write(root,name,raw):
    root=Path(root);_name(name)
    require(type(raw) is bytes and len(raw)<=LIMIT,'bounded exact metadata bytes required')
    parent=child=None
    try:
        parent=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);directory=_root(root,parent)
        child=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_NONBLOCK,0o600,dir_fd=parent)
        info=os.fstat(child)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_dev==directory.st_dev,'import metadata file type/device')
        view=memoryview(raw);offset=0
        while offset<len(view):
            count=os.write(child,view[offset:]);require(type(count) is int and count>0,'metadata short write');offset+=count
        os.fsync(child);os.fsync(parent);_root(root,parent)
        after=os.fstat(child);current=os.stat(name,dir_fd=parent,follow_symlinks=False)
        require(after.st_size==len(raw) and signature(after)==signature(current) and after.st_nlink==1,'import metadata publication changed')
        return hashlib.sha256(raw).hexdigest()
    finally:
        original._close_owned(tuple(fd for fd in (child,parent) if fd is not None),io)


def read(root,name):
    root=Path(root);_name(name);parent=child=None
    try:
        parent=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);directory=_root(root,parent)
        child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
        before=os.fstat(child)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_dev==directory.st_dev and 0<=before.st_size<=LIMIT,'import metadata read type/extent')
        chunks=[];size=0
        while True:
            raw=os.read(child,min(16384,LIMIT+1-size))
            if not raw:break
            chunks.append(raw);size+=len(raw);require(size<=LIMIT,'import metadata grew beyond limit')
        _root(root,parent);after=os.fstat(child);current=os.stat(name,dir_fd=parent,follow_symlinks=False)
        require(size==before.st_size and signature(before)==signature(after)==signature(current),'import metadata changed during read')
        return b''.join(chunks)
    finally:
        original._close_owned(tuple(fd for fd in (child,parent) if fd is not None),io)


def exact(root,name,raw):
    require(type(raw) is bytes and read(root,name)==raw,'import metadata exact bytes differ')


def birth(root):
    root=Path(root);parent=None
    try:
        parent=os.open(root.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);_root(root.parent,parent)
        _name(root.name);os.mkdir(root.name,dir_fd=parent);os.fsync(parent);_root(root.parent,parent)
        info=os.stat(root.name,dir_fd=parent,follow_symlinks=False)
        require(stat.S_ISDIR(info.st_mode) and root.resolve()==root,'import stage directory changed')
        return (info.st_dev,info.st_ino)
    finally:original._close_owned(tuple(fd for fd in (parent,) if fd is not None),io)


def metadata(path,root):
    import json
    path=Path(path);root=Path(root)
    require(path.is_absolute() and path.resolve()==path and path.is_relative_to(root) and path.stat().st_dev==root.stat().st_dev,'import Binding metadata containment/device differs')
    raw=read(path.parent,path.name)
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


def close_actions(actions):
    """Close each descriptor once; select actual fatal errors before wrapping."""
    import sys
    primary=sys.exception();errors=[]
    fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
    for action in actions:
        try:action()
        except BaseException as error:errors.append(error)
    if not errors:return
    selected=primary if primary is not None and fatal(primary) else next((e for e in errors if fatal(e)),None)
    if selected is not None:
        for error in errors:
            if error is not selected:selected.add_note('import descriptor close unresolved: '+type(error).__name__)
        if selected is primary:return
        earlier=errors[:next(i for i,e in enumerate(errors) if e is selected)]
        prior=([primary] if primary is not None else [])+earlier
        if prior:
            cause=prior[0] if len(prior)==1 else ExceptionGroup('prior import body/close failures',prior)
            if selected.__cause__ is not None and selected.__cause__ is not cause:
                cause=BaseExceptionGroup('prior import evidence and original fatal cause',[cause,selected.__cause__])
            selected.__cause__=cause
        raise selected
    # Only ordinary cleanup errors remain. Construct the terminal wrapper now,
    # after every owned descriptor and actual fatal have been considered.
    failure=io.CleanupFailure('import descriptor close unresolved')
    causes=([primary] if primary is not None else [])+errors
    failure.__cause__=causes[0] if len(causes)==1 else ExceptionGroup('import body/close failures',causes)
    for error in errors:failure.add_note(type(error).__name__)
    raise failure

def entries(root,allowed,*,required):
    root=Path(root);fd=None;iterator=None
    try:
        fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);_root(root,fd)
        iterator=os.scandir(fd);seen=set()
        for entry in iterator:
            require(len(seen)<len(allowed) and entry.name in allowed,'foreign compact owner inventory')
            seen.add(entry.name)
        require(required<=seen,'missing compact owner inventory');_root(root,fd)
    finally:
        actions=[]
        if iterator is not None:actions.append(iterator.close)
        if fd is not None:actions.append(lambda:os.close(fd))
        close_actions(actions)
