"""Exact pilot writable closure; historical claim siblings are read-only inputs."""
import os,stat,time
from pathlib import Path
from types import MappingProxyType
from .workflow_storage import StorageWatch,StorageLimit,FIELDS,_close
KIND='real-pilot-writable-union'
EXPERIMENT='eth-paper-real-data-end-to-end-resource-20261005-01'
COUNTS={'allocated_bytes':'max_allocated_bytes','logical_file_bytes':'max_logical_bytes','entries':'max_entries'}

def selected(budget):return type(budget) is dict and budget.get('schema_version')==2

def validate(budget,root):
    root=Path(root)
    if type(budget) is not dict or set(budget)!={'schema_version','kind','authority_root','experiment','roots','shared_files','limits'} or budget['schema_version']!=2 or budget['kind']!=KIND:raise ValueError('explicit real-pilot writable closure required')
    if not root.is_absolute() or root.resolve(strict=True)!=root or budget['authority_root']!=str(root) or budget['experiment']!=EXPERIMENT:raise ValueError('original authority/experiment differs')
    parent=root/'research_runs';target=parent/EXPERIMENT
    if budget['roots']!=[str(root/'research_artifacts'),str(target)] or budget['shared_files']!=[str(parent/'.lock')]:raise ValueError('exact writer roots and shared lock required')
    limits=budget['limits']
    if type(limits) is not dict or set(limits)!=FIELDS or any(type(x) is not int or not 0<x<2**63 for x in limits.values()) or limits['max_depth']>64 or limits['max_scan_seconds']>5:raise ValueError('finite aggregate storage limits required')
    if parent.resolve(strict=True)!=parent or not stat.S_ISDIR(parent.lstat().st_mode) or parent.stat().st_dev!=root.stat().st_dev:raise ValueError('canonical existing lifecycle parent required')
    artifact=StorageWatch(root/'research_artifacts',dict(limits))
    if artifact.identity[0]!=root.stat().st_dev:raise ValueError('writer volume differs')
    if target.exists() or target.is_symlink():
        target_watch=StorageWatch(target,dict(limits))
        if target_watch.identity[0]!=artifact.identity[0]:raise ValueError('experiment volume differs')
    return artifact

class WritableUnion:
    def __init__(self,budget,root):
        self.artifact=validate(budget,root);self.root=Path(root);self.limits=MappingProxyType(dict(budget['limits']))
        self.parent=self.root/'research_runs';s=self.parent.lstat();self.parent_identity=(s.st_dev,s.st_ino)
        self.target=self.parent/EXPERIMENT;self.lock=self.parent/'.lock';self.target_identity=None;self.lock_identity=None
        self.budget={**budget,'roots':list(budget['roots']),'shared_files':list(budget['shared_files']),'limits':dict(self.limits)}
        self.identities=[{'root':str(self.artifact.root),'device':self.artifact.identity[0],'inode':self.artifact.identity[1]}, {'root':str(self.target),'device':None,'inode':None,'state':'prospective-unobserved'}, {'shared_parent':str(self.parent),'device':s.st_dev,'inode':s.st_ino}]
        # If already born at binding, pin immediately. No invented absent inode.
        if self.target.exists() or self.target.is_symlink():self._birth()
    def _parent_check(self):
        s=self.parent.lstat()
        if not stat.S_ISDIR(s.st_mode) or self.parent.resolve(strict=True)!=self.parent or (s.st_dev,s.st_ino)!=self.parent_identity:raise ValueError('lifecycle parent replaced/redirected')
        return s
    def _birth(self):
        self._parent_check()
        try:s=self.target.lstat()
        except FileNotFoundError:
            if self.target_identity is not None:raise ValueError('experiment disappeared after birth')
            self.identities[1]={'root':str(self.target),'device':None,'inode':None,'state':'observed-absent-before-birth'}
            return None
        if not stat.S_ISDIR(s.st_mode) or self.target.resolve(strict=True)!=self.target or s.st_dev!=self.parent_identity[0]:raise ValueError('experiment birth type/volume/path differs')
        identity=(s.st_dev,s.st_ino)
        if self.target_identity is not None and identity!=self.target_identity:raise ValueError('experiment rebirth refused')
        self.target_identity=identity
        self.identities[1]={'root':str(self.target),'device':s.st_dev,'inode':s.st_ino,'state':'observed-born'}
        return s
    def check(self):
        begin=time.monotonic();total={k:0 for k in (*COUNTS,'regular_files','directories')};observations=[]
        def enforce():
            for key,limit in COUNTS.items():
                if total[key]>self.limits[limit]:raise StorageLimit('aggregate '+key,{**total,'roots':observations})
            if time.monotonic()-begin>self.limits['max_scan_seconds']:raise StorageLimit('aggregate time',{**total,'roots':observations})
        parent=self._parent_check();total['allocated_bytes']+=parent.st_blocks*512;total['directories']+=1
        # Lifecycle's existing shared lock is a separate writer, never followed.
        fd=os.open(self.lock,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        primary=None
        try:
            s=os.fstat(fd);current=self.lock.lstat();identity=(s.st_dev,s.st_ino)
            if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or identity!=(current.st_dev,current.st_ino) or identity[0]!=self.parent_identity[0] or (self.lock_identity is not None and identity!=self.lock_identity):raise ValueError('shared lock type/link/identity differs')
            self.lock_identity=identity;lock_start=s
            total['allocated_bytes']+=s.st_blocks*512;total['logical_file_bytes']+=s.st_size;total['entries']+=1;total['regular_files']+=1
            observations.append({'shared_file':str(self.lock),'device':s.st_dev,'inode':s.st_ino,'allocated_bytes':s.st_blocks*512,'logical_file_bytes':s.st_size})
            enforce()
        except BaseException as error:primary=error;raise
        finally:_close(fd,primary)
        born=self._birth();total['entries']+=int(born is not None);enforce()
        roots=[(self.artifact.root,self.artifact.identity)]
        if born is not None:roots.append((self.target,self.target_identity))
        else:observations.append({'root':str(self.target),'state':'observed-absent-before-birth','device':None,'inode':None,'counts':'no existing subtree observed; no baseline credit'})
        for path,identity in roots:
            remaining=dict(self.limits)
            for key,limit in COUNTS.items():
                remaining[limit]-=total[key]
                if remaining[limit]<=0:raise StorageLimit('aggregate '+key,{**total,'roots':observations})
            current=StorageWatch(path,remaining)
            if current.identity!=identity:raise ValueError('watched writer root replaced')
            root_begin=time.monotonic()
            try:obs=current._check(begin,[])
            except BaseException as error:
                partial=getattr(error,'observation',{})
                try:error.observation={**{k:total[k]+partial.get(k,0) for k in total},'roots':observations,'failed_root':str(path),'partial_root':partial}
                except BaseException as later:
                    if not isinstance(error,Exception) or isinstance(error,MemoryError):raise error
                    raise later from error
                raise
            obs['shared_scan_elapsed_seconds']=time.monotonic()-begin;obs['elapsed_seconds']=time.monotonic()-root_begin;observations.append(obs)
            for k in total:total[k]+=obs[k]
            enforce()
        last_parent=self._parent_check()
        total['allocated_bytes']+=max(0,(last_parent.st_blocks-parent.st_blocks)*512)
        # Birth during an absence observation is not silently credited as empty.
        after=self._birth()
        if born is None and after is not None:raise ValueError('experiment born during scan; complete new observation required')
        a=self.artifact.root.lstat()
        if (a.st_dev,a.st_ino)!=self.artifact.identity or self.artifact.root.resolve(strict=True)!=self.artifact.root:raise ValueError('artifact root changed')
        l=self.lock.lstat()
        if not stat.S_ISREG(l.st_mode) or l.st_nlink!=1 or (l.st_dev,l.st_ino)!=self.lock_identity:raise ValueError('shared lock changed during scan')
        total['allocated_bytes']+=max(0,(l.st_blocks-lock_start.st_blocks)*512)
        total['logical_file_bytes']+=max(0,l.st_size-lock_start.st_size)
        enforce()
        return {**total,'roots':observations,'root_identities':[dict(x) for x in self.identities],'shared_parent_identity':list(self.parent_identity),'authority_root':str(self.root),'elapsed_seconds':time.monotonic()-begin,'qualification':'Sampled exact writer closure including shared parent directory allocation and lock. Historical claim siblings/source/runtime outside writer scope; no kernel quota, atomic snapshot, or absent-tree allocation credit.'}

def environment(root,original):
    root=Path(root);base=root/'research_artifacts/real_pilot_runtime'
    result=dict(original)
    routes={'TMPDIR':'tmp','TMP':'tmp','TEMP':'tmp','XDG_CACHE_HOME':'cache','TORCH_HOME':'torch','MPLCONFIGDIR':'matplotlib','HF_HOME':'hf','TORCH_EXTENSIONS_DIR':'torch-extensions','TORCHINDUCTOR_CACHE_DIR':'torchinductor','TRITON_CACHE_DIR':'triton','NUMBA_CACHE_DIR':'numba','CUDA_CACHE_PATH':'cuda','XDG_CONFIG_HOME':'config','XDG_DATA_HOME':'data'}
    result.update({k:str(base/v) for k,v in routes.items()})
    return result

def prepare_environment(root,budget,env):
    validate(budget,root)
    for key,value in env.items():
        if key in ('PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):continue
        p=Path(value)
        if not p.is_relative_to(Path(root)/'research_artifacts/real_pilot_runtime'):raise ValueError('unaccounted native writer route')
        if p.resolve(strict=False)!=p:raise ValueError('native writer parent redirected')
        p.mkdir(parents=True,exist_ok=True)
        if p.resolve(strict=True)!=p:raise ValueError('native writer route redirected')
