"""Lossless engineering codec-file routing. No production or research authority.

Callbacks are finite/cooperative and byte equality is provisional engineering
readback. No network, retirement, deletion, numeric conversion or model batching.
"""
import dataclasses as D
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import codec01 as C
import local_store01 as L
import recovery04 as R
import spool05 as S
import owned_io as IO

MAX_TARGETS=16
MAX_MEMBERS=20000
MAX_PLANS=2048
EVENT=4096
SCRATCH=12*C.FILE


def require(ok,why):
    if not ok:raise ValueError(why)


def encode(value):
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False,default=lambda v: {'immutable_bytes_hex':v.hex()} if type(v) is bytes else (_ for _ in ()).throw(TypeError('unsupported metadata type')))+'\n').encode()
    require(len(raw)<=C.FILE,'routing metadata file cap')
    return raw


def sha(raw):return hashlib.sha256(raw).hexdigest()


@D.dataclass(frozen=True)
class File:
    ordinal:int
    name:str
    kind:str
    size:int
    sha256:str
    mode:int
    raw_offset:int
    raw_size:int
    raw_sha256:str


@D.dataclass(frozen=True)
class Inventory:
    target_key:str
    root:str
    root_identity:tuple
    descriptor:bytes
    terminal_sha256:str
    raw_sha256:str
    logical_bytes:int
    files:tuple
    original_signatures:tuple

    def pin(self):
        _inventory_schema(self)
        return sha(encode(D.asdict(self)))


def inspect(root,target_key,expected,terminal_pin):
    """Authenticate complete actual codec files. target_key is NOT a Target."""
    C.pin(target_key);C.pin(terminal_pin)
    descriptor=C.canonical(expected);expected=C.parse(descriptor);C.descriptor(expected)
    root=Path(root);require(root.is_absolute() and root.resolve(strict=True)==root,'canonical original codec directory')
    before=root.lstat();require(stat.S_ISDIR(before.st_mode) and stat.S_IMODE(before.st_mode)==0o700 and before.st_blocks*512<=L.BLOCK,'private source directory')
    names=set(os.listdir(root));require(0<len(names)<=MAX_MEMBERS,'finite source files')
    pins={}
    for name in sorted(names):
        L.name(name);st=(root/name).lstat()
        require(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and 0<st.st_size<=C.FILE,'literal complete source types/modes')
        pins[name]=R.sig(st)
    result=C.verify_stream(lambda name:R.read(root,L.name(name)),terminal_pin,expected)
    require(set(result['members'])==names,'extra/missing codec membership')
    start=C.parse(R.read(root,'start.json'));terminal=C.parse(R.read(root,'terminal.json'))
    ordered=[('start.json','start',-1,0,'')]
    for ref in terminal['pages']:
        page=C.parse(R.read(root,ref['name']))
        for row in page['rows']:
            ordered.append((row['name'],'chunk',row['offset'],row['bytes'],row['raw_sha256']))
        ordered.append((ref['name'],'page',-1,0,''))
    ordered.append(('terminal.json','terminal',-1,0,''))
    require(len(ordered)==len(names) and {x[0] for x in ordered}==names,'emission membership bijection')
    rows=[]
    for i,(name,kind,offset,size,rawpin) in enumerate(ordered):
        body=R.read(root,name);require(R.sig((root/name).lstat())==pins[name],'source changed during enumeration')
        rows.append(File(i,name,kind,len(body),sha(body),0o600,offset,size,rawpin))
    require(root.resolve(strict=True)==root and (root.lstat().st_dev,root.lstat().st_ino,root.lstat().st_mode)==(before.st_dev,before.st_ino,before.st_mode) and set(os.listdir(root))==names,'original root changed during enumeration')
    require(start['descriptor']==expected,'frozen dtype/scope descriptor')
    return Inventory(target_key,str(root),(before.st_dev,before.st_ino,before.st_mode),descriptor,terminal_pin,result['raw_sha256'],result['logical_bytes'],tuple(rows),tuple((n,pins[n]) for n in sorted(pins)))


def _file_schema(value):
    require(type(value) is File, 'exact immutable File')
    require(all(type(getattr(value,k)) is int for k in ('ordinal','size','mode','raw_offset','raw_size')), 'exact integer File fields')
    require(value.ordinal>=0 and 0<value.size<=C.FILE and value.mode==0o600, 'bounded File size/mode/ordinal')
    L.name(value.name);C.pin(value.sha256)
    require(type(value.kind) is str and value.kind in ('start','chunk','page','terminal'), 'exact File kind')
    if value.kind=='chunk':
        require(value.raw_offset>=0 and 0<value.raw_size<=C.CHUNK, 'bounded raw chunk extent')
        C.pin(value.raw_sha256)
    else:
        require(value.raw_offset==-1 and value.raw_size==0 and type(value.raw_sha256) is str and value.raw_sha256=='', 'exact metadata raw sentinel')


def _inventory_schema(value):
    require(type(value) is Inventory, 'exact immutable Inventory')
    C.pin(value.target_key);C.pin(value.terminal_sha256);C.pin(value.raw_sha256)
    require(type(value.root) is str and Path(value.root).is_absolute(), 'exact absolute root string')
    require(type(value.root_identity) is tuple and len(value.root_identity)==3 and all(type(n) is int and n>=0 for n in value.root_identity) and value.root_identity[2]==stat.S_IFDIR|0o700, 'exact original directory signature')
    require(type(value.descriptor) is bytes, 'immutable descriptor bytes')
    total=C.descriptor(C.parse(value.descriptor))
    require(type(value.logical_bytes) is int and value.logical_bytes==total, 'exact logical denominator integer')
    require(type(value.files) is tuple and 0<len(value.files)<=MAX_MEMBERS, 'finite immutable File tuple')
    for i,file in enumerate(value.files):
        _file_schema(file);require(file.ordinal==i, 'exact File ordinal sequence')
    names=tuple(file.name for file in value.files)
    require(len(set(names))==len(names), 'unique File names')
    require(type(value.original_signatures) is tuple and len(value.original_signatures)==len(names), 'immutable complete signatures')
    for entry in value.original_signatures:
        require(type(entry) is tuple and len(entry)==2 and type(entry[0]) is str and type(entry[1]) is tuple and len(entry[1])==7, 'exact nested signature schema')
        require(all(type(n) is int and n>=0 for n in entry[1]), 'exact integer signature fields')
        require(entry[1][2]==stat.S_IFREG|0o600 and entry[1][3]==1 and 0<entry[1][4]<=C.FILE, 'signature type/link/size bounds')
    require(tuple(x[0] for x in value.original_signatures)==tuple(sorted(names)), 'complete sorted signature names')


def current(inventory):
    _inventory_schema(inventory)
    actual=inspect(inventory.root,inventory.target_key,C.parse(inventory.descriptor),inventory.terminal_sha256)
    require(actual==inventory,'original complete codec source changed')


@D.dataclass(frozen=True)
class Partition:
    target:int
    index:int
    start:int
    files:tuple
    plan:S.Plan


@D.dataclass(frozen=True)
class Route:
    inventories:tuple
    partitions:tuple
    members_per_plan:int

    def encoded(self):
        _route_schema(self)
        # Exact source inventory once; partitions reference it without repeating
        # every file descriptor and spool member in the ledger intent.
        return encode({'inventories':[D.asdict(i) for i in self.inventories],
                       'members_per_plan':self.members_per_plan,
                       'partitions':[{'target':p.target,'index':p.index,'start':p.start,
                                      'count':len(p.files),'spool_plan_sha256':sha(p.plan.encoded())}
                                     for p in self.partitions]})
    def pin(self):return sha(self.encoded())


def _route_schema(value):
    require(type(value) is Route and type(value.inventories) is tuple and 0<len(value.inventories)<=MAX_TARGETS, 'exact finite Route inventories')
    for inventory in value.inventories:_inventory_schema(inventory)
    require(type(value.members_per_plan) is int and 0<value.members_per_plan<=32, 'exact retained partition bound')
    require(type(value.partitions) is tuple and 0<len(value.partitions)<=MAX_PLANS, 'exact finite Partition tuple')
    for part in value.partitions:
        require(type(part) is Partition and all(type(getattr(part,k)) is int for k in ('target','index','start')), 'exact integer Partition fields')
        require(0<=part.target<len(value.inventories) and 0<=part.index<len(value.partitions) and part.start>=0, 'bounded partition coordinates')
        require(type(part.files) is tuple and 0<len(part.files)<=value.members_per_plan, 'immutable partition files')
        for file in part.files:_file_schema(file)
        require(type(part.plan) is S.Plan, 'original exact spool Plan')
        part.plan.validate()


def route(inventories,members_per_plan=32):
    require(type(inventories) is tuple and 0<len(inventories)<=MAX_TARGETS and all(type(x) is Inventory for x in inventories),'finite actual inventories')
    for inventory in inventories:_inventory_schema(inventory)
    require(type(members_per_plan) is int and 0<members_per_plan<=32,'retained finite plans; no window recycling')
    require(len({i.target_key for i in inventories})==len(inventories) and len({i.root for i in inventories})==len(inventories),'unique declared target/root identities')
    require(sum(len(i.files) for i in inventories)<=MAX_MEMBERS,'whole route cardinality cap')
    require(sum(i.logical_bytes for i in inventories)<=C.MAX_BYTES, 'whole aggregate logical denominator cap')
    partitions=[]
    for t,inventory in enumerate(inventories):
        current(inventory)
        for start in range(0,len(inventory.files),members_per_plan):
            files=inventory.files[start:start+members_per_plan]
            members=tuple(S.Member(0,j,f.size,f.sha256) for j,f in enumerate(files))
            p=S.Plan(members,len(members),0,0);logical,allocated=p.required()
            p=D.replace(p,logical_reservation=logical,allocated_reservation=allocated);p.validate()
            partitions.append(Partition(t,len(partitions),start,files,p))
    require(len(partitions)<=MAX_PLANS,'finite total plans')
    value=Route(inventories,tuple(partitions),members_per_plan);value.encoded();return value


def validate_route(value):
    _route_schema(value)
    require(route(value.inventories,value.members_per_plan)==value,'complete ordered route reconstruction differs')


def estimate(value):
    """Conservative accounting units, not capacity, quota, wire or memory proof."""
    _route_schema(value)
    roundb=lambda n:((n+L.BLOCK-1)//L.BLOCK)*L.BLOCK
    source_bytes=sum(f.size for i in value.inventories for f in i.files)
    one_copy_allocated=sum(roundb(f.size)+L.ENTRY_HEADROOM for i in value.inventories for f in i.files)+len(value.inventories)*(L.DIRECTORY_HEADROOM+L.SCRATCH_HEADROOM+L.BLOCK)
    spool_logical=sum(p.plan.required()[0] for p in value.partitions)
    spool_allocated=sum(p.plan.required()[1] for p in value.partitions)
    # Original codec files + complete recovered codec duplicate + retained spool
    # duplicate; repeated start/page/footer bytes count in every physical copy.
    # Ledger intent and bounded begin/done/failure journal, root/entries and IO
    # scratch headroom are charged before any route file or callback is written.
    logs=2*len(value.partitions)+4
    ledger_bytes=len(value.encoded())+logs*EVENT
    ledger_allocated=roundb(len(value.encoded()))+(logs+1)*(roundb(EVENT)+L.ENTRY_HEADROOM)+L.DIRECTORY_HEADROOM+L.BLOCK
    return (2*source_bytes+spool_logical+ledger_bytes+SCRATCH,
            2*one_copy_allocated+spool_allocated+ledger_allocated+SCRATCH)


@D.dataclass(frozen=True)
class Envelope:
    route_sha256:str
    inventory_sha256:str
    partition:int
    ordinal:int
    target_key:str
    descriptor_sha256:str
    file:File
    spool_plan_sha256:str
    spool_member:S.Member

    def pin(self):return sha(encode(D.asdict(self)))


@D.dataclass(frozen=True)
class RoutedAck:
    envelope_sha256:str
    ack:S.Ack


@D.dataclass(frozen=True)
class RoutedRecovery:
    envelope_sha256:str
    ack:S.Ack
    body:bytes


def production(*args,**kwargs):
    raise RuntimeError('UNAVAILABLE: genuine original Target/Owner/Binding/Produced ancestry, authenticated reservation/transport/typed recovery/retirement/native capacity are not integrated')


class Router:
    """Single-use byte utility. No callback supplies scientific authority.

    All original, spool and recovered files remain retained. Shared accounting
    never resets/refunds between partitions or targets. A callback may block:
    sampled deadlines cannot replace a separately admitted outer supervisor.
    """
    def __init__(self,root,value,logical_limit,allocated_limit,seconds=120):
        validate_route(value)
        require(type(logical_limit) is int and type(allocated_limit) is int and logical_limit>0 and allocated_limit>0,'strict whole reservation limits')
        require(type(seconds) in (int,float) and 0<seconds<=120,'finite sampled routing deadline')
        need=estimate(value);require(need[0]<=logical_limit and need[1]<=allocated_limit,'whole shared reservation exhausted')
        self.route=value;self._route_pin=value.pin();self._reserved=need;self._reservation_pin=need;self._limits=(logical_limit,allocated_limit)
        self.root=Path(root);self.failed=True;self.closed=False;self.started=False;self.finished=False
        self.deadline=time.monotonic()+seconds;self._files={};self._attempted=();self._completed=();self._retained=();self._recovered=()
        self._rootcheck(empty=True);self.rootpin=self._identity();self._floor(need[1])
        try:
            self._write('intent.json',value.encoded())
            self.failed=False;self.check()
        except BaseException:self.failed=True;raise

    def _identity(self):
        st=self.root.lstat();return (st.st_dev,st.st_ino,st.st_mode)

    def _rootcheck(self,empty=False):
        require(self.root.is_absolute() and self.root.resolve(strict=True)==self.root,'canonical ledger root')
        st=self.root.lstat();require(stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==0o700 and st.st_blocks*512<=L.BLOCK,'private ledger root')
        if empty:require(not os.listdir(self.root),'fresh ledger root')

    def _floor(self,additional=0):
        fs=os.statvfs(self.root)
        require(0<fs.f_frsize<=L.BLOCK and fs.f_bavail*fs.f_frsize>=S.FLOOR+additional,'10GiB floor plus whole reservation observation')

    def _write(self,name,body):
        require(type(body) is bytes and len(body)<=(C.FILE if name=='intent.json' else EVENT) and name not in self._files,'finite immutable ledger event')
        self._rootcheck();require(self._identity()==self.rootpin,'ledger inode changed')
        self._files[name]=None # attempted partial is never reusable or forgotten
        with R.new_file(self.root/name) as fd:
            at=0
            while at<len(body):
                n=os.write(fd,body[at:]);require(n>0,'ledger write progress');at+=n
            os.fsync(fd)
        require(R.read(self.root,name)==body,'ledger readback')
        self._files[name]=(R.sig((self.root/name).lstat()),sha(body))

    def check(self):
        require(not self.failed and not self.closed,'failed/closed routing instance')
        require(time.monotonic()<self.deadline,'routing sampled deadline')
        self._rootcheck();require(self._identity()==self.rootpin and self.route.pin()==self._route_pin,'root/route changed')
        require(set(os.listdir(self.root))==set(self._files),'whole ledger membership')
        for name,pin in self._files.items():
            require(pin is not None and R.sig((self.root/name).lstat())==pin[0] and sha(R.read(self.root,name))==pin[1],'immutable ledger body changed')
        self._floor()
        require(self._reserved==self._reservation_pin, 'shared reservation changed')
        for retained in self._retained:self._check_retained(retained)
        # Sample complete sources and recovered bytes after store cleanup and
        # again at success boundaries. This is not continuous mutation immunity.
        if self._recovered:
            require(len(self._recovered)==len(self.route.inventories), 'complete recovered snapshot population')
            for original,recovered in zip(self.route.inventories,self._recovered):
                current(original);current(recovered)

    @property
    def consumed(self):return self._reserved
    @property
    def limit(self):return self._limits

    def _check_retained(self,retained):
        root,pin,files=retained;root=Path(root)
        require(root.resolve(strict=True)==root and (root.lstat().st_dev,root.lstat().st_ino)==pin and stat.S_IMODE(root.lstat().st_mode)==0o700, 'closed retained spool root changed')
        require(set(os.listdir(root))=={n for n,_,_ in files}, 'closed retained spool membership changed')
        for name,original,expected in files:
            st=(root/name).lstat()
            require(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and (st.st_dev,st.st_ino,st.st_size,st.st_blocks)==original and sha(R.read(root,name))==expected, 'closed retained spool body changed')

    @property
    def attempted(self):return self._attempted
    @property
    def completed(self):return self._completed

    def run(self,spool_roots,recovered_roots,send,recover,cleanup=lambda:None):
        require(not self.failed and not self.closed and not self.started,'routing instance cannot retry')
        self.started=True
        try:
            self.check();validate_route(self.route)
            require(type(spool_roots) is tuple and len(spool_roots)==len(self.route.partitions) and type(recovered_roots) is tuple and len(recovered_roots)==len(self.route.inventories),'exact finite output roots')
            roots=tuple(Path(x) for x in spool_roots+recovered_roots)
            allroots=(self.root,)+tuple(Path(i.root) for i in self.route.inventories)+roots
            require(len(set(allroots))==len(allroots) and all(not a.is_relative_to(b) for a in allroots for b in allroots if a!=b),'disjoint full source/output namespaces')
            for path in roots:
                require(path.is_absolute() and path.resolve(strict=True)==path and stat.S_IMODE(path.lstat().st_mode)==0o700 and path.lstat().st_blocks*512<=L.BLOCK and not os.listdir(path),'fresh private output namespace')
            stores=[]
            try:
                for root in recovered_roots:stores.append(L.LocalStore(root))
                for part in self.route.partitions:
                    self.check();inventory=self.route.inventories[part.target];current(inventory)
                    self._attempted+=(part.index,)
                    self._write('begin-%04d.json'%part.index,encode({'partition':part.index,'inventory_sha256':inventory.pin(),'start':part.start,'members':len(part.files),'consumed':self.consumed}))
                    spool=None
                    try:
                        spool=S.Spool(spool_roots[part.index],part.plan,seconds=min(120,max(0.001,self.deadline-time.monotonic())))
                        for f in part.files:
                            self.check();body=R.read(Path(inventory.root),f.name)
                            require(len(body)==f.size and sha(body)==f.sha256,'exact whole framed member')
                            env=Envelope(self._route_pin,inventory.pin(),part.index,f.ordinal,inventory.target_key,sha(inventory.descriptor),f,spool.identity,part.plan.members[f.ordinal-part.start])
                            received=[]
                            def sending(identity,member,data):
                                require(identity==env.spool_plan_sha256 and member.sha256==f.sha256 and data==body,'original spool routing join')
                                response=send(env,data)
                                require(type(response) is RoutedAck and type(response.envelope_sha256) is str and response.envelope_sha256==env.pin() and S.valid_ack(response.ack),'exact routed acknowledgment')
                                received.append(response);return response.ack
                            def recovering(ack):
                                require(len(received)==1 and ack==received[0].ack,'single original routed ack')
                                response=recover(env,received[0])
                                require(type(response) is RoutedRecovery and type(response.envelope_sha256) is str and response.envelope_sha256==env.pin() and S.valid_ack(response.ack) and response.ack==ack and type(response.body) is bytes and response.body==body,'exact routed recovery')
                                stores[part.target].put(f.name,response.body)
                                return S.Recovery(ack,response.body)
                            spool.transfer(body,sending,recovering,cleanup)
                            self.check()
                        current(inventory)
                        spool.check()
                        retained=(str(spool.root),spool._root,tuple((name,pin,spool._sealed.get(name,sha(b'\0'*pin[2]))) for name,pin in sorted(spool._pins.items())))
                        self._retained+=(retained,)
                    finally:IO._cleanup(() if spool is None else (spool.close,))
                    self.check();self._completed+=(part.index,)
                    self._write('done-%04d.json'%part.index,encode({'partition':part.index,'consumed':self.consumed,'typed_research_recovery':False}))
                for inventory,store in zip(self.route.inventories,stores):
                    current(inventory)
                    proof=store.verify(inventory.terminal_sha256,C.parse(inventory.descriptor))
                    require(proof['raw_sha256']==inventory.raw_sha256 and proof['logical_bytes']==inventory.logical_bytes,'lossless entire raw population')
                    actual=inspect(store.root,inventory.target_key,C.parse(inventory.descriptor),inventory.terminal_sha256)
                    require(actual.files==inventory.files,'complete recovered mode/body/order/offset membership')
                    self._recovered+=(actual,)
            finally:IO._cleanup(tuple(store.close for store in stores))
            self.check()
            self._write('complete.json',encode({'status':'complete-engineering-byte-routing-only','route_sha256':self._route_pin,'members':sum(len(i.files) for i in self.route.inventories),'partitions':len(self._completed),'consumed':self.consumed,'representation_complete':False,'external_origin_proved':False,'release_authority':False}))
            self.check();self.finished=True
        except BaseException as error:
            self.failed=True
            def retain():self._write('failed.json',encode({'status':'FAILED','exception_type':type(error).__name__,'attempted_prefix':len(self._attempted),'completed_prefix':len(self._completed),'total_partitions':len(self.route.partitions),'consumed':self.consumed}))
            IO._cleanup((retain,),primary=error)
            raise

    def close(self):self.closed=True
    def release(self):raise RuntimeError('no typed research recovery, genuine retirement or production release authority')
