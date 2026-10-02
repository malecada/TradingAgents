"""Bounded diagnostic markers; no numerical values, retry or resource authority."""
import hashlib
import math
import os
from pathlib import Path
import re
import time
from ..lifecycle import current_metadata_scope
from .neural_physical import _bounded_encode

MAX_BYTES=65536
PHASES=('graph_validation','graph_load','model','tensor_adapter','forward','loss','backward','optimizer','checkpoint','reload')
EVENTS=tuple(phase+'_'+position for phase in PHASES for position in ('before','after'))
WEEKS=('2022-01-03','2022-06-13','2022-07-25','2022-11-07','2023-06-05','2024-01-01','2024-03-11','2024-08-05','2024-12-23')
IDENTITY_KEYS={'plan_sha256','claim_sha256','source_commit','model_config_sha256','cell_id','graph_manifest_sha256'}


def _read(path,maximum):
    # Kernel metadata only. Never array/model files and never an unbounded read.
    with path.open('rb') as stream:data=stream.read(maximum+1)
    if len(data)>maximum:raise ValueError('phase metadata read bound exceeded')
    return data.decode('ascii')


def _sample(cgroup):
    value={'memory_current_bytes':None,'anon_bytes':None,'file_bytes':None,
           'pressure':None,'unavailable':[],
           'qualification':'instantaneous unit metadata, not peak or phase attribution; unknown is not zero'}
    def integer(text):
        result=int(text)
        if not 0<=result<2**63:raise ValueError('metadata integer outside finite range')
        return result
    try:value['memory_current_bytes']=integer(_read(cgroup/'memory.current',64).strip())
    except (OSError,ValueError,UnicodeError):value['unavailable'].append('memory_current')
    try:
        stats=dict(line.split() for line in _read(cgroup/'memory.stat',16384).splitlines())
        anon,file=integer(stats['anon']),integer(stats['file'])
        value['anon_bytes'],value['file_bytes']=anon,file
    except (OSError,ValueError,UnicodeError,KeyError):value['unavailable'].append('memory_stat')
    try:value['pressure']=_read(cgroup/'memory.pressure',512).strip()
    except (OSError,ValueError,UnicodeError):value['unavailable'].append('pressure')
    return value


class PhaseJournal:
    """Original physical scope owns every durable replacement and its scratch file."""
    def __init__(self,scope,directory,identity,cgroup):
        if scope is None or current_metadata_scope() is not scope:raise ValueError('original phase metadata authority required')
        if type(identity) is not dict or set(identity)!=IDENTITY_KEYS:raise ValueError('phase identity schema differs')
        for key in IDENTITY_KEYS-{'cell_id'}:
            width=40 if key=='source_commit' else 64
            if type(identity[key]) is not str or re.fullmatch('[0-9a-f]{'+str(width)+'}',identity[key]) is None:raise ValueError('phase identity hash differs')
        cells=tuple('neural_checkpoint-'+week for week in WEEKS)
        if identity['cell_id'] not in cells:raise ValueError('phase cell outside fixed population')
        directory=Path(directory);expected=scope.roots['producer']/f'cell-{cells.index(identity["cell_id"]):02d}'
        if directory!=expected or directory.resolve()!=directory or not directory.is_dir():raise ValueError('phase original cell directory differs')
        if identity['source_commit']!=scope.anchor['source']:raise ValueError('phase source differs from original authority')
        self._scope=scope;self._directory=directory;self._inode=self._directory_identity()
        self._path=directory/'phase-journal.json';self._identity=dict(identity)
        self._anchor=scope.anchor_hash;self._events=[];self._last=None;self._poisoned=False
        self._cgroup=Path(cgroup)
        if not self._cgroup.is_absolute() or not self._cgroup.is_relative_to('/sys/fs/cgroup') or '..' in self._cgroup.parts or len(str(self._cgroup))>4096:raise ValueError('phase cgroup path differs')
        self._maximum=min(MAX_BYTES,scope.policy['max_json_bytes']);self._begin=time.monotonic()
        if os.path.lexists(self._path) or os.path.lexists(directory/'.physical-phase-journal.json'):raise FileExistsError('phase journal identity already used; no retry')
        self._check()

    def _directory_identity(self):
        info=self._directory.stat();return info.st_dev,info.st_ino

    def _check(self):
        if current_metadata_scope() is not self._scope or self._scope.anchor_hash!=self._anchor:raise ValueError('phase original authority changed')
        if self._directory.resolve()!=self._directory or self._directory_identity()!=self._inode:raise ValueError('phase cell directory replaced')
        observed=self._scope.check()
        if observed['claim_sha256']!=self._identity['claim_sha256']:raise ValueError('phase original claim differs')

    def record(self,event):
        if self._poisoned:raise ValueError('phase journal stopped; no retry')
        self._poisoned=True
        if len(self._events)>=len(EVENTS) or event!=EVENTS[len(self._events)]:raise ValueError('phase event out of order or duplicate')
        self._check()
        if self._last is None:
            if os.path.lexists(self._path):raise FileExistsError('phase journal already exists')
        elif hashlib.sha256(_bounded_encode(self._scope.read_metadata(self._path),self._maximum)).hexdigest()!=self._last:
            raise ValueError('phase previous receipt changed')
        elapsed=time.monotonic()-self._begin
        if not math.isfinite(elapsed) or not 0<=elapsed<=7*86400:raise ValueError('phase elapsed outside finite bound')
        events=[*self._events,{'event':event,'elapsed_seconds':elapsed,'observation':_sample(self._cgroup)}]
        value={'schema_version':1,'identity':self._identity,'physical_anchor_sha256':self._anchor,
               'events':events,'qualification':'before marks intent; after marks returned stage; no cell outcome or retry authority'}
        encoded=_bounded_encode(value,self._maximum)
        self._scope.atomic(self._path,value)
        self._check()
        self._events=events;self._last=hashlib.sha256(encoded).hexdigest();self._poisoned=False
