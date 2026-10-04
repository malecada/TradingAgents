"""Opaque engineering spool. No research, production, transport or deletion authority.

All local slots are allocated before payload writes. Retained slots never recycle.
A recovered page is evidence of callback byte equality ONLY, never remote origin.
"""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import owned_io as io

FILE = 4 * 1024**2
FLOOR = 10 * 1024**3
NON_TAIL = 9239969792
META = 4096


def require(ok, why):
    if not ok:
        raise ValueError(why)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


@dataclasses.dataclass(frozen=True)
class Member:
    page: int
    chunk: int
    size: int
    sha256: str


@dataclasses.dataclass(frozen=True)
class Ack:
    plan: str
    page: int
    chunk: int
    size: int
    sha256: str
    receipt_sha256: str


@dataclasses.dataclass(frozen=True)
class Recovery:
    ack: Ack
    body: bytes
    # These are exact complete opaque member bytes, NOT typed research recovery.


def sha(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def valid_ack(value):
    return (type(value) is Ack and sha(value.plan) and sha(value.sha256)
            and sha(value.receipt_sha256)
            and type(value.page) is int and value.page >= 0
            and type(value.chunk) is int and value.chunk >= 0
            and type(value.size) is int and 0 < value.size <= FILE)


@dataclasses.dataclass(frozen=True)
class Plan:
    members: tuple
    window: int
    logical_reservation: int
    allocated_reservation: int
    allocation_quantum: int = 4096

    def encoded(self):
        return canonical(dataclasses.asdict(self))

    def validate(self):
        require(type(self.members) is tuple and 0 < len(self.members) <= 4096, 'finite immutable member tuple')
        require(type(self.window) is int and 0 < self.window <= min(32, len(self.members)), 'bounded retained window')
        require(type(self.allocation_quantum) is int and self.allocation_quantum >= 4096 and self.allocation_quantum <= FILE and self.allocation_quantum & (self.allocation_quantum-1) == 0, 'explicit allocation quantum')
        for i,m in enumerate(self.members):
            require(type(m) is Member and type(m.page) is int and type(m.chunk) is int and (m.page,m.chunk)==(i//self.window,i%self.window), 'finite sorted contiguous page/chunk identity')
            require(type(m.size) is int and 0 < m.size <= FILE and sha(m.sha256), 'bounded exact member')
        logical,allocated = self.required()
        require(type(self.logical_reservation) is int and self.logical_reservation >= logical, 'whole logical reservation exhausted')
        require(type(self.allocated_reservation) is int and self.allocated_reservation >= allocated, 'whole allocated reservation exhausted')
        require(sum(m.size for m in self.members) <= NON_TAIL, 'non-tail denominator bound')

    def required(self):
        # All future body bytes, five fixed event slots/member, four terminal/plan
        # slots, two directory allowances plus one directory-entry allowance/file.
        n=len(self.members);q=self.allocation_quantum
        roundq=lambda x: ((x+q-1)//q)*q
        logical=sum(m.size for m in self.members)+(5*n+4)*META
        allocated=sum(roundq(m.size) for m in self.members)+(5*n+4)*roundq(META)+(6*n+6)*q
        return logical,allocated


def production(*args, **kwargs):
    raise RuntimeError('production closed: genuine Target/Owner/Binding/Produced ancestry, whole storage reservation, finite real transport, typed complete recovery and native release adapters unimplemented')


class Spool:
    """Single-process engineering state machine; hostile same-process code excluded.

    Callbacks must be finite. Deadline checks cannot interrupt a hung callback;
    genuine bounded subprocess transport is an unimplemented production adapter.
    No adapter is treated as an authority or a remote-capacity/wire measurement.
    """
    def __init__(self, root, plan, seconds=30):
        require(type(plan) is Plan, 'exact immutable plan')
        plan.validate()
        require(type(seconds) in (int,float) and 0 < seconds <= 120, 'finite deadline')
        root=Path(root)
        require(root.is_absolute() and root.resolve()==root, 'canonical existing private root')
        self.failed=True;self.closed=False;self._fds={};self._pins={};self._sealed={}
        self._plan=plan;self._plan_pin=plan.encoded();self.identity=digest(self._plan_pin)
        self._events=();self._states=tuple('ABSENT' for _ in plan.members);self._next=0;self.calls=0
        self.deadline=time.monotonic()+seconds
        self.root=root;self.fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            st=os.fstat(self.fd);self._root=(st.st_dev,st.st_ino)
            self._path_pin=self._path_identity()
            require(self._path_pin[-1]==self._root, 'root descriptor/path mismatch')
            require(stat.S_IMODE(st.st_mode)==0o700 and not os.listdir(self.fd), 'fresh empty private root')
            self._floor(plan.required()[1])
            # Counter is consumed in full BEFORE allocation/write; never refunded.
            self.consumed=plan.required()
            self._allocate('plan',META)
            self._allocate('terminal',META)
            for i,m in enumerate(plan.members[:plan.window]):
                self._allocate('body-%04d'%i,m.size)
                for phase in ('pending','ack','recovered','eligible','failure'):
                    self._allocate('%s-%04d'%(phase,i),META)
            self._write('plan', canonical({'plan_sha256':self.identity,'members':len(plan.members),'consumed':self.consumed,'engineering_only':True}))
            self.failed=False
            self.check()
        except BaseException:
            self.close()
            raise

    def _path_identity(self):
        # Walk every component through held no-follow descriptors. A lexical
        # parent symlink cannot reuse the original root inode as authority.
        parts=self.root.parts
        require(parts[0]=='/' and len(parts)<=128, 'bounded absolute root chain')
        fds=[];identities=[]
        try:
            fds.append(os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC))
            for part in parts[1:]:
                require(part not in ('','.','..'), 'literal directory component')
                fds.append(os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fds[-1]))
            for fd in fds:
                st=os.fstat(fd);identities.append((st.st_dev,st.st_ino))
            return tuple(identities)
        finally:
            io._cleanup(tuple(lambda fd=fd:os.close(fd) for fd in reversed(fds)))

    def _floor(self, additional=0):
        v=os.fstatvfs(self.fd)
        require(v.f_bavail*v.f_frsize >= FLOOR+additional, 'observed 10GiB floor including reservation')
        require(self._plan.allocation_quantum >= v.f_frsize, 'allocation quantum below filesystem fragment')

    def _allocate(self,name,size):
        fd=os.open(name,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=self.fd)
        self._fds[name]=fd
        os.posix_fallocate(fd,0,size)
        os.fsync(fd)
        s=os.fstat(fd)
        require(s.st_size==size and s.st_blocks*512>=size and s.st_blocks*512<=((size+self._plan.allocation_quantum-1)//self._plan.allocation_quantum)*self._plan.allocation_quantum, 'physical allocation outside conservative bound')
        self._pins[name]=(s.st_dev,s.st_ino,size,s.st_blocks)
        os.fsync(self.fd)

    def _write(self,name,raw):
        require(type(raw) is bytes and name not in self._sealed, 'immutable write once')
        size=self._pins[name][2];require(len(raw)<=size, 'slot bound')
        padded=raw+b'\0'*(size-len(raw));fd=self._fds[name]
        offset=0
        while offset<len(padded):
            n=os.pwrite(fd,padded[offset:],offset);require(n>0,'short write');offset+=n
        os.fsync(fd);self._sealed[name]=digest(padded)

    def check(self):
        require(not self.failed and not self.closed, 'terminal failed/closed spool')
        require(time.monotonic()<self.deadline and self._plan.encoded()==self._plan_pin, 'deadline/plan mutation')
        require(self._path_identity()==self._path_pin, 'canonical root ancestor chain changed')
        s=os.stat(self.root,follow_symlinks=False)
        require((s.st_dev,s.st_ino)==self._root and stat.S_IMODE(s.st_mode)==0o700, 'root changed')
        require(set(os.listdir(self.fd))==set(self._fds), 'complete local membership changed')
        for name,fd in self._fds.items():
            s=os.fstat(fd);p=os.stat(name,dir_fd=self.fd,follow_symlinks=False)
            require((s.st_dev,s.st_ino,s.st_size,s.st_blocks)==self._pins[name] and (p.st_dev,p.st_ino)==(s.st_dev,s.st_ino) and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'owned allocated inode changed')
            raw=os.pread(fd,s.st_size,0)
            require(len(raw)==s.st_size and digest(raw)==self._sealed.get(name,digest(b'\0'*s.st_size)), 'immutable slot changed')
        self._floor()

    @property
    def states(self):
        return self._states

    @property
    def events(self):
        return self._events

    def _event(self,i,phase,obj):
        raw=canonical(obj);self._write('%s-%04d'%(phase,i),raw)
        self._events+=((i,phase,raw),)
        states=list(self._states);states[i]=phase.upper();self._states=tuple(states)

    def transfer(self,body,send,recover,cleanup=lambda:None):
        """Exactly one ordered member; attempted identity consumed even on failure."""
        require(not self.failed and not self.closed, 'terminal failed/closed spool')
        i=self._next
        try:
            self.check()
            require(i<len(self._plan.members) and i<self._plan.window, 'retained window exhausted; no retirement authority')
            m=self._plan.members[i];self._next+=1
            require(type(body) is bytes and len(body)==m.size and digest(body)==m.sha256,'original opaque body mismatch')
            self._event(i,'pending',{'plan':self.identity,'member':dataclasses.asdict(m)})
            self._write('body-%04d'%i,body);self.check()
            self.calls+=1;ack=send(self.identity,m,body);self.check()
            require(valid_ack(ack) and (ack.plan,ack.page,ack.chunk,ack.size,ack.sha256)==(self.identity,m.page,m.chunk,m.size,m.sha256) and sha(ack.receipt_sha256), 'exact unique acknowledgement required')
            self._event(i,'ack',dataclasses.asdict(ack))
            self.calls+=1;r=recover(ack);self.check()
            require(type(r) is Recovery and valid_ack(r.ack) and r.ack==ack and type(r.body) is bytes and r.body==body, 'complete opaque recovery mismatch')
            self._event(i,'recovered',{'ack_sha256':digest(canonical(dataclasses.asdict(ack))),'body_sha256':digest(r.body)})
        except BaseException as error:
            self.failed=True
            def retain():
                self._write('terminal',canonical({'status':'FAILED','index':i,'exception_type':type(error).__name__,'attempted_prefix':self._next,'absent_suffix_start':self._next,'member_count':len(self._states),'consumed':self.consumed}))
            io._cleanup((retain,),primary=error)
            raise
        finally:
            try:
                io._cleanup((cleanup,))
                if not self.failed:
                    self.check()
                    self._event(i,'eligible',{'typed_complete_research_recovery':False,'release_authority':False,'external_retirement_required':True})
                    self.check()
            except BaseException as error:
                self.failed=True
                if 'terminal' not in self._sealed:
                    io._cleanup((lambda:self._write('terminal',canonical({'status':'FAILED_CLEANUP','index':i,'exception_type':type(error).__name__,'consumed':self.consumed})),),primary=error)
                raise

    def release(self):
        raise RuntimeError('no release/deletion authority: complete typed external recovery and genuine release adapter required')

    def close(self):
        if self.closed:return
        self.closed=True
        fds=tuple(self._fds.values())+(self.fd,)
        self._fds={}
        io._cleanup(tuple(lambda fd=fd:os.close(fd) for fd in fds))
