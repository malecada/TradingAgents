"""Explicit engineering result reuse; never old per-occurrence execution credit."""
import array,copy,ctypes,hashlib,json,math,struct,sys,types,time
from pathlib import Path
from . import adaptive_edge_policy
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from . import matching_checkpoint as engine
from tradingagents.research.onchain_replication import matching_pair as pair
from tradingagents.research.onchain_replication import matching_reference as reference
from tradingagents.research.onchain_replication import contracts

from . import batched_pair_executor as accepted
from .geometry_summary import Geometry
from . import matching_immutable_session as immutable_session

MODULES=(accepted,engine,engine.ann,engine.hard,engine.sparse,engine.ann.typed_identity,pair,reference,contracts,immutable_session,adaptive_edge_policy)
SOURCE_PINS=(
    (adaptive_edge_policy, '31e1242a3312586560cff8da10ff96e329874f4edc0751b838f7f88035f126af'),
    (accepted, 'f7c51b9423a45c0e61defd9260924acb1e0611d5c8727de8abb96e42d1ad147e'),
    (engine, '309f260cdd0956966ecbd588df9da11f9c45f241ddeab93fb280c96f8ddf9f4a'),
    (engine.ann, 'b9229da33098c6c00c2e0e85a0a25a7d1a6f7968befbf82e30a092c424dd967e'),
    (engine.hard, '3c34a2fab8657747b2ed984120c13ddfde6f86c7eb53dcb47c011dacb9189a1c'),
    (engine.sparse, '06f2d312a1527f335decc8e0c4d1283448a28e783d5e64018d70e9bf3416883e'),
    (engine.ann.typed_identity, '0d72321bcaef01fe9667e5e6bc42c78ecb4aaca4a9099dcf5ceb924718c8c7d7'),
    (pair, '4a99532c84afabc5768ae0fe450fa5c9619ec25ee2833e0766dce023e477a20e'),
    (reference, '75e3269a94cf0d840c299f52c7b138b58dd138251bde6048e52e6c1149934332'),
    (contracts, '3f88e9e56f2bfca059e2ef9da2b01ae593444b05e1067154653ea6a5479fea1a'),
    (immutable_session, 'c3fc9b7a9a456f269eded17ba5ece492edccc91e2fc8e6563a0febcca80baeef'),
)

def require(ok,message):
    if not ok:raise ValueError(message)
def raw(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
# Snapshots originate only in this trusted module import, never caller input.
def roster():
    result=[]
    for module in MODULES:
        for name,value in sorted(vars(module).items()):
            if isinstance(value,types.FunctionType):result.append((module.__name__,name,id(value),id(value.__code__)))
            elif isinstance(value,type) and value.__module__==module.__name__:
                for method,item in sorted(vars(value).items()):
                    if isinstance(item,types.FunctionType):result.append((module.__name__,name+'.'+method,id(item),id(item.__code__)))
    return tuple(result)
ROSTER=roster()
DIRECT=(np.asarray,np.empty,np.zeros,np.exp,np.multiply,np.add,math.exp,math.fsum)
ROUND=ctypes.CDLL(None).fegetround;ROUND.argtypes=[];ROUND.restype=ctypes.c_int

def attest(counters):
    counters['source_guard_calls']+=1
    require(roster()==ROSTER,'numeric runtime function/code changed')
    light_environment()
    for module,pin in SOURCE_PINS:
        h=hashlib.sha256()
        with Path(module.__file__).open('rb') as stream:
            for chunk in iter(lambda:stream.read(65536),b''):
                counters['source_hashed_bytes']+=len(chunk);h.update(chunk)
        require(h.hexdigest()==pin,'numeric source changed')

def light_environment():
    require((np.asarray,np.empty,np.zeros,np.exp,np.multiply,np.add,math.exp,math.fsum)==DIRECT,'numeric primitive changed')
    require(ROUND()==0 and np.geterr()=={'divide':'warn','over':'warn','under':'ignore','invalid':'warn'},'default numerical environment required')
    require(sys.gettrace() is None and sys.getprofile() is None,'instrumented runtime unsupported')


def config_bytes(config):
    require(type(config) is dict and all(type(k) is str and type(v) in (str,int,float,bool) for k,v in config.items()),'plain primitive matching config required')
    return raw(config)

def immutable(graph):
    if type(graph) is not AttributedGraph or type(graph.node_ids) is not tuple:return False
    if any(type(v) is not str for v in graph.node_ids) or type(graph.parent_hash) is not str or type(graph.center_id) is not str:return False
    for name in ('node_features','edge_index','edge_features'):
        array=getattr(graph,name)
        if type(array) is not np.ndarray or not array.flags.c_contiguous or array.dtype.kind not in 'fiu':return False
        for _ in range(4):
            if type(array) is bytes:break
            if type(array) is not np.ndarray or array.flags.writeable:return False
            array=array.base
        else:return False
    return True

def numeric_key(a,b,configuration,limit):
    # Exact ordered framing, no hash-only equivalence and no retained graph refs.
    arrays=[getattr(g,n) for g in (a,b) for n in ('node_features','edge_index','edge_features')]
    headers=[raw({'dtype':x.dtype.str,'shape':list(x.shape)}) for x in arrays]
    size=8+len(configuration)+sum(16+len(h)+x.nbytes for h,x in zip(headers,arrays,strict=True))
    if size>limit:return None
    parts=[struct.pack('>Q',len(configuration)),configuration]
    for header,array in zip(headers,arrays,strict=True):parts.extend((struct.pack('>Q',len(header)),header,struct.pack('>Q',array.nbytes),array.tobytes(order='C')))
    result=b''.join(parts);require(len(result)==size,'key extent differs');return result

def entry_size(entry):
    key,value,hashed=entry
    return sys.getsizeof(entry)+sys.getsizeof(key)+sys.getsizeof(value)+sys.getsizeof(hashed)+sum(sys.getsizeof(x) for x in value)

class NumericReuseExecutor:
    """Explicit batches; source/runtime attestation is NOT continuous authority."""
    def __init__(self,config,policy,schedule,checkpoint,*,max_entries,max_retained_bytes,max_key_bytes,authority_poll=None,geometry=False,max_geometry_summary_bytes=8192,edge_cache_policy=None):
        adaptive_edge_policy.attach(self,edge_cache_policy)
        require(type(max_entries) is int and 0<max_entries<=4096,'finite entry bound required')
        require(type(max_retained_bytes) is int and 1024<=max_retained_bytes<=64*1024**2,'retained cache bound required')
        require(type(max_key_bytes) is int and 0<max_key_bytes<=min(max_retained_bytes,8*1024**2),'bounded exact key required')
        require(callable(checkpoint),'checkpoint callback required')
        require(geometry is None or type(geometry) is bool,'geometry opt-in must be bool or None')
        self._geometry=Geometry(max_geometry_summary_bytes) if geometry is True else None
        self.last_geometry_summary=None
        self.counters=dict(source_guard_calls=0,source_hashed_bytes=0,key_hashed_bytes=0,lookup_probes=0,lru_link_updates=0,evictions=0)
        attest(self.counters);self.configuration=config_bytes(config);self.checkpoint=checkpoint;self._user_checkpoint=checkpoint
        if authority_poll is not None:
            require(callable(authority_poll),'optional authority poll must be callable')
            original_poll=authority_poll;clock=time.perf_counter_ns
            require(type(clock) is types.BuiltinFunctionType and clock.__module__=='time' and clock.__name__=='perf_counter_ns','builtin authority timer required')
            self._authority_poll_original=original_poll
            names=('authority_poll_calls','authority_poll_ns','authority_poll_failures')
            totals=[0,0,0];limit=2**63-1
            self.counters.update(dict(zip(names,totals)))
            def current_poll():
                require(self._authority_poll_original is original_poll and time.perf_counter_ns is clock,'authority callback/timer changed')
                require(all(type(self.counters.get(k)) is int and self.counters[k]==v for k,v in zip(names,totals)),'authority timing counters changed')
            def measured_poll():
                current_poll();start=clock()
                require(type(start) is int and 0<=start<=limit and totals[0]<limit,'authority timing bound exceeded')
                totals[0]+=1;self.counters[names[0]]=totals[0]
                primary=None
                try:
                    return original_poll()
                except BaseException as error:
                    primary=error;raise
                finally:
                    try:
                        stop=clock();current_poll()
                        require(type(stop) is int and start<=stop<=limit and totals[1]+stop-start<=limit,'authority timing bound exceeded')
                        totals[1]+=stop-start
                        if primary is not None:totals[2]+=1
                        self.counters.update(dict(zip(names,totals)))
                    except BaseException as timing_error:
                        if primary is None:raise
                        primary.add_note('authority timing failed: '+repr(timing_error))
            authority_poll=measured_poll
        self.authority_poll=authority_poll
        self.executor=accepted.PairExecutor(config,policy,schedule,self._checkpoint,authority_poll=authority_poll,**adaptive_edge_policy.options(self))
        self.checkpoint_adapter=self.executor.checkpoint
        self.policy_pin=raw(self.executor.policy);self.schedule_pin=raw(self.executor.schedule)
        self.max_entries=max_entries;self.max_retained_bytes=max_retained_bytes;self.max_key_bytes=max_key_bytes
        buckets=1
        while buckets<2*max_entries:buckets*=2
        self._slots=[None]*max_entries
        self._heads=array.array('i',[-1])*buckets
        self._hp=array.array('i',[-1])*max_entries;self._hn=array.array('i',range(1,max_entries+1));self._hn[-1]=-1
        self._lp=array.array('i',[-1])*max_entries;self._ln=array.array('i',[-1])*max_entries
        self._base_bytes=sum(sys.getsizeof(v) for v in (self._slots,self._heads,self._hp,self._hn,self._lp,self._ln))
        require(self._base_bytes<=max_retained_bytes,'fixed tables exceed cache allowance')
        self._bytes=self._base_bytes;self.counters['accounted_cache_bytes']=self._bytes;self._free=0;self._oldest=self._newest=-1;self.count=0
        self.poisoned=False;self.closed=False;self.active=False;self.occurrences=0;self.computed=0;self.reused=0;self.last_receipt=None
        self._pins=(accepted.PairExecutor.__call__,accepted.PairExecutor.__call__.__code__,reference.validate_pair,reference.validate_pair.__code__,pair.policy_check,pair.policy_check.__code__,engine.ann.typed_identity.graph_identity,engine.ann.typed_identity.graph_identity.__code__)
    @property
    def retained_bytes(self):return self._bytes
    def _current(self):
        adaptive_edge_policy.join(self,self.executor)
        light_environment()
        require((accepted.PairExecutor.__call__,accepted.PairExecutor.__call__.__code__,reference.validate_pair,reference.validate_pair.__code__,pair.policy_check,pair.policy_check.__code__,engine.ann.typed_identity.graph_identity,engine.ann.typed_identity.graph_identity.__code__)==self._pins,'occurrence function pins changed')
        require(self.executor.authority_poll is self.authority_poll,'authority poll changed')
        require(not self.executor.poisoned and config_bytes(self.executor.config)==self.configuration and raw(self.executor.policy)==self.policy_pin and raw(self.executor.schedule)==self.schedule_pin and self.executor.checkpoint is self.checkpoint_adapter and self.checkpoint is self._user_checkpoint,'executor/config/policy/schedule changed')
    def begin_batch(self):
        require(not self.closed and not self.poisoned and not self.active,'batch entry unavailable')
        try:
            attest(self.counters);self._current();self.active=True
            if self._geometry is not None:
                self.last_geometry_summary=None;self._geometry_counts=(self.computed,self.reused);self._geometry.begin(self.occurrences)
        except BaseException:self._poison();raise
    def end_batch(self):
        require(not self.closed and not self.poisoned and self.active,'batch final unavailable')
        try:
            self._current();attest(self.counters);self.active=False
            if self._geometry is not None:
                self.last_geometry_summary=self._geometry.finish(self.occurrences,self.computed-self._geometry_counts[0],self.reused-self._geometry_counts[1])
        except BaseException:self._poison();raise
    def _checkpoint(self,*args):
        self._current();attest(self.counters)
        self.checkpoint(*args)
        self._current();attest(self.counters)
    def _bucket(self,hashed):return hashed&(len(self._heads)-1)
    def _find(self,key,hashed):
        i=self._heads[self._bucket(hashed)]
        while i!=-1:
            self.counters['lookup_probes']+=1;entry=self._slots[i]
            if entry[2]==hashed and entry[0]==key:return i
            i=self._hn[i]
        return None
    def _unlink_lru(self,i):
        prev,next=self._lp[i],self._ln[i]
        if prev==-1:self._oldest=next
        else:self._ln[prev]=next
        if next==-1:self._newest=prev
        else:self._lp[next]=prev
        self.counters['lru_link_updates']+=1
    def _append_lru(self,i):
        self._lp[i]=self._newest;self._ln[i]=-1
        if self._newest==-1:self._oldest=i
        else:self._ln[self._newest]=i
        self._newest=i;self.counters['lru_link_updates']+=1
    def _touch(self,i):
        if i!=self._newest:self._unlink_lru(i);self._append_lru(i)
    def _evict(self):
        i=self._oldest;entry=self._slots[i];bucket=self._bucket(entry[2]);prev,next=self._hp[i],self._hn[i]
        if prev==-1:self._heads[bucket]=next
        else:self._hn[prev]=next
        if next!=-1:self._hp[next]=prev
        self._unlink_lru(i);self._bytes-=entry_size(entry);self._slots[i]=None
        self._hp[i]=-1;self._hn[i]=self._free;self._free=i;self.count-=1;self.counters['evictions']+=1;self.counters['accounted_cache_bytes']=self._bytes
    def _store(self,key,hashed,result,purpose,ordinal):
        entry=(key,(*result,purpose,ordinal),hashed);size=entry_size(entry)
        if self._base_bytes+size>self.max_retained_bytes:return False
        while self.count and (self.count==self.max_entries or self._bytes+size>self.max_retained_bytes):self._evict()
        i=self._free;self._free=self._hn[i];bucket=self._bucket(hashed);next=self._heads[bucket]
        self._slots[i]=entry;self._hp[i]=-1;self._hn[i]=next
        if next!=-1:self._hp[next]=i
        self._heads[bucket]=i;self._append_lru(i);self.count+=1;self._bytes+=size;self.counters['accounted_cache_bytes']=self._bytes;return True
    def _clear(self):
        while self.count:self._evict()
    def _poison(self):
        if self._geometry is not None:self._geometry.poison();self.last_geometry_summary=None
        self.poisoned=True;self.executor.poisoned=True;self.active=False;self._clear();self.last_receipt=None
    def __call__(self,a,b,purpose_hash):
        require(not self.closed and not self.poisoned and self.active,'active batch required')
        self.last_receipt=None
        try:
            if self.authority_poll is not None:self.authority_poll()
            self._current();require(type(purpose_hash) is str and self.occurrences<2**64,'plain purpose and bounded occurrence required');pair.hash_string(purpose_hash)
            reference.validate_pair(a,b,self.executor.config)
            pair.policy_check(a,b,self.executor.config,self.executor.policy,allow_checkpoint_layout=True)
            engine.ann.typed_identity.graph_identity(a);engine.ann.typed_identity.graph_identity(b)
            key=numeric_key(a,b,self.configuration,self.max_key_bytes) if immutable(a) and immutable(b) else None
            hashed=None
            if key is not None:
                self.counters['key_hashed_bytes']+=len(key);hashed=int.from_bytes(hashlib.sha256(key).digest()[:8],'big')
            before=(self.executor.checkpoints,self.executor.reserved_bytes);ordinal=self.occurrences
            index=self._find(key,hashed) if key is not None else None
            if index is not None:
                value=self._slots[index][1];result=value[:3];origin_purpose,origin_ordinal=value[3:];mode='reused'
            else:result=self.executor(a,b,purpose_hash);origin_purpose,origin_ordinal=purpose_hash,ordinal;mode='computed'
            require(type(result) is tuple and len(result)==3 and type(result[0]) is float and math.isfinite(result[0]) and 0<=result[0]<=1 and type(result[1]) is int and result[1]>=0 and result[2] in ('temperature_complete','iteration_cap'),'complete numeric result required')
            if self.authority_poll is not None:self.authority_poll()
            self._current()
            if key is not None:require(immutable(a) and immutable(b) and numeric_key(a,b,self.configuration,self.max_key_bytes)==key,'numeric inputs changed during computation')
            cached=False
            if key is not None:
                if mode=='reused':self._touch(index);cached=True
                else:cached=self._store(key,hashed,result,purpose_hash,ordinal)
            require(self._bytes<=self.max_retained_bytes,'physical retained cache bound exceeded')
            self.last_receipt={'schema_version':2,'kind':'engineering_numeric_occurrence','ordinal':ordinal,'purpose_sha256':purpose_hash,'mode':mode,'origin_purpose_sha256':origin_purpose,'origin_ordinal':origin_ordinal,'score_f64_be':struct.pack('>d',result[0]).hex(),'iterations':result[1],'convergence':result[2],'cached':cached,'checkpoint_attempt_delta':self.executor.checkpoints-before[0],'checkpoint_reserved_byte_delta':self.executor.reserved_bytes-before[1],'retained_cache_bytes':self._bytes,'old_per_occurrence_execution_credit':False,'boundary_validated_batch_complete':False}
            if self._geometry is not None:self._geometry.add(a,b,self.last_receipt)
            self.occurrences+=1;self.computed+=mode=='computed';self.reused+=mode=='reused';return result
        except BaseException:self._poison();raise
    def close(self):
        # Close does not silently turn an unfinished batch into an attested one.
        try:
            if self.active and not self.poisoned:self.end_batch()
        finally:self._clear();self.last_receipt=None;self.closed=True
