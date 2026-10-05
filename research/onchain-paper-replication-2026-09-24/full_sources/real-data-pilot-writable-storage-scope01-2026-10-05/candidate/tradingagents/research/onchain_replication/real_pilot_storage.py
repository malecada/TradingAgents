"""Explicit real-pilot writable union; unchanged strict scans, no exclusions."""
import os,time
from pathlib import Path
from types import MappingProxyType
from .workflow_storage import StorageWatch,StorageLimit,FIELDS
KIND='real-pilot-writable-union'
EXPERIMENT='eth-paper-real-data-end-to-end-resource-20261005-01'
COUNTS={'allocated_bytes':'max_allocated_bytes','logical_file_bytes':'max_logical_bytes','entries':'max_entries'}

def selected(budget):return type(budget) is dict and budget.get('schema_version')==2

def validate(budget,root):
    root=Path(root)
    if type(budget) is not dict or set(budget)!={'schema_version','kind','authority_root','roots','limits'} or budget['schema_version']!=2 or budget['kind']!=KIND:raise ValueError('explicit real-pilot writable union required')
    if not root.is_absolute() or root.resolve(strict=True)!=root or budget['authority_root']!=str(root):raise ValueError('original authority root differs')
    expected=[str(root/'research_artifacts'),str(root/'research_runs')]
    if budget['roots']!=expected:raise ValueError('exact disjoint writable roots required')
    limits=budget['limits']
    if type(limits) is not dict or set(limits)!=FIELDS or any(type(x) is not int or not 0<x<2**63 for x in limits.values()) or limits['max_depth']>64 or limits['max_scan_seconds']>5:raise ValueError('finite aggregate storage limits required')
    watches=[StorageWatch(p,dict(limits)) for p in expected]
    if len({w.identity for w in watches})!=2 or any(w.identity[0]!=root.stat().st_dev for w in watches):raise ValueError('writable roots must be distinct on authority volume')
    return watches

class WritableUnion:
    def __init__(self,budget,root):
        self.watches=validate(budget,root);self.root=Path(root);self.limits=MappingProxyType(dict(budget['limits']))
        self.budget={'schema_version':2,'kind':KIND,'authority_root':str(self.root),'roots':[str(w.root) for w in self.watches],'limits':dict(self.limits)}
        self.identities=[{'root':str(w.root),'device':w.identity[0],'inode':w.identity[1]} for w in self.watches]
    def check(self):
        begin=time.monotonic();total={k:0 for k in (*COUNTS,'regular_files','directories')};observations=[]
        for original in self.watches:
            remaining=dict(self.limits)
            for key,limit in COUNTS.items():
                remaining[limit]-=total[key]
                if remaining[limit]<=0:raise StorageLimit('aggregate '+key,{**total,'roots':observations})
            current=StorageWatch(original.root,remaining)
            if current.identity!=original.identity:raise ValueError('watched root replaced')
            root_begin=time.monotonic()
            try:obs=current._check(begin,[])
            except BaseException as error:
                partial=getattr(error,'observation',{})
                try:error.observation={**{k:total[k]+partial.get(k,0) for k in total},'roots':observations,'failed_root':str(original.root),'partial_root':partial}
                except BaseException as later:
                    if not isinstance(error,Exception) or isinstance(error,MemoryError):raise error
                    raise later from error
                raise
            obs['shared_scan_elapsed_seconds']=time.monotonic()-begin
            obs['elapsed_seconds']=time.monotonic()-root_begin
            observations.append(obs)
            for k in total:total[k]+=obs[k]
            if time.monotonic()-begin>self.limits['max_scan_seconds']:raise StorageLimit('aggregate time',{**total,'roots':observations})
        for watched in self.watches:
            now=watched.root.lstat()
            if watched.root.resolve(strict=True)!=watched.root or (now.st_dev,now.st_ino)!=watched.identity:raise ValueError('watched root changed during aggregate observation')
        if time.monotonic()-begin>self.limits['max_scan_seconds']:raise StorageLimit('aggregate time',{**total,'roots':observations})
        return {**total,'roots':observations,'root_identities':self.identities,'authority_root':str(self.root),'elapsed_seconds':time.monotonic()-begin,'qualification':'Sampled disjoint writable union only; common authority root and read-only source/runtime are not censused. Shared finite counters/time, strict per-root scans, no kernel quota or inter-sample bound.'}

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
