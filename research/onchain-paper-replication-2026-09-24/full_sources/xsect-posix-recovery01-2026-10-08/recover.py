"""Opaque POSIX reconstruction into an exclusive new tree; no original reads."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
from contextlib import contextmanager
from tradingagents.research.onchain_replication.preservation import verify_bundle

BLOCK=1024*1024

def require(ok,why):
    if not ok:raise ValueError(why)

def _relative(value,*,directory=False):
    require(type(value) is str and '\x00' not in value and '\\' not in value and len(value)<=4096,'invalid relative path')
    if directory and value=='.':return ()
    parts=value.split('/')
    require(parts and len(parts)<=64 and all(p not in ('','.','..') for p in parts),'noncanonical relative path')
    return tuple(parts)

def _absolute(value):
    value=str(value);p=PurePosixPath(value)
    require(p.is_absolute() and str(p)==value and '..' not in p.parts and len(p.parts)<=64,'canonical absolute path required')
    return p

def _layout(rows,directories,original_root,*,max_files,max_total_bytes,max_file_bytes):
    require(all(type(n) is int and 0<n<2**63 for n in (max_files,max_total_bytes,max_file_bytes)),'finite positive bounds required')
    require(type(rows) is list and 0<len(rows)<=max_files and type(directories) is list and 0<len(directories)<=max_files+1,'bounded complete inventory required')
    origin=_absolute(original_root);files={};dirs={};total=0
    for collection,is_dir,result in ((directories,True,dirs),(rows,False,files)):
        for row in collection:
            require(type(row) is dict,'row must be object');name=row['relative_path'];_relative(name,directory=is_dir)
            require(name not in result,'duplicate path')
            require(row['kind']==('directory' if is_dir else 'regular') and type(row['mode']) is int and (stat.S_ISDIR(row['mode']) if is_dir else stat.S_ISREG(row['mode'])),'typed mode differs')
            require(type(row['mtime_ns']) is int and -(2**63)<row['mtime_ns']<2**63,'mtime bound')
            require(row.get('posix_mode',format(stat.S_IMODE(row['mode']),'04o'))==format(stat.S_IMODE(row['mode']),'04o'),'POSIX mode differs')
            expected=str(origin if name=='.' else origin/name)
            require(row['source_path']==expected and (is_dir or row['resolved_path']==expected),'original namespace differs')
            if not is_dir:
                require(type(row['bytes']) is int and 0<=row['bytes']<=max_file_bytes and row['bytes']==row['logical_bytes'] and row['nlink']==1,'file extent/link count differs')
                require(type(row['expected_sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['expected_sha256']),'file digest differs')
                total+=row['bytes'];require(total<=max_total_bytes,'whole payload exceeds bound')
            result[name]=row
    require('.' in dirs and not files.keys()&dirs.keys(),'root or namespace differs')
    for name in (*files,*dirs):
        if name=='.':continue
        parent=str(PurePosixPath(name).parent)
        require(parent in dirs,'missing explicit parent directory')
    return files,dirs,total

@contextmanager
def _walk(fd,parts):
    current=os.dup(fd)
    try:
        for part in parts:
            following=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=current)
            os.close(current);current=following
        yield current
    finally:os.close(current)

def _open_root(target_root,original_root):
    target=_absolute(target_root);origin=_absolute(original_root)
    require(not target.is_relative_to(origin) and not origin.is_relative_to(target),'recovery/original namespaces overlap')
    base=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        with _walk(base,target.parts[1:]) as fd:return os.dup(fd)
    finally:os.close(base)

def _identity(fd,pin):
    info=os.fstat(fd);require((info.st_dev,info.st_ino)==tuple(pin),'new root identity changed')


def create_new_tree(target_root,rows,directories,*,original_root,max_files,max_total_bytes,max_file_bytes):
    """Create root and all directories exclusively; return (device,inode) pin."""
    _,dirs,_=_layout(rows,directories,original_root,max_files=max_files,max_total_bytes=max_total_bytes,max_file_bytes=max_file_bytes)
    target=_absolute(target_root);origin=_absolute(original_root)
    require(not target.is_relative_to(origin) and not origin.is_relative_to(target),'recovery/original namespaces overlap')
    base=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        with _walk(base,target.parts[1:-1]) as parent:
            os.mkdir(target.name,0o700,dir_fd=parent);os.fsync(parent)
    finally:os.close(base)
    fd=_open_root(target_root,original_root)
    try:
        for name in sorted(dirs,key=lambda n:(len(_relative(n,directory=True)),n)):
            if name=='.':continue
            parts=_relative(name)
            with _walk(fd,parts[:-1]) as parent:
                os.mkdir(parts[-1],0o700,dir_fd=parent);os.fsync(parent)
        os.fsync(fd);info=os.fstat(fd);return (info.st_dev,info.st_ino)
    finally:os.close(fd)


def _signature(info):
    return tuple(getattr(info,n) for n in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))


def recover_bundle(archive,manifest,expected_rows,target_root,*,directories,original_root,root_pin,batch,max_files,max_total_bytes,max_file_bytes,max_archive_bytes):
    """Recover exactly one declared complete bundle; failures retain partials."""
    _layout(expected_rows,directories,original_root,max_files=max_files,max_total_bytes=max_total_bytes,max_file_bytes=max_file_bytes)
    require(type(batch) is dict and set(batch)=={'index','start','stop','raw_bytes'} and all(type(v) is int for v in batch.values()),'batch schema differs')
    start,stop=batch['start'],batch['stop'];require(batch['index']>=0 and 0<=start<stop<=len(expected_rows),'batch bounds differ')
    selected=expected_rows[start:stop];expected=[{**row,'member':f'files/{i:08d}'} for i,row in enumerate(selected,start)]
    require(type(manifest) is dict and set(manifest)=={'members','files','raw_bytes','archive_bytes','archive_sha256'} and json.dumps(manifest['members'],sort_keys=True,allow_nan=False)==json.dumps(expected,sort_keys=True,allow_nan=False),'complete ordered manifest differs')
    require(type(manifest['files']) is int and manifest['files']==len(selected) and type(manifest['raw_bytes']) is int and manifest['raw_bytes']==batch['raw_bytes']==sum(r['bytes'] for r in selected),'bundle payload denominator differs')
    require(type(max_archive_bytes) is int and 0<max_archive_bytes<2**63 and type(manifest['archive_bytes']) is int and 0<manifest['archive_bytes']<=max_archive_bytes,'archive bound differs')
    require(type(manifest['archive_sha256']) is str and re.fullmatch('[0-9a-f]{64}',manifest['archive_sha256']),'archive digest differs')
    archive=Path(_absolute(archive));origin=_absolute(original_root)
    require(not PurePosixPath(archive).is_relative_to(origin) and archive.resolve(strict=True)==archive,'archive source is original or redirected')
    before=archive.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==manifest['archive_bytes'],'archive type/extent differs')
    # Existing exact verifier remains the admission boundary, not reimplemented.
    verified=verify_bundle(archive,manifest)
    require(_signature(archive.lstat())==_signature(before),'archive changed during verification')
    source_fd=os.open(archive,os.O_RDONLY|os.O_NOFOLLOW);root_fd=None
    try:
        require(_signature(os.fstat(source_fd))==_signature(before),'archive changed before extraction')
        root_fd=_open_root(target_root,original_root);_identity(root_fd,root_pin)
        with os.fdopen(os.dup(source_fd),'rb') as stream,tarfile.open(fileobj=stream,mode='r|') as tar:
            count=0
            for member in tar:
                require(count<len(expected),'extra member');row=expected[count]
                require(member.type==tarfile.REGTYPE and not member.linkname and member.name==row['member'] and member.size==row['bytes'],'member changed')
                parts=_relative(row['relative_path'])
                with _walk(root_fd,parts[:-1]) as parent:
                    fd=os.open(parts[-1],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
                    try:
                        digest=hashlib.sha256();remaining=row['bytes']
                        with tar.extractfile(member) as inp:
                            while remaining:
                                chunk=inp.read(min(BLOCK,remaining));require(bool(chunk),'short member')
                                digest.update(chunk);remaining-=len(chunk);view=memoryview(chunk)
                                while view:
                                    size=os.write(fd,view);require(size>0,'short write');view=view[size:]
                            require(not inp.read(1),'extra member bytes')
                        require(digest.hexdigest()==row['expected_sha256'],'reconstructed digest differs')
                        os.fchmod(fd,stat.S_IMODE(row['mode']));now=os.fstat(fd)
                        os.utime(fd,ns=(now.st_atime_ns,row['mtime_ns']));os.fsync(fd)
                        after=os.fstat(fd)
                        require(after.st_nlink==1 and after.st_size==row['bytes'] and after.st_mode==row['mode'] and after.st_mtime_ns==row['mtime_ns'],'reconstructed metadata differs')
                        require(_signature(os.stat(parts[-1],dir_fd=parent,follow_symlinks=False))==_signature(after),'reconstructed name changed')
                        os.fsync(parent)
                    finally:os.close(fd)
                count+=1
            require(count==len(expected),'short member count')
        require(_signature(os.fstat(source_fd))==_signature(before) and _signature(archive.lstat())==_signature(before),'archive changed during reconstruction')
        _identity(root_fd,root_pin);os.fsync(root_fd)
        fresh=_open_root(target_root,original_root)
        try:_identity(fresh,root_pin)
        finally:os.close(fresh)
        return {**verified,'start':start,'stop':stop,'archive_sha256':manifest['archive_sha256'],'originals_opened':False}
    finally:
        if root_fd is not None:os.close(root_fd)
        os.close(source_fd)


def verify_new_tree(target_root,expected_rows,directories,*,original_root,root_pin,max_files,max_total_bytes,max_file_bytes,restore_directories=False):
    """Whole exact inventory/content check; optionally finalize directory metadata.

    Set restore_directories only after every batch has been reconstructed. All
    contents and namespaces are checked before directory/root metadata changes.
    """
    files,dirs,total=_layout(expected_rows,directories,original_root,max_files=max_files,max_total_bytes=max_total_bytes,max_file_bytes=max_file_bytes)
    require(type(restore_directories) is bool,'boolean restore flag required')
    fd=_open_root(target_root,original_root)
    try:
        _identity(fd,root_pin);seen_files=set();seen_dirs=set()
        pending=['.']
        while pending:
            relative=pending.pop();seen_dirs.add(relative)
            with _walk(fd,_relative(relative,directory=True)) as parent:
                with os.scandir(parent) as iterator:
                    for entry in iterator:
                        name=entry.name if relative=='.' else relative+'/'+entry.name
                        info=entry.stat(follow_symlinks=False)
                        if stat.S_ISDIR(info.st_mode):
                            require(name in dirs,'extra directory');pending.append(name)
                        else:
                            require(name in files and stat.S_ISREG(info.st_mode) and info.st_nlink==1,'extra/linked/nonregular file');row=files[name]
                            child=os.open(entry.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
                            try:
                                before=os.fstat(child);require(_signature(before)==_signature(info),'file changed before verify')
                                require(before.st_size==row['bytes'] and before.st_mode==row['mode'] and before.st_mtime_ns==row['mtime_ns'],'file metadata differs')
                                h=hashlib.sha256();remaining=row['bytes']
                                while remaining:
                                    chunk=os.read(child,min(BLOCK,remaining));require(bool(chunk),'short reconstructed file');h.update(chunk);remaining-=len(chunk)
                                require(not os.read(child,1) and h.hexdigest()==row['expected_sha256'],'file hash/extent differs')
                                require(_signature(os.fstat(child))==_signature(before) and _signature(os.stat(entry.name,dir_fd=parent,follow_symlinks=False))==_signature(before),'file changed during verify')
                            finally:os.close(child)
                            seen_files.add(name)
        require(seen_files==files.keys() and seen_dirs==dirs.keys(),'whole denominator differs')
        for name in sorted(dirs,key=lambda n:(-len(_relative(n,directory=True)),n)):
            with _walk(fd,_relative(name,directory=True)) as directory:
                row=dirs[name]
                if restore_directories:
                    os.fchmod(directory,stat.S_IMODE(row['mode']));info=os.fstat(directory)
                    os.utime(directory,ns=(info.st_atime_ns,row['mtime_ns']));os.fsync(directory)
                info=os.fstat(directory)
                require(info.st_mode==row['mode'] and info.st_mtime_ns==row['mtime_ns'],'directory metadata differs')
        _identity(fd,root_pin)
        fresh=_open_root(target_root,original_root)
        try:_identity(fresh,root_pin)
        finally:os.close(fresh)
        return {'files':len(files),'directories_including_root':len(dirs),'raw_bytes':total,'directory_metadata_restored':restore_directories,'originals_opened':False,'writer_exclusion_proved':False}
    finally:os.close(fd)
