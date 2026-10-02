"""Bounded, callback-free byte/inode authority. No scientific admission alone."""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat


def require(value,message):
    if not value:raise ValueError(message)


def fatal(error):
    return error is not None and (isinstance(error,(MemoryError,RecursionError)) or not isinstance(error,Exception))


def preserve(primary,later):
    if fatal(primary):return primary
    if fatal(later):return later
    return primary if later is None else later


def signature(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def read_hash(path,limit,chunk):
    before=path.lstat();require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'cold file layout/capacity differs')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW);primary=None
    try:
        require(signature(os.fstat(fd))==signature(before),'cold file changed before open')
        digest=hashlib.sha256();total=0
        while True:
            raw=os.read(fd,chunk)
            if not raw:break
            total+=len(raw);require(total<=limit,'cold file grew beyond cap');digest.update(raw)
        require(total==before.st_size and signature(os.fstat(fd))==signature(before)
            and signature(path.lstat())==signature(before),'cold file changed during read')
        return signature(before),digest.hexdigest()
    except BaseException as error:primary=error;raise
    finally:
        try:os.close(fd)
        except BaseException as close_error:
            if fatal(primary):raise primary
            if fatal(close_error):raise
            raise RuntimeError('cold descriptor closure unresolved') from close_error


@dataclass(frozen=True)
class Snapshot:
    root:Path
    roots:tuple
    bounds:tuple
    directories:tuple
    files:tuple
    def check(self,*,full):
        current=_scan(self.root,self.roots,dict(self.bounds),full=full)
        require(current.directories==self.directories,'cold directory population/identity changed')
        require(tuple((p,s) for p,s,h in current.files)==tuple((p,s) for p,s,h in self.files),'cold file population/identity changed')
        if full:require(current.files==self.files,'cold saved bytes changed')


def _scan(root,roots,bounds,*,full):
    root=Path(root);require(root.is_absolute() and root.resolve()==root,'cold root redirected')
    required={'max_files','max_directories','max_total_bytes','max_file_bytes','max_depth','chunk_bytes'}
    require(set(bounds)==required and all(type(v) is int and 0<v<2**63 for v in bounds.values())
        and bounds['chunk_bytes']<=1024**2,'cold scan limits differ')
    require(type(roots) is tuple and roots and len(set(roots))==len(roots),'cold roots duplicate/empty')
    paths=[]
    for rel in roots:
        p=Path(rel);require(type(rel) is str and not p.is_absolute() and '..' not in p.parts and str(p)==rel and rel!='.','cold root escape')
        require(not any(p==q or p.is_relative_to(q) or q.is_relative_to(p) for q in paths),'cold roots overlap');paths.append(p)
    files=[];directories=[];total=0;device=root.stat().st_dev
    stack=[(root/p,0) for p in paths]
    while stack:
        path,depth=stack.pop();require(depth<=bounds['max_depth'] and path.resolve()==path,'cold depth/redirect differs')
        info=path.lstat();require(stat.S_ISDIR(info.st_mode) and info.st_dev==device,'cold directory layout differs')
        fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        primary=None
        try:
            require(signature(os.fstat(fd))==signature(info),'cold directory changed before open')
            names=[]
            with os.scandir(fd) as entries:
                for entry in entries:
                    require(len(names)<bounds['max_files']+bounds['max_directories'],'cold directory entry cap exceeded');names.append(entry.name)
            names=tuple(sorted(names));directories.append((str(path.relative_to(root)),(info.st_dev,info.st_ino,info.st_mode),names))
            require(len(directories)<=bounds['max_directories'],'cold directory cap exceeded')
            for name in names:
                child=path/name;s=child.lstat();rel=str(child.relative_to(root))
                require(not stat.S_ISLNK(s.st_mode) and s.st_dev==device,'cold member redirected/device differs')
                if stat.S_ISDIR(s.st_mode):stack.append((child,depth+1));continue
                require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=bounds['max_file_bytes'],'cold file layout differs')
                total+=s.st_size;require(total<=bounds['max_total_bytes'] and len(files)<bounds['max_files'],'cold total capacity exceeded')
                pin,sha=read_hash(child,bounds['max_file_bytes'],bounds['chunk_bytes']) if full else (signature(s),None)
                files.append((rel,pin,sha))
            require(signature(os.fstat(fd))==signature(info) and signature(path.lstat())==signature(info),'cold directory changed during scan')
        except BaseException as error:primary=error;raise
        finally:
            try:os.close(fd)
            except BaseException as error:
                if fatal(primary):raise primary
                if fatal(error):raise
                raise RuntimeError('cold directory closure unresolved') from error
    return Snapshot(root,roots,tuple(sorted(bounds.items())),tuple(sorted(directories)),tuple(sorted(files)))


def capture(root,roots,bounds):return _scan(root,roots,bounds,full=True)


def write_once(root,inode,name,raw,cap):
    """Exclusive bytes under a captured directory; failed partial files remain."""
    require(type(raw) is bytes and len(raw)<=cap and type(name) is str and Path(name).name==name,'cold publication capacity/name differs')
    root=Path(root);require(root.resolve()==root,'cold publication root redirected')
    dfd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);fd=None;primary=None
    try:
        info=os.fstat(dfd);require((info.st_dev,info.st_ino)==inode,'cold publication directory replaced')
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=dfd)
        view=memoryview(raw)
        while view:
            count=os.write(fd,view);require(count>0,'cold publication made no progress');view=view[count:]
        os.fsync(fd);os.fsync(dfd)
        current=root.lstat();require((current.st_dev,current.st_ino)==inode and root.resolve()==root,'cold publication root changed')
    except BaseException as error:primary=error
    for descriptor in (fd,dfd):
        if descriptor is not None:
            try:os.close(descriptor)
            except BaseException as error:primary=preserve(primary,error)
    if primary is not None:raise primary
