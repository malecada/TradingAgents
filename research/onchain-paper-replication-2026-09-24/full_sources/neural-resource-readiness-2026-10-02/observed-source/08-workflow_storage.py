"""Bounded, descriptor-anchored storage observations for owned output trees.

Allocated bytes are st_blocks * 512, including directories. Logical file bytes
also constrain sparse files. This is sampled accounting, not a kernel filesystem
quota, an atomic snapshot, or a bound on growth between observations. A registered
runner must pair it with bounded writes, checkpoint/event reservations and the
outer free-disk guard, and retain any observed breach as terminal evidence.
"""
from __future__ import annotations
import os
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
        begin=time.monotonic()
        observed={'allocated_bytes':0,'logical_file_bytes':0,'regular_files':0,'directories':0,'entries':0}
        limits=self.limits
        def enforce():
            for key,cap,reason in (('allocated_bytes','max_allocated_bytes','allocated'),('logical_file_bytes','max_logical_bytes','logical'),('entries','max_entries','entries')):
                if observed[key]>limits[cap]:raise StorageLimit(reason,observed)
            if time.monotonic()-begin>limits['max_scan_seconds']:raise StorageLimit('time',observed)
        def account(info):
            if info.st_dev!=self.identity[0]:raise ValueError('storage entry crossed filesystem')
            if stat.S_ISREG(info.st_mode):
                if info.st_nlink!=1:raise ValueError('storage hardlink refused')
                observed['regular_files']+=1;observed['logical_file_bytes']+=info.st_size
            elif stat.S_ISDIR(info.st_mode):observed['directories']+=1
            else:raise ValueError('storage special file or symbolic link refused')
            observed['allocated_bytes']+=info.st_blocks*512
            enforce()
        flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC
        def visit(fd,depth):
            info=os.fstat(fd);account(info)
            with os.scandir(fd) as entries:
                for entry in entries:
                    observed['entries']+=1;enforce()
                    before=os.stat(entry.name,dir_fd=fd,follow_symlinks=False)
                    if stat.S_ISDIR(before.st_mode):
                        if depth+1>limits['max_depth']:raise StorageLimit('depth',observed)
                        child=os.open(entry.name,flags,dir_fd=fd)
                        try:
                            opened=os.fstat(child)
                            if (before.st_dev,before.st_ino)!=(opened.st_dev,opened.st_ino):raise ValueError('storage directory changed while opening')
                            visit(child,depth+1)
                            current=os.stat(entry.name,dir_fd=fd,follow_symlinks=False)
                            if (current.st_dev,current.st_ino)!=(opened.st_dev,opened.st_ino):raise ValueError('storage directory changed during observation')
                        finally:os.close(child)
                    else:account(before)
        root_fd=os.open(self.root,flags)
        try:
            info=os.fstat(root_fd)
            if (info.st_dev,info.st_ino)!=self.identity:raise ValueError('owned storage root replaced')
            if self.root.resolve(strict=True)!=self.root:raise ValueError('owned storage root redirected')
            visit(root_fd,0)
            current=self.root.lstat()
            if not stat.S_ISDIR(current.st_mode) or (current.st_dev,current.st_ino)!=self.identity or self.root.resolve(strict=True)!=self.root:
                raise ValueError('owned storage root changed during observation')
            enforce()
            return {**observed,'elapsed_seconds':time.monotonic()-begin,'root':str(self.root),
                'root_device':self.identity[0],'root_inode':self.identity[1],
                'qualification':'Sampled non-atomic st_blocks accounting, including directories; no hard filesystem quota or inter-sample growth guarantee.'}
        finally:os.close(root_fd)
