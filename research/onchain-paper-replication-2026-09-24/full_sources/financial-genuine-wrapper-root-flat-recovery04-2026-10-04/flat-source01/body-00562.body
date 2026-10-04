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
    io._cleanup(actions)


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
