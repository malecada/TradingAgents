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

class StorageMutationObservation(ValueError):
    """Discarded incomplete/changed census; never a successful measurement."""
    def __init__(self,reason,relative):
        path=str(relative)
        self.evidence={'reason':reason,'relative_path':path[:512],
            'path_truncated':len(path)>512,
            'path_sha256':hashlib.sha256(os.fsencode(path)).hexdigest()}
        super().__init__('storage concurrent namespace or metadata change: '+reason)


def _signature(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_nlink,
            info.st_size,info.st_blocks,info.st_mtime_ns,info.st_ctime_ns)


class StorageCleanupFailure(RuntimeError):pass


def _cleanup(action,primary=None):
    try:action()
    except BaseException as error:
        # Do not invoke add_note/str/repr on a primary while deciding precedence.
        # An uncertain close is never eligible for a namespace retry.
        fatal=lambda e:not isinstance(e,Exception) or isinstance(e,MemoryError)
        if primary is not None and fatal(primary):
            try:
                # Use the builtin exception dictionary descriptor directly: no
                # overridden getattr/setattr/property or diagnostic callback.
                state=BaseException.__dict__['__dict__'].__get__(primary)
                previous=dict.get(state,'storage_cleanup_errors',())
                if type(previous) is not tuple:previous=(previous,)
                dict.__setitem__(state,'storage_cleanup_errors',previous+(error,))
            except BaseException as attachment_error:
                # Keep the original fatal even if evidence attachment fails.
                # The attachment error's context retains the current close error;
                # the previous tuple has not been overwritten before success.
                raise primary from attachment_error
            raise primary
        if fatal(error):raise error from primary
        failure=StorageCleanupFailure('storage owned close uncertain; no scan retry')
        failure.storage_cleanup_errors=(error,)
        raise failure from primary

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
        try:return self._check(begin,history)
        except BaseException as error:
            # The body/cleanup already selected this fatal. Do not read
            # overridable cause/context/observation diagnostics first.
            if not isinstance(error,Exception) or isinstance(error,MemoryError):raise
            prior=getattr(error.__cause__ or error.__context__,'observation',{})
            _annotate(error,prior,history);raise

    def _check(self,begin,history):
        mutations=[]
        for attempt in range(3):
            if time.monotonic()-begin>self.limits['max_scan_seconds']:
                raise StorageLimit('time',{'hardlink_observations':history,'mutation_observations':mutations})
            try:
                result=self._scan(begin)
            except (HardlinkObservation,StorageMutationObservation) as error:
                row={**error.evidence,'partial_counts':{k:v for k,v in getattr(error,'observation',{}).items() if k in ('allocated_bytes','logical_file_bytes','regular_files','directories','entries')}}
                if isinstance(error,HardlinkObservation):history.append(row);error.history=list(history)
                else:mutations.append(row)
                _annotate(error,{},history)
                error.observation['mutation_observations']=list(mutations)
                if attempt==2:raise
                remaining=self.limits['max_scan_seconds']-(time.monotonic()-begin)
                if remaining<=0:raise StorageLimit('time',error.observation) from error
                # Cleanup completed before retry. All old counts are discarded.
                time.sleep(min(.005,remaining))
                continue
            except BaseException as error:
                # The body/cleanup already selected this fatal. Do not read
                # overridable cause/context/observation diagnostics first.
                if not isinstance(error,Exception) or isinstance(error,MemoryError):raise
                prior=getattr(error.__cause__ or error.__context__,'observation',{})
                _annotate(error,prior,history)
                error.observation['mutation_observations']=list(mutations)
                raise
            result['scan_attempts']=attempt+1
            result['hardlink_observations']=history
            result['mutation_observations']=mutations
            result['aggregate_entry_visit_bound']=6*self.limits['max_entries']
            elapsed=time.monotonic()-begin
            result['elapsed_seconds']=elapsed
            if elapsed>self.limits['max_scan_seconds']:raise StorageLimit('time',result)
            result['qualification']+=' At most three attempts share one time budget. Each accepted attempt includes the whole descriptor census followed, after its cleanup, by a complete literal namespace and metadata rejoin. Each pass independently obeys all registered tree limits. No file name is ignored. Continuous change after any sampled operation remains outside this metadata-only guarantee.'
            return result
        raise AssertionError('unreachable storage retry state')

    def _scan(self,begin):
        observed={'allocated_bytes':0,'logical_file_bytes':0,'regular_files':0,'directories':0,'entries':0}
        limits=self.limits;seals={};names={}
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
            info=os.fstat(fd);account(info,relative);seals[str(relative)]=_signature(info)
            entries=os.scandir(fd);iterator_primary=None;listed=[]
            try:
                for entry in entries:
                    observed['entries']+=1;enforce();listed.append(entry.name)
                    before=os.stat(entry.name,dir_fd=fd,follow_symlinks=False)
                    child_relative=relative/entry.name
                    if stat.S_ISDIR(before.st_mode):
                        if depth+1>limits['max_depth']:raise StorageLimit('depth',observed)
                        child=os.open(entry.name,flags,dir_fd=fd);primary=None
                        try:
                            opened=os.fstat(child)
                            if _signature(before)!=_signature(opened):raise StorageMutationObservation('directory changed while opening',child_relative)
                            visit(child,depth+1,child_relative)
                            current=os.stat(entry.name,dir_fd=fd,follow_symlinks=False)
                            if _signature(current)!=_signature(opened):raise StorageMutationObservation('directory changed during observation',child_relative)
                        except BaseException as error:primary=error;raise
                        finally:_close(child,primary)
                    else:
                        account(before,child_relative);seals[str(child_relative)]=_signature(before)
            except BaseException as error:iterator_primary=error;raise
            finally:_cleanup(entries.close,iterator_primary)
            if len(listed)!=len(set(listed)):raise StorageMutationObservation('duplicate enumerated name',relative)
            names[str(relative)]=tuple(sorted(listed))
            if _signature(os.fstat(fd))!=_signature(info):raise StorageMutationObservation('directory changed after enumeration cleanup',relative)
        root_fd=None;primary=None
        try:
            root_fd=os.open(self.root,flags)
            info=os.fstat(root_fd)
            if (info.st_dev,info.st_ino)!=self.identity:raise ValueError('owned storage root replaced')
            if self.root.resolve(strict=True)!=self.root:raise ValueError('owned storage root redirected')
            visit(root_fd,0,Path('.'))
            current=self.root.lstat()
            if not stat.S_ISDIR(current.st_mode) or (current.st_dev,current.st_ino)!=self.identity or self.root.resolve(strict=True)!=self.root:
                raise ValueError('owned storage root changed during observation')
            enforce()
        except FileNotFoundError as error:
            primary=StorageMutationObservation('entry disappeared before census completed','.')
            _annotate(primary,observed,[]);raise primary from error
        except BaseException as error:
            primary=error;_annotate(error,observed,[]);raise
        finally:
            if root_fd is not None:_close(root_fd,primary)
        # Every owned descriptor/scandir cleanup has completed. Rejoin the ENTIRE
        # root and each recorded directory/name/stat; missing/new names cannot be
        # accepted by skipping temporary entries. This is a finite sampled audit,
        # not a lock or proof that later writes cannot occur.
        first=dict(observed);observed={key:0 for key in observed};rejoin_entries=0
        try:
            # Finish every namespace iterator and its cleanup before the final
            # full metadata pass. A later-directory close can alter an earlier
            # file; interleaving these phases would accept stale earlier counts.
            for relative in sorted(names):
                enforce();path=self.root if relative=='.' else self.root/relative
                if path.resolve(strict=True)!=path:raise ValueError('storage rejoin path redirected')
                if _signature(path.lstat())!=seals[relative]:raise StorageMutationObservation('directory changed at namespace rejoin',relative)
                listed=[];entries=os.scandir(path);iterator_primary=None
                try:
                    for entry in entries:
                        listed.append(entry.name);rejoin_entries+=1
                        if rejoin_entries>limits['max_entries']:raise StorageLimit('entries',{**observed,'entries':rejoin_entries})
                        enforce()
                except BaseException as error:iterator_primary=error;raise
                finally:_cleanup(entries.close,iterator_primary)
                if tuple(sorted(listed))!=names[relative] or _signature(path.lstat())!=seals[relative]:
                    raise StorageMutationObservation('complete namespace rejoin differs',relative)
            for relative in sorted(seals):
                enforce();path=self.root if relative=='.' else self.root/relative
                current=path.lstat()
                if path.resolve(strict=True)!=path:raise ValueError('storage rejoin path redirected')
                if relative!='.':observed['entries']+=1
                account(current,relative)
                if _signature(current)!=seals[relative]:raise StorageMutationObservation('metadata changed at complete rejoin',relative)
            if observed!=first:raise StorageMutationObservation('complete accounting rejoin differs','.')
            enforce()
            return {**observed,'elapsed_seconds':time.monotonic()-begin,'root':str(self.root),
                'root_device':self.identity[0],'root_inode':self.identity[1],
                'qualification':'Sampled non-atomic st_blocks accounting, including directories; no hard filesystem quota, immutable-byte proof or inter-sample growth guarantee.'}
        except FileNotFoundError as error:
            failure=StorageMutationObservation('entry disappeared during complete rejoin','.')
            _annotate(failure,{key:max(first[key],observed[key]) for key in observed},[]);raise failure from error
        except BaseException as error:
            _annotate(error,{key:max(first[key],observed[key]) for key in observed},[]);raise
