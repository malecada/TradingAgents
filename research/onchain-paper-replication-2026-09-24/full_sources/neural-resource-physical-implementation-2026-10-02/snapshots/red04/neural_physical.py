"""Explicit future neural physical route; old jobs never select this module.

Three owned roots, bounded JSON and synchronized immutable publication. Allocated
checks are sampled, not a filesystem quota; kernel per-file limits bound writes.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid
from itertools import chain

PREFIX='research_artifacts/onchain-paper-replication-2026-09-24'
FIELDS={'schema_version','max_file_bytes','max_json_bytes','max_allocated_bytes','max_logical_bytes','max_entries','tail_reserve_bytes'}


def validate(policy):
    if type(policy) is not dict or set(policy)!=FIELDS or any(type(v) is not int or v<=0 for v in policy.values()) or policy['schema_version']!=1:
        raise ValueError('physical policy schema/positive integer limits differ')
    if not policy['max_json_bytes']<=policy['max_file_bytes']<=64*1024**2:raise ValueError('physical per-file envelope differs')
    if policy['tail_reserve_bytes']<4*policy['max_json_bytes'] or policy['tail_reserve_bytes']>=min(policy['max_allocated_bytes'],policy['max_logical_bytes']):raise ValueError('physical terminal tail reserve differs')
    if policy['max_entries']>4096:raise ValueError('physical entry envelope differs')
    return dict(policy)


def verify_file_limit(expected,actual):
    if tuple(actual)!=(expected,expected):raise ValueError('kernel file limit readback differs')


def _encode(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def _hash(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def _identity(path):
    s=path.lstat()
    if not stat.S_ISDIR(s.st_mode):raise ValueError('physical root is not directory')
    return [s.st_dev,s.st_ino]


class PhysicalCleanupFailure(BaseException):pass


def _close(fd,primary=None):
    try:os.close(fd)
    except BaseException as error:
        if primary is not None:
            primary.add_note('physical close uncertainty: '+repr(error))
            if not isinstance(primary,Exception) or isinstance(primary,MemoryError):raise primary
        failure=PhysicalCleanupFailure('physical owned close uncertain; no descriptor retry')
        failure.add_note(repr(error));raise failure from primary


def _sync(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);primary=None
    try:os.fsync(fd)
    except BaseException as error:primary=error;raise
    finally:_close(fd,primary)


def _write(path,data,replace=False):
    """Exclusive bounded bytes; preserve failed partial file, no close retry."""
    temporary=path.with_name('.physical-'+path.name) if replace else path
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);primary=None
    try:
        view=memoryview(data)
        while view:
            count=os.write(fd,view)
            if count<=0:raise OSError('physical metadata short write')
            view=view[count:]
        os.fsync(fd)
    except BaseException as error:primary=error;raise
    finally:_close(fd,primary)
    if replace:os.replace(temporary,path)
    _sync(path.parent)


class Scope:
    @classmethod
    def create(cls,root,experiment,source,policy,launcher):
        root=Path(root).resolve();policy=validate(policy)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',experiment) or not re.fullmatch('[0-9a-f]{40}',source):raise ValueError('physical job identity differs')
        roots={'control':root/PREFIX/'runs'/experiment,'lifecycle':root/'research_runs'/experiment,'producer':root/PREFIX/'sources'/experiment}
        if any(p.exists() or p.is_symlink() for k,p in roots.items() if k!='control'):raise ValueError('physical roots must be fresh')
        base=roots['control']
        if base.resolve()!=base or _identity(base)[0]!=root.stat().st_dev:raise ValueError('physical control ancestor/device differs')
        anchor={'schema_version':1,'root':str(root),'experiment':experiment,'source':source,'policy':policy,'launcher':launcher,
                'roots':{k:str(p) for k,p in roots.items()},'control_identity':_identity(base)}
        data=_encode(anchor)
        if len(data)>policy['max_json_bytes']:raise ValueError('physical anchor JSON exceeds limit')
        _write(base/'physical-anchor.json',data)
        _write(base/'physical.lock',b'')
        _write(base/'physical-state.json',_encode({'identities':{'control':anchor['control_identity']},'claim_sha256':None}))
        return cls.open(root,experiment,source,policy)

    @classmethod
    def open(cls,root,experiment,source,policy):
        root=Path(root).resolve();base=root/PREFIX/'runs'/experiment
        raw=(base/'physical-anchor.json').read_bytes();anchor=json.loads(raw)
        if anchor['root']!=str(root) or anchor['experiment']!=experiment or anchor['source']!=source or anchor['policy']!=validate(policy):raise ValueError('physical anchor contract differs')
        expected={'control':str(base),'lifecycle':str(root/'research_runs'/experiment),'producer':str(root/PREFIX/'sources'/experiment)}
        if anchor['roots']!=expected or _identity(base)!=anchor['control_identity'] or base.resolve()!=base:raise ValueError('physical original control/root mapping differs')
        self=cls();self.root=root;self.base=base;self.anchor=anchor;self.anchor_hash=hashlib.sha256(raw).hexdigest();self.policy=dict(policy);self.roots={k:Path(v) for k,v in expected.items()};self.tail=False
        self.lock_identity=(base/'physical.lock').stat().st_ino
        return self

    @contextmanager
    def _locked(self):
        if _identity(self.base)!=self.anchor['control_identity'] or _hash(self.base/'physical-anchor.json')!=self.anchor_hash:raise ValueError('physical original anchor changed')
        fd=os.open(self.base/'physical.lock',os.O_RDWR|os.O_NOFOLLOW);primary=None
        try:
            if os.fstat(fd).st_ino!=self.lock_identity:raise ValueError('physical lock replaced')
            fcntl.flock(fd,fcntl.LOCK_EX);yield
        except BaseException as error:primary=error;raise
        finally:_close(fd,primary)

    def _state(self):return json.loads((self.base/'physical-state.json').read_bytes())

    def _scan(self,*,tail=False,reserve=0):
        state=self._state();changed=False;allocated=logical=files=entries=0
        for role,path in self.roots.items():
            if not path.exists():
                if role in state['identities']:raise ValueError('physical original root disappeared')
                continue
            if path.resolve()!=path or _identity(path)[0]!=self.root.stat().st_dev:raise ValueError('physical root redirection/device differs')
            actual=_identity(path)
            if role in state['identities'] and state['identities'][role]!=actual:raise ValueError('physical original root replaced')
            if role not in state['identities']:state['identities'][role]=actual;changed=True
            paths=chain((path,),path.rglob('*'))
            for member in paths:
                if len(member.relative_to(path).parts)>16:raise ValueError('physical depth envelope exceeded')
                info=member.lstat();entries+=1
                if info.st_dev!=self.root.stat().st_dev or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):raise ValueError('physical special entry/device refused')
                allocated+=info.st_blocks*512
                if stat.S_ISREG(info.st_mode):
                    if info.st_nlink!=1:raise ValueError('physical unexpected hardlink')
                    logical+=info.st_size;files+=1
                    if info.st_size>self.policy['max_file_bytes']:raise ValueError('physical file write limit exceeded')
                if entries>self.policy['max_entries']:raise ValueError('physical entry budget exceeded')
        claim=self.roots['lifecycle']/'claim.json'
        if claim.exists():
            value=json.loads(claim.read_bytes())
            if value.get('experiment_id')!=self.anchor['experiment'] or value.get('source')!=self.anchor['source']:raise ValueError('physical claim owner differs')
            identity=_hash(claim)
            if state['claim_sha256'] is not None and state['claim_sha256']!=identity:raise ValueError('physical original claim changed')
            if state['claim_sha256'] is None:state['claim_sha256']=identity;changed=True
        if 'producer' in state['identities'] and state['claim_sha256'] is None:raise ValueError('physical producer before claim birth')
        hold=0 if tail else self.policy['tail_reserve_bytes']
        if allocated+reserve>self.policy['max_allocated_bytes']-hold or logical+reserve>self.policy['max_logical_bytes']-hold:raise ValueError('physical scoped storage budget exceeded')
        if changed:_write(self.base/'physical-state.json',_encode(state),replace=True)
        return {'allocated_bytes':allocated,'logical_bytes':logical,'files':files,'entries':entries,'roles':list(self.roots),'claim_sha256':state['claim_sha256'],
                'qualification':'sampled allocated accounting; not filesystem quota; kernel file-size and bounded metadata writes required'}

    def check(self,*,tail=False):
        with self._locked():return self._scan(tail=tail)

    def _publish(self,path,value,replace):
        path=Path(path)
        if path.resolve()!=path or not any(path.is_relative_to(p) and path!=p for p in self.roots.values()):raise ValueError('physical write outside exact roots')
        data=_encode(value)
        if len(data)>self.policy['max_json_bytes']:raise ValueError('physical JSON write limit exceeded')
        if path==self.roots['lifecycle']/'claim.json' and (value.get('experiment_id')!=self.anchor['experiment'] or value.get('source')!=self.anchor['source']):raise ValueError('physical claim owner differs')
        terminal=path.name in {'failed.json','complete.json','failure-ledger.json','observer.json','postmortem-cells.json','unsealed-journals.json','observer-death.json','child_exit.json','final.json','physical-final.json'} or (isinstance(value,dict) and (value.get('status') in ('failed','unavailable') or value.get('failure') is not None))
        tail=self.tail or terminal
        with self._locked():
            self._scan(tail=tail,reserve=self.policy['max_json_bytes']+8192)
            if replace:_write(path,data,replace=True)
            else:
                temporary=path.parent/('.physical-pending-'+uuid.uuid4().hex)
                _write(temporary,data)
                os.link(temporary,path)
                _sync(path.parent)
                try:temporary.unlink()
                except BaseException as error:raise PhysicalCleanupFailure('physical immutable temporary cleanup uncertain') from error
                _sync(path.parent)
            self._scan(tail=tail)

    def immutable(self,path,value):self._publish(path,value,False)
    def atomic(self,path,value):self._publish(path,value,True)

    @contextmanager
    def terminal_tail(self):
        previous=self.tail;self.tail=True
        try:yield self
        finally:self.tail=previous

    def finish(self):
        with self.terminal_tail():
            before=self.check(tail=True)
            # Snapshot plus explicit own-receipt reservation; return actual post-write accounting.
            self.immutable(self.base/'physical-final.json',{'status':'accounted','snapshot_before_receipt':before,
                'self_receipt_reserved_bytes':self.policy['max_json_bytes']+8192,'scope':'three roots after observer/lifecycle tail; final receipt checked after write'})
            result=self.check(tail=True)
        return {**result,'terminal_tail_included':True}
