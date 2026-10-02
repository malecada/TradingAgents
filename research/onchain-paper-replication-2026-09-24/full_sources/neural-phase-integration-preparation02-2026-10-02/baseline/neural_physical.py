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
import time

PREFIX='research_artifacts/onchain-paper-replication-2026-09-24'
FIELDS={'schema_version','max_file_bytes','max_json_bytes','max_allocated_bytes','max_logical_bytes','max_entries','tail_reserve_bytes'}


def validate(policy):
    if type(policy) is not dict or set(policy)!=FIELDS or any(type(v) is not int or v<=0 for v in policy.values()) or policy['schema_version']!=1:
        raise ValueError('physical policy schema/positive integer limits differ')
    if not policy['max_json_bytes']<=policy['max_file_bytes']<=64*1024**2:raise ValueError('physical per-file envelope differs')
    if policy['tail_reserve_bytes']<4*policy['max_json_bytes'] or policy['tail_reserve_bytes']>=min(policy['max_allocated_bytes'],policy['max_logical_bytes']):raise ValueError('physical terminal tail reserve differs')
    if not 32<=policy['max_entries']<=4096:raise ValueError('physical entry envelope differs')
    return dict(policy)


def verify_file_limit(expected,actual):
    if tuple(actual)!=(expected,expected):raise ValueError('kernel file limit readback differs')


def _encode(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def _bounded_encode(value,maximum):
    lower=0
    def visit(item,depth=0):
        nonlocal lower
        if depth>64:raise ValueError('physical JSON depth exceeded')
        if isinstance(item,str):lower+=len(item)+2
        elif type(item) in (list,tuple):
            lower+=2+len(item)
            if lower>maximum:raise ValueError('physical JSON write limit exceeded')
            for child in item:visit(child,depth+1)
        elif type(item) is dict:
            lower+=2+2*len(item)
            if lower>maximum:raise ValueError('physical JSON write limit exceeded')
            for key,child in item.items():
                if type(key) is not str:raise ValueError('physical JSON object keys must be strings')
                visit(key,depth+1);visit(child,depth+1)
        elif item is None or type(item) in (bool,int,float):
            if type(item) is int and item.bit_length()>4*maximum:raise ValueError('physical JSON integer exceeds limit')
            lower+=1
        else:raise ValueError('physical JSON value type differs')
        if lower>maximum:raise ValueError('physical JSON write limit exceeded')
    visit(value)
    pieces=[];size=1
    for chunk in json.JSONEncoder(sort_keys=True,indent=2,allow_nan=False).iterencode(value):
        data=chunk.encode();size+=len(data)
        if size>maximum:raise ValueError('physical JSON write limit exceeded')
        pieces.append(data)
    return b''.join(pieces)+b'\n'


def _read(path,maximum):
    """Nonblocking bounded regular metadata; refuse changed path/extent after read."""
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC);primary=None
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1:raise ValueError('physical control type must be single-link regular file')
        if before.st_size>maximum:raise ValueError('physical control extent exceeds limit')
        parts=[];remaining=before.st_size
        while remaining:
            piece=os.read(fd,min(remaining,65536))
            if not piece:raise ValueError('physical control extent shortened')
            parts.append(piece);remaining-=len(piece)
        if os.read(fd,1):raise ValueError('physical control extent grew')
        after=os.fstat(fd);current=path.lstat()
        key=lambda info:(info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_nlink)
        if key(before)!=key(after) or key(after)!=key(current):raise ValueError('physical control changed during read')
        return b''.join(parts)
    except BaseException as error:primary=error;raise
    finally:_close(fd,primary)


def _hash(path,maximum):return hashlib.sha256(_read(path,maximum)).hexdigest()
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
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False) and name not in ('tail',):raise AttributeError('physical original authority is immutable')
        object.__setattr__(self,name,value)

    @classmethod
    def create(cls,root,experiment,source,policy,launcher):
        from .neural_authority import ParentAuthority
        root=Path(root).resolve();policy=validate(policy)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',experiment) or not re.fullmatch('[0-9a-f]{40}',source):raise ValueError('physical job identity differs')
        roots={'control':root/PREFIX/'runs'/experiment,'lifecycle':root/'research_runs'/experiment,'producer':root/PREFIX/'sources'/experiment}
        if any(os.path.lexists(p) for k,p in roots.items() if k!='control'):raise ValueError('physical roots must be fresh')
        for path in roots.values():
            if path.resolve()!=path:raise ValueError('physical fresh root ancestor redirected')
            if not path.parent.is_dir() or path.parent.resolve()!=path.parent or _identity(path.parent)[0]!=root.stat().st_dev:raise ValueError('physical canonical existing parent scaffold required')
        base=roots['control']
        if base.resolve()!=base or _identity(base)[0]!=root.stat().st_dev:raise ValueError('physical control ancestor/device differs')
        _write(base/'physical.lock',b'')
        original={'identities':{'control':_identity(base)},'claim_sha256':None,'receipts':{}}
        anchor_hash=None
        def handle(request):
            if request.get('anchor_sha256')!=anchor_hash:raise ValueError('physical original launch authority differs')
            op=request.get('op')
            if op=='get' and set(request)=={'op','anchor_sha256'}:return original
            if op=='birth' and set(request)=={'op','role','anchor_sha256'}:
                role=request['role']
                if role not in ('lifecycle','producer') or role in original['identities']:raise ValueError('physical original birth is exclusive')
                if role=='producer' and original['claim_sha256'] is None:raise ValueError('physical producer before claim birth')
                path=roots[role]
                if path.resolve()!=path or os.path.lexists(path):raise ValueError('physical original fresh birth redirected/replaced')
                if not path.parent.is_dir() or _identity(path.parent)[0]!=root.stat().st_dev:raise ValueError('physical root parent scaffold missing/device differs')
                path.mkdir(exist_ok=False);_sync(path.parent)
                identity=_identity(path);original['identities'][role]=identity
                name='physical-birth-'+role+'.json'
                data=_bounded_encode({'role':role,'identity':identity,'anchor_sha256':anchor_hash},policy['max_json_bytes'])
                _write(base/name,data);original['receipts'][name]=hashlib.sha256(data).hexdigest()
                return original
            if op=='claim' and set(request)=={'op','value','anchor_sha256'}:
                value=request['value']
                if original['claim_sha256'] is not None or 'lifecycle' not in original['identities']:raise ValueError('physical claim birth is exclusive')
                if value.get('experiment_id')!=experiment or value.get('source')!=source:raise ValueError('physical claim owner differs')
                life=roots['lifecycle']
                if _identity(life)!=original['identities']['lifecycle'] or life.resolve()!=life:raise ValueError('physical original lifecycle root replaced')
                data=_bounded_encode(value,policy['max_json_bytes'])
                _write(life/'claim.json',data);original['claim_sha256']=hashlib.sha256(data).hexdigest()
                return original
            raise ValueError('physical authority request schema differs')
        authority=ParentAuthority(policy['max_json_bytes'],handle)
        try:
            anchor={'schema_version':1,'root':str(root),'experiment':experiment,'source':source,'policy':policy,'launcher':launcher,
                    'roots':{k:str(p) for k,p in roots.items()},'control_identity':_identity(base),
                    'lock_identity':[(base/'physical.lock').stat().st_dev,(base/'physical.lock').stat().st_ino],
                    'parent_authority':authority.identity}
            data=_bounded_encode(anchor,policy['max_json_bytes']);anchor_hash=hashlib.sha256(data).hexdigest()
            _write(base/'physical-anchor.json',data)
            self=cls.open(root,experiment,source,policy,original_anchor=anchor_hash)
            object.__setattr__(self,'_server',authority)
            (base/'scratch').mkdir()
            for name in ('tmp','cache','torch'):(base/'scratch'/name).mkdir()
            _sync(base/'scratch');_sync(base)
            self.check()
            return self
        except BaseException as primary:
            try:authority.close()
            except BaseException as error:
                primary.add_note('physical authority close: '+repr(error))
                if isinstance(primary,Exception) and not isinstance(primary,MemoryError) and (not isinstance(error,Exception) or isinstance(error,MemoryError)):raise error from primary
            raise

    @classmethod
    def open(cls,root,experiment,source,policy,*,original_anchor=None):
        root=Path(root).resolve();base=root/PREFIX/'runs'/experiment
        policy=validate(policy)
        # Bounded type/extent admission is required even if supplied authority is missing.
        raw=_read(base/'physical-anchor.json',policy['max_json_bytes'])
        if not isinstance(original_anchor,str) or hashlib.sha256(raw).hexdigest()!=original_anchor:raise ValueError('physical original anchor capability required/differs')
        anchor=json.loads(raw)
        if anchor['root']!=str(root) or anchor['experiment']!=experiment or anchor['source']!=source or anchor['policy']!=policy:raise ValueError('physical anchor contract differs')
        expected={'control':str(base),'lifecycle':str(root/'research_runs'/experiment),'producer':str(root/PREFIX/'sources'/experiment)}
        if anchor['roots']!=expected or _identity(base)!=anchor['control_identity'] or base.resolve()!=base:raise ValueError('physical original control/root mapping differs')
        self=cls();self.root=root;self.base=base;self.anchor=anchor;self.anchor_hash=original_anchor;self.policy=dict(policy);self.roots={k:Path(v) for k,v in expected.items()};self.tail=False
        self.lock_identity=anchor['lock_identity'];self._server=None;self._sealed=True
        self._original()
        return self

    def _original(self,**value):
        from .neural_authority import request
        if hashlib.sha256(_encode(self.anchor)).hexdigest()!=self.anchor_hash:raise ValueError('physical in-process original authority changed')
        return request(self.anchor['parent_authority'],self.anchor_hash,value or {'op':'get'},self.policy['max_json_bytes'])

    def environment(self):
        scratch=self.base/'scratch'
        return {'TMPDIR':str(scratch/'tmp'),'TMP':str(scratch/'tmp'),'TEMP':str(scratch/'tmp'),
                'XDG_CACHE_HOME':str(scratch/'cache'),'TORCH_HOME':str(scratch/'torch')}

    def verify_environment(self):
        import tempfile
        expected=self.environment()
        if any(os.environ.get(key)!=value for key,value in expected.items()):raise ValueError('physical configured scratch environment differs')
        for value in set(expected.values()):
            path=Path(value)
            if path.resolve()!=path or _identity(path)[0]!=self.root.stat().st_dev:raise ValueError('physical configured scratch directory differs')
        # Imports can cache tempfile's old choice before the selected route joins.
        tempfile.tempdir=None
        if tempfile.gettempdir()!=expected['TMPDIR']:raise ValueError('physical cached scratch directory differs')
        self.check()

    def read_metadata(self,path):
        path=Path(path)
        if path.resolve()!=path or not any(path.is_relative_to(p) and path!=p for p in self.roots.values()):raise ValueError('physical metadata outside original roots')
        with self._locked():
            self._scan(tail=self.tail)
            value=json.loads(_read(path,self.policy['max_json_bytes']))
            self._scan(tail=self.tail)
            return value

    def close_authority(self):
        if self._server is None:raise ValueError('physical scope does not own parent authority')
        self._server.close()

    def birth(self,role):
        if role not in ('lifecycle','producer'):raise ValueError('physical root role differs')
        with self._locked():
            self._scan(reserve=16384+self.policy['max_json_bytes'])
            self._original(op='birth',role=role)
            self._scan()
        return self.roots[role]

    @contextmanager
    def _locked(self):
        if self.policy!=self.anchor['policy'] or self.roots!={k:Path(v) for k,v in self.anchor['roots'].items()} or hashlib.sha256(_encode(self.anchor)).hexdigest()!=self.anchor_hash:
            raise ValueError('physical in-process authority changed')
        if _identity(self.base)!=self.anchor['control_identity'] or _hash(self.base/'physical-anchor.json',self.policy['max_json_bytes'])!=self.anchor_hash:raise ValueError('physical original anchor changed')
        fd=os.open(self.base/'physical.lock',os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK);primary=None
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_nlink!=1 or os.fstat(fd).st_size:raise ValueError('physical original lock type/extent differs')
            if [os.fstat(fd).st_dev,os.fstat(fd).st_ino]!=self.lock_identity:raise ValueError('physical lock replaced')
            fcntl.flock(fd,fcntl.LOCK_EX);self._original();yield;self._original()
        except BaseException as error:primary=error;raise
        finally:_close(fd,primary)

    def _state(self):return self._original()

    def _scan(self,*,tail=False,reserve=0):
        state=self._state();allocated=logical=files=entries=0
        for name,expected in state['receipts'].items():
            if _hash(self.base/name,self.policy['max_json_bytes'])!=expected:raise ValueError('physical original birth receipt changed')
        for role,path in self.roots.items():
            if not os.path.lexists(path):
                if role in state['identities']:raise ValueError('physical original root disappeared')
                continue
            if path.resolve()!=path or _identity(path)[0]!=self.root.stat().st_dev:raise ValueError('physical root redirection/device differs')
            actual=_identity(path)
            if role in state['identities'] and state['identities'][role]!=actual:raise ValueError('physical original root replaced')
            if role not in state['identities']:raise ValueError('physical original birth required; unrecorded root')
            begin=time.monotonic()
            flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC
            def account(info):
                nonlocal allocated,logical,files,entries
                entries+=1
                if time.monotonic()-begin>5:raise ValueError('physical scan time limit exceeded')
                if info.st_dev!=self.root.stat().st_dev or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):raise ValueError('physical special entry/device refused')
                allocated+=info.st_blocks*512
                if stat.S_ISREG(info.st_mode):
                    if info.st_nlink!=1:raise ValueError('physical unexpected hardlink')
                    logical+=info.st_size;files+=1
                    if info.st_size>self.policy['max_file_bytes']:raise ValueError('physical file write limit exceeded')
                if entries+(2 if reserve else 0)>self.policy['max_entries']-(0 if tail else 16):raise ValueError('physical entry budget exceeded')
            identity=lambda info:[info.st_dev,info.st_ino]
            def visit(fd,depth):
                account(os.fstat(fd))
                with os.scandir(fd) as children:
                    for entry in children:
                        before=os.stat(entry.name,dir_fd=fd,follow_symlinks=False)
                        if stat.S_ISDIR(before.st_mode):
                            if depth>=16:raise ValueError('physical depth envelope exceeded')
                            child=os.open(entry.name,flags,dir_fd=fd);primary=None
                            try:
                                opened=os.fstat(child)
                                if identity(before)!=identity(opened):raise ValueError('physical directory changed during open')
                                visit(child,depth+1)
                                if identity(os.stat(entry.name,dir_fd=fd,follow_symlinks=False))!=identity(opened):raise ValueError('physical directory changed during scan')
                            except BaseException as error:primary=error;raise
                            finally:_close(child,primary)
                        else:account(before)
            fd=os.open(path,flags);primary=None
            try:
                if identity(os.fstat(fd))!=actual:raise ValueError('physical original root replaced while opening')
                visit(fd,0)
                if _identity(path)!=actual or path.resolve()!=path:raise ValueError('physical original root changed during scan')
            except BaseException as error:primary=error;raise
            finally:_close(fd,primary)
        claim=self.roots['lifecycle']/'claim.json'
        if claim.exists():
            value=json.loads(_read(claim,self.policy['max_json_bytes']))
            if value.get('experiment_id')!=self.anchor['experiment'] or value.get('source')!=self.anchor['source']:raise ValueError('physical claim owner differs')
            identity=_hash(claim,self.policy['max_json_bytes'])
            if state['claim_sha256'] is not None and state['claim_sha256']!=identity:raise ValueError('physical original claim changed')
            if state['claim_sha256'] is None:raise ValueError('physical original claim publication required')
        elif state['claim_sha256'] is not None:raise ValueError('physical original claim disappeared')
        if 'producer' in state['identities'] and state['claim_sha256'] is None:raise ValueError('physical producer before claim birth')
        hold=0 if tail else self.policy['tail_reserve_bytes']
        if allocated+reserve>self.policy['max_allocated_bytes']-hold or logical+reserve>self.policy['max_logical_bytes']-hold:raise ValueError('physical scoped storage budget exceeded')
        if self._original()!=state:raise ValueError('physical original authority changed during scan')
        return {'allocated_bytes':allocated,'logical_bytes':logical,'files':files,'entries':entries,'roles':list(self.roots),'claim_sha256':state['claim_sha256'],
                'qualification':'sampled allocated accounting; not filesystem quota; kernel file-size and bounded metadata writes required'}

    def check(self,*,tail=False):
        with self._locked():return self._scan(tail=tail)

    def _publish(self,path,value,replace):
        path=Path(path)
        if path.resolve()!=path or not any(path.is_relative_to(p) and path!=p for p in self.roots.values()):raise ValueError('physical write outside exact roots')
        data=_bounded_encode(value,self.policy['max_json_bytes'])
        if path==self.roots['lifecycle']/'claim.json' and (value.get('experiment_id')!=self.anchor['experiment'] or value.get('source')!=self.anchor['source']):raise ValueError('physical claim owner differs')
        terminal=path.name in {'failed.json','complete.json','failure-ledger.json','observer.json','postmortem-cells.json','unsealed-journals.json','observer-death.json','child_exit.json','final.json','physical-final.json'} or (isinstance(value,dict) and (value.get('status') in ('failed','unavailable') or value.get('failure') is not None))
        tail=self.tail or terminal
        with self._locked():
            observation=self._scan(tail=tail,reserve=self.policy['max_json_bytes']+8192)
            if path.is_relative_to(self.roots['lifecycle']) and path!=self.roots['lifecycle']/'claim.json' and observation['claim_sha256'] is None:
                raise ValueError('physical lifecycle output before claim birth')
            if path==self.roots['lifecycle']/'claim.json':
                if replace:raise ValueError('physical original claim cannot be replaced')
                self._original(op='claim',value=value)
            elif replace:_write(path,data,replace=True)
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
