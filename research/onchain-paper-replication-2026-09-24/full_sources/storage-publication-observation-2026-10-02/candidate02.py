"""Bounded, descriptor-anchored storage observations for owned output trees.

Allocated bytes are st_blocks * 512, including directories. Logical file bytes
also constrain sparse files. This is sampled accounting, not a kernel filesystem
quota, an atomic snapshot, or a bound on growth between observations. A registered
runner must pair it with bounded writes, checkpoint/event reservations and the
outer free-disk guard, and retain any observed breach as terminal evidence.
"""
from __future__ import annotations
import os
import hashlib
import json
from pathlib import Path
import stat
import time
from types import MappingProxyType

FIELDS={'max_allocated_bytes','max_logical_bytes','max_entries','max_depth','max_scan_seconds'}

class StorageLimit(ValueError):
    def __init__(self,reason,observation):
        super().__init__('storage '+reason+' limit exceeded')
        self.observation=dict(observation)
        self.reason=reason

class HardlinkObservation(ValueError):
    """An incomplete scan saw a link; it is never an accepted observation."""
    def __init__(self,relative,info):
        path=str(relative)
        self.evidence={'relative_path':path[:512],'path_truncated':len(path)>512,
            'path_sha256':hashlib.sha256(os.fsencode(path)).hexdigest(),
            'device':info.st_dev,'inode':info.st_ino,'links':info.st_nlink}
        self.history=[]
        super().__init__('storage hardlink refused: '+json.dumps(self.evidence,sort_keys=True))

class StorageCleanupFailure(BaseException):pass


def _cleanup(action,primary=None):
    try:action()
    except BaseException as error:
        if primary is not None:
            primary.add_note('storage descriptor close uncertainty: '+repr(error))
            if not isinstance(primary,Exception) or isinstance(primary,MemoryError):raise primary
        if not isinstance(error,Exception) or isinstance(error,MemoryError):raise error
        failure=StorageCleanupFailure('storage owned close uncertain; no scan retry')
        failure.add_note(repr(error));raise failure from primary

def _close(fd,primary=None):return _cleanup(lambda:os.close(fd),primary)


def _annotate(error,observed,history):
    try:
        old=getattr(error,'observation',observed)
        error.observation={**dict(old),'hardlink_observations':list(history)}
    except BaseException as secondary:
        if not isinstance(error,Exception) or isinstance(error,MemoryError):raise error
        if not isinstance(secondary,Exception) or isinstance(secondary,MemoryError):raise secondary from error
        error.add_note('storage diagnostic attachment unavailable: '+repr(secondary))

class StorageWatch:
    def __init__(self,root,limits):
        if type(limits) is not dict or set(limits)!=FIELDS or any(type(n) is not int or n<=0 for n in limits.values()):
            raise ValueError('positive integer storage limits required')
        if limits['max_depth']>64 or limits['max_scan_seconds']>5:
            raise ValueError('storage traversal depth/time limits too large')
        self.limits=MappingProxyType(dict(limits));self.root=Path(root)
        if not self.root.is_absolute() or self.root.resolve(strict=True)!=self.root:
            raise ValueError('canonical owned storage root required')
        info=self.root.lstat()
        if not stat.S_ISDIR(info.st_mode):raise ValueError('storage root must be a directory')
        self.identity=(info.st_dev,info.st_ino)

    def check(self):
        begin=time.monotonic();history=[]
        for attempt in range(3):
            if time.monotonic()-begin>self.limits['max_scan_seconds']:
                raise StorageLimit('time',{'hardlink_observations':history})
            try:
                result=self._scan(begin)
            except HardlinkObservation as error:
                history.append(error.evidence);error.history=list(history)
                _annotate(error,{},history)
                if attempt==2:raise
                remaining=self.limits['max_scan_seconds']-(time.monotonic()-begin)
                if remaining<=0:raise StorageLimit('time',error.observation) from error
                # Close completed before retry; no interrupted scan is accepted.
                time.sleep(min(.005,remaining))
                continue
            except BaseException as error:
                prior=getattr(error.__cause__,'observation',{})
                _annotate(error,prior,history);raise
            result['scan_attempts']=attempt+1
            result['hardlink_observations']=history
            result['aggregate_entry_visit_bound']=3*self.limits['max_entries']
            elapsed=time.monotonic()-begin  # Includes final descriptor cleanup.
            result['elapsed_seconds']=elapsed
            if elapsed>self.limits['max_scan_seconds']:raise StorageLimit('time',result)
            result['qualification']+=' At most three fresh complete scans share one time budget; only singly linked regular files occur in an accepted scan. Transient links may occur between/during discarded observations.'
            return result
        raise AssertionError('unreachable storage retry state')

    def _scan(self,begin):
        observed={'allocated_bytes':0,'logical_file_bytes':0,'regular_files':0,'directories':0,'entries':0}
        limits=self.limits
        def enforce():
            for key,cap,reason in (('allocated_bytes','max_allocated_bytes','allocated'),('logical_file_bytes','max_logical_bytes','logical'),('entries','max_entries','entries')):
                if observed[key]>limits[cap]:raise StorageLimit(reason,observed)
            if time.monotonic()-begin>limits['max_scan_seconds']:raise StorageLimit('time',observed)
        def account(info,relative):
            if info.st_dev!=self.identity[0]:raise ValueError('storage entry crossed filesystem')
            if stat.S_ISREG(info.st_mode):
                if info.st_nlink!=1:raise HardlinkObservation(relative,info)
                observed['regular_files']+=1;observed['logical_file_bytes']+=info.st_size
            elif stat.S_ISDIR(info.st_mode):observed['directories']+=1
            else:raise ValueError('storage special file or symbolic link refused')
            observed['allocated_bytes']+=info.st_blocks*512
            enforce()
        flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC
        def visit(fd,depth,relative):
            info=os.fstat(fd);account(info,relative)
            entries=os.scandir(fd);iterator_primary=None
            try:
                for entry in entries:
                    observed['entries']+=1;enforce()
                    before=os.stat(entry.name,dir_fd=fd,follow_symlinks=False)
                    if stat.S_ISDIR(before.st_mode):
                        if depth+1>limits['max_depth']:raise StorageLimit('depth',observed)
                        child=os.open(entry.name,flags,dir_fd=fd)
                        primary=None
                        try:
                            opened=os.fstat(child)
                            if (before.st_dev,before.st_ino)!=(opened.st_dev,opened.st_ino):raise ValueError('storage directory changed while opening')
                            visit(child,depth+1,relative/entry.name)
                            current=os.stat(entry.name,dir_fd=fd,follow_symlinks=False)
                            if (current.st_dev,current.st_ino)!=(opened.st_dev,opened.st_ino):raise ValueError('storage directory changed during observation')
                        except BaseException as error:primary=error;raise
                        finally:_close(child,primary)
                    else:account(before,relative/entry.name)
            except BaseException as error:iterator_primary=error;raise
            finally:_cleanup(entries.close,iterator_primary)
        root_fd=os.open(self.root,flags);primary=None
        try:
            info=os.fstat(root_fd)
            if (info.st_dev,info.st_ino)!=self.identity:raise ValueError('owned storage root replaced')
            if self.root.resolve(strict=True)!=self.root:raise ValueError('owned storage root redirected')
            visit(root_fd,0,Path('.'))
            current=self.root.lstat()
            if not stat.S_ISDIR(current.st_mode) or (current.st_dev,current.st_ino)!=self.identity or self.root.resolve(strict=True)!=self.root:
                raise ValueError('owned storage root changed during observation')
            enforce()
            return {**observed,'elapsed_seconds':time.monotonic()-begin,'root':str(self.root),
                'root_device':self.identity[0],'root_inode':self.identity[1],
                'qualification':'Sampled non-atomic st_blocks accounting, including directories; no hard filesystem quota or inter-sample growth guarantee.'}
        except BaseException as error:
            primary=error;_annotate(error,observed,[]);raise
        finally:_close(root_fd,primary)
