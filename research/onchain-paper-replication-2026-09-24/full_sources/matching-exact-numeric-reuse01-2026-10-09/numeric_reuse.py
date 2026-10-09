"""Explicit engineering result reuse; never old per-occurrence execution credit."""
import collections,copy,ctypes,hashlib,importlib.util,json,math,struct,sys,types
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import matching_pair as pair
from tradingagents.research.onchain_replication import matching_reference as reference
from tradingagents.research.onchain_replication import contracts

HERE=Path(__file__).resolve().parent
EXECUTOR_PATH=HERE.parent/'mcm-batched-execution03-2026-10-09/pair_executor.py'
EXECUTOR_SHA='6d1ad3a720eec15f63c7fd6423a9f0c92b4e5020c0d9962ef825f8b5cf73d34a'

def require(ok,message):
    if not ok:raise ValueError(message)
def raw(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
require(digest(EXECUTOR_PATH)==EXECUTOR_SHA,'accepted executor source changed')
spec=importlib.util.spec_from_file_location('accepted_pair_executor_for_numeric_reuse',EXECUTOR_PATH)
accepted=importlib.util.module_from_spec(spec);spec.loader.exec_module(accepted)
MODULES=(accepted,engine,engine.ann,engine.hard,engine.sparse,engine.ann.typed_identity,pair,reference,contracts)
SOURCE_PINS=json.loads((HERE/'SOURCE_PINS.json').read_bytes())
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

def guard():
    require(roster()==ROSTER,'numeric runtime function/code changed')
    require((np.asarray,np.empty,np.zeros,np.exp,np.multiply,np.add,math.exp,math.fsum)==DIRECT,'numeric primitive changed')
    require(ROUND()==0 and np.geterr()=={'divide':'warn','over':'warn','under':'ignore','invalid':'warn'},'default numerical environment required')
    require(sys.gettrace() is None and sys.getprofile() is None,'instrumented runtime unsupported')
    for path,pin in SOURCE_PINS.items():require(digest(Path(path))==pin,'numeric source changed')

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
    key,value=entry
    return sys.getsizeof(entry)+sys.getsizeof(key)+sys.getsizeof(value)+sum(sys.getsizeof(x) for x in value)

def retained_size(cache):
    # Fixed slot list plus exact CPython object sizes; shared primitive values
    # conservatively counted per entry. No hidden hash-table resizing.
    return sys.getsizeof(cache)+sum(entry_size(x) for x in cache if x is not None)

class NumericReuseExecutor:
    def __init__(self,config,policy,schedule,checkpoint,*,max_entries,max_retained_bytes,max_key_bytes):
        require(type(max_entries) is int and 0<max_entries<=4096,'finite entry bound required')
        require(type(max_retained_bytes) is int and 1024<=max_retained_bytes<=64*1024**2,'retained cache bound required')
        require(type(max_key_bytes) is int and 0<max_key_bytes<=min(max_retained_bytes,8*1024**2),'bounded exact key required')
        guard();self.configuration=config_bytes(config)
        self.executor=accepted.PairExecutor(config,policy,schedule,checkpoint)
        self.policy_pin=raw(self.executor.policy);self.schedule_pin=raw(self.executor.schedule);self.checkpoint=checkpoint
        self.max_entries=max_entries;self.max_retained_bytes=max_retained_bytes;self.max_key_bytes=max_key_bytes
        self._cache=[None]*max_entries;require(sys.getsizeof(self._cache)<=max_retained_bytes,'slot table exceeds retained bound');self.count=0;self.poisoned=False;self.closed=False;self.occurrences=0;self.computed=0;self.reused=0;self.last_receipt=None
    @property
    def retained_bytes(self):return retained_size(self._cache)
    def _current(self):
        guard();require(not self.executor.poisoned and config_bytes(self.executor.config)==self.configuration and raw(self.executor.policy)==self.policy_pin and raw(self.executor.schedule)==self.schedule_pin and self.executor.checkpoint is self.checkpoint,'executor/config/policy/schedule changed')
    def _drop_oldest(self):
        for i in range(self.count-1):self._cache[i]=self._cache[i+1]
        self.count-=1;self._cache[self.count]=None
    def _find(self,key):
        for i in range(self.count):
            if self._cache[i][0]==key:return i
        return None
    def _touch(self,index):
        entry=self._cache[index]
        for i in range(index,self.count-1):self._cache[i]=self._cache[i+1]
        self._cache[self.count-1]=entry
    def _store(self,key,result,purpose,ordinal):
        entry=(key,(*result,purpose,ordinal));size=entry_size(entry)
        while self.count and (self.count==self.max_entries or self.retained_bytes+size>self.max_retained_bytes):self._drop_oldest()
        if self.retained_bytes+size>self.max_retained_bytes:return False
        self._cache[self.count]=entry;self.count+=1;return True
    def _clear(self):
        for i in range(self.count):self._cache[i]=None
        self.count=0
    def __call__(self,a,b,purpose_hash):
        require(not self.closed and not self.poisoned,'reuse executor unavailable')
        self.last_receipt=None
        try:
            self._current();require(type(purpose_hash) is str and self.occurrences<2**64,'plain purpose and bounded occurrence required');pair.hash_string(purpose_hash)
            # Validate every fresh occurrence, including nonnumeric identity fields.
            reference.validate_pair(a,b,self.executor.config)
            pair.policy_check(a,b,self.executor.config,self.executor.policy,allow_checkpoint_layout=True)
            engine.ann.typed_identity.graph_identity(a);engine.ann.typed_identity.graph_identity(b)
            eligible=immutable(a) and immutable(b)
            key=numeric_key(a,b,self.configuration,self.max_key_bytes) if eligible else None
            before=(self.executor.checkpoints,self.executor.reserved_bytes)
            ordinal=self.occurrences
            index=self._find(key) if key is not None else None
            if index is not None:
                value=self._cache[index][1];result=value[:3];origin_purpose,origin_ordinal=value[3:];mode='reused'
            else:
                result=self.executor(a,b,purpose_hash);origin_purpose,origin_ordinal=purpose_hash,ordinal;mode='computed'
            require(type(result) is tuple and len(result)==3 and type(result[0]) is float and math.isfinite(result[0]) and 0<=result[0]<=1 and type(result[1]) is int and result[1]>=0 and result[2] in ('temperature_complete','iteration_cap'),'complete numeric result required')
            # Real checkpoint callbacks may have changed runtime/config/graphs.
            self._current()
            if key is not None:require(immutable(a) and immutable(b) and numeric_key(a,b,self.configuration,self.max_key_bytes)==key,'numeric inputs changed during computation')
            cached=False
            if key is not None:
                if mode=='reused':self._touch(index);cached=True
                else:cached=self._store(key,result,purpose_hash,ordinal)
            require(self.retained_bytes<=self.max_retained_bytes,'physical retained cache bound exceeded')
            self.last_receipt={'schema_version':1,'kind':'engineering_numeric_occurrence','ordinal':ordinal,'purpose_sha256':purpose_hash,'mode':mode,'origin_purpose_sha256':origin_purpose,'origin_ordinal':origin_ordinal,'score_f64_be':struct.pack('>d',result[0]).hex(),'iterations':result[1],'convergence':result[2],'cached':cached,'checkpoint_attempt_delta':self.executor.checkpoints-before[0],'checkpoint_reserved_byte_delta':self.executor.reserved_bytes-before[1],'retained_cache_bytes':self.retained_bytes,'old_per_occurrence_execution_credit':False}
            self.occurrences+=1;self.computed+=mode=='computed';self.reused+=mode=='reused';return result
        except BaseException:
            self.poisoned=True;self.executor.poisoned=True;self._clear();self.last_receipt=None;raise
    def close(self):
        self._clear();self.last_receipt=None;self.closed=True
