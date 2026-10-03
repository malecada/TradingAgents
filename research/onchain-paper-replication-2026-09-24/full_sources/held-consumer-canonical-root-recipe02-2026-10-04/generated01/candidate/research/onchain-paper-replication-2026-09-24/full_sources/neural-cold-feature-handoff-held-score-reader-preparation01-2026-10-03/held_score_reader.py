"""Genuine held-stage local sealed-batch reader; no transport or disposition.

Load this dated module with its two exact source-pinned local content helpers.
Production imports below require the genuine installed numerical/source closure;
pure tests extract this code with explicitly qualified authority stand-ins.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import os
import stat
import sys
import exact_members02 as content
import owned_io as local_io
from tradingagents.research.onchain_replication import compact_owner as owners
from tradingagents.research.onchain_replication import imported_mcm_identity as imported
from tradingagents.research.onchain_replication import mcm_score_stream as streams
from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest,thaw
from tradingagents.research.onchain_replication.matching_identity import graph_identity

require=content.require
META=8192
PART=1048576
MAX_CHUNKS=32767
PREFIX='research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03'
CONTENT_SHA='ea1ffcef833344ff1a5fbd89bc2f79ade1414c90a3159329c1f3bdee86bfe0cb'
LOCAL_IO_SHA='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'

def _actual_fatal(error):
    return (isinstance(error,MemoryError) or not isinstance(error,Exception)) and not isinstance(error,(local_io.CleanupFailure,owners.io.CleanupFailure))

def _select(primary,later):
    if primary is None:return later
    if _actual_fatal(primary):return primary
    if _actual_fatal(later):return later
    if isinstance(later,(local_io.CleanupFailure,owners.io.CleanupFailure)) and not isinstance(primary,(local_io.CleanupFailure,owners.io.CleanupFailure)):return later
    return primary

def _actions(actions,primary=None):
    selected=primary
    for action in actions:
        try:action()
        except BaseException as error:selected=_select(selected,error)
    if selected is not None:raise selected

def _read(path):
    path=Path(path);require(path.is_absolute() and path.resolve()==path,'direct original metadata path required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        s=os.fstat(fd);pin=content.signature(s)
        require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=META and content.signature(path.lstat())==pin,'original bounded metadata differs')
        pieces=[];count=0
        while True:
            b=os.read(fd,min(4096,META-count+1))
            if not b:break
            count+=len(b);require(count<=META,'metadata extent exceeded');pieces.append(b)
        raw=b''.join(pieces)
        require(count==s.st_size and content.signature(os.fstat(fd))==content.signature(path.lstat())==pin and path.resolve()==path,'original metadata changed')
        return raw,pin
    finally:local_io._cleanup((lambda:os.close(fd),))

def _source_check(owner):
    root=owner.bound._run.admission.root;registered=owner.bound._run.admission.experiment['source_files']
    paths={PREFIX+'/held_score_reader.py':Path(__file__),PREFIX+'/exact_members02.py':Path(content.__file__),PREFIX+'/owned_io.py':Path(local_io.__file__),
        'tradingagents/research/onchain_replication/mcm_score_stream.py':Path(streams.__file__)}
    for name,loaded in paths.items():
        expected=registered.get(name)
        if name.endswith('/exact_members02.py'):require(expected==CONTENT_SHA,'accepted local content source changed')
        if name.endswith('/owned_io.py'):require(expected==LOCAL_IO_SHA,'accepted local IO source changed')
        require(content.sha(expected) and loaded.resolve()==root/name,'held reader loaded source not admitted')
        # Source bodies are bounded separately from compact8KiB metadata.
        fd=os.open(root/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
        try:
            before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=1048576,'held source body bound differs')
            h=hashlib.sha256();count=0
            while True:
                b=os.read(fd,min(65536,1048577-count))
                if not b:break
                count+=len(b);require(count<=1048576,'source grew');h.update(b)
            require(count==before.st_size and h.hexdigest()==expected and content.signature(before)==content.signature(os.fstat(fd))==content.signature((root/name).lstat()),'held source body changed')
        finally:local_io._cleanup((lambda:os.close(fd),))
    require(content._cleanup is local_io._cleanup,'local content cleanup module changed')


class HeldBatches:
    __slots__=('_objects','_completion','_scope','_scientific','_cm','_reader','_pins','_failed','_closed','_frozen')
    def __setattr__(self,name,value):
        if getattr(self,'_frozen',False):raise AttributeError('held reader cannot be rebound')
        object.__setattr__(self,name,value)
    def __delattr__(self,name):raise AttributeError('held reader cannot be deleted')
    def __init__(self,target,stage,held,stream):
        require(type(target) is imported.Target and type(stage) is owners.Stage and type(held) is owners._HeldTransition and type(stream) is streams.MCMScoreStream,'actual Target/Stage/held transition/stream required')
        owner=target.owner;require(type(owner) is owners.Owner,'actual Owner required')
        self._objects=(target,stage,held,stream,owner,owner.bound,owner.bound._run)
        self._completion=None;self._scope=None;self._scientific=None
        self._cm=None;self._reader=None;self._pins=None;self._failed=False;self._closed=False;self._frozen=True
        try:
            object.__setattr__(self,'_completion',streams.completed_evidence(stream))
            object.__setattr__(self,'_scope',canonical_bytes(target.derive_scope()))
            object.__setattr__(self,'_scientific',(target.graph,target.dictionary,tuple(graph_identity(m) for m in target.dictionary.representatives),target.dictionary.identity,target.dictionary.matching_config_hash))
            self._authority();pins,terminal=self._metadata();object.__setattr__(self,'_pins',pins)
            cm=content.open_local(stage.root/'stream/batches',kind='score-batches',document_sha256=terminal)
            object.__setattr__(self,'_cm',cm)
            reader=cm.__enter__();object.__setattr__(self,'_reader',reader)
            self._check()
        except BaseException as primary:
            # __enter__ handles its own failed construction/FD; never exit it twice.
            if self._reader is None:object.__setattr__(self,'_cm',None)
            self._close(primary)
    @property
    def closed(self):return self._closed
    @property
    def members(self):
        self._checked();return self._reader.members
    def _revoke(self):
        object.__setattr__(self,'_failed',True);self._objects[4].poisoned=True
    def _authority(self):
        require(not self._closed and not self._failed,'held reader revoked or closed')
        target,stage,held,stream,owner,bound,run=self._objects
        require(target.owner is owner and owner.bound is bound and bound._run is run and stage.owner is owner
            and owner.active is stage and owner.stages.get(stage.name) is stage and stage.kind=='mcm' and not stage.closed,'original held authority objects changed')
        held.check(owner);owner.lease();stage.lease();owners.verify_current(owner);target.check();_source_check(owner)
        scope=target.derive_scope();require(canonical_bytes(scope)==self._scope,'original target workload changed')
        graph,dictionary,motifs,identity,matching=self._scientific
        require(target.graph is graph and target.dictionary is dictionary and dictionary.identity==identity and dictionary.matching_config_hash==matching
            and tuple(graph_identity(m) for m in dictionary.representatives)==motifs and len(motifs)==32,'original dictionary/graph/motif order changed')
        require(stream._imported is stream._imported_pin is target and stream.batches is self._completion[0][1]
            and streams.completed_evidence(stream)==self._completion and stream.root==stage.root/'stream'
            and stream.scope==scope and stream.workload==scope['workflow'] and stage.scope['workflow']==scope['workflow']
            and stream.owner==owner.identity and stream.n==len(graph.node_ids) and stream.k==32 and stage.pairs==stream.cells==32*stream.n,'successful original stream/workload differs')
        require(type(stream.batches.chunk_cells) is int and stream.batches.chunk_cells==owner.policy['score_chunk_cells']
            and 1<=stream.batches.chunks<=MAX_CHUNKS
            and 8*stage.pairs<=stage.reservation<=owner.policy['max_retained_logical_bytes'],'original chunk policy/count/reservation differs')
        record=bound.record;require(record.get('resource_only') is True and record['source_commit']==run.admission.source,'actual resource source required')
        key=record['job_input'];require(run.admission.inputs[key]['sha256']==record['job_sha256'] and digest(run.read_input(key))==record['job_sha256'],'actual selected resource job changed')
        held.check(owner);stage.lease();owners.verify_current(owner)
    def _metadata(self):
        target,stage,held,stream,owner,bound,run=self._objects
        require(stage.root.resolve()==stage.root and (stage.root.lstat().st_dev,stage.root.lstat().st_ino)==stage.inode,'original stage inode changed')
        files=(stage.root/'intent.json',stream.root/'start.json',stream.root/'complete.json',stream.root/'batches/start.json')
        bodies=[];pins=[]
        for p in files:
            raw,pin=_read(p);bodies.append(raw);pins.append((str(p),pin,digest(raw)))
        require(bodies[0]==stage.intent and digest(bodies[0])==stage.intent_sha256,'original stage intent changed')
        start=content.parse(bodies[1]);complete=content.parse(bodies[2]);batchstart=content.parse(bodies[3]);scope=target.derive_scope()
        require(start=={'schema_version':1,'kind':'mcm-score-stream','scope':scope,'owner':owner.identity,'rows':stream.n,'motifs':32,'batch_start_sha256':stream.batches.start_sha,'chunk_cells':stream.batches.chunk_cells}
            and all(type(start[k]) is int for k in ('schema_version','rows','motifs','chunk_cells')) and digest(bodies[1])==stream.start_sha,'original stream start differs')
        require(bodies[2]==self._completion[1] and digest(bodies[2])==self._completion[2]
            and set(complete)=={'schema_version','start_sha256','head','cells','chunks','batch_terminal_sha256'}
            and all(type(complete[k]) is int for k in ('schema_version','cells','chunks')) and complete['schema_version']==1
            and complete['start_sha256']==stream.start_sha and complete['head']==stream.head and complete['cells']==stage.pairs
            and complete['chunks']==stream.batches.chunks and content.sha(complete['batch_terminal_sha256']),'genuine completed stream receipt changed')
        require(batchstart=={'schema_version':1,'scope':scope,'owner':owner.identity,'rows':stream.n,'motifs':32,'chunk_cells':stream.batches.chunk_cells,'dtype':'<f8','order':'row-major'}
            and all(type(batchstart[k]) is int for k in ('schema_version','rows','motifs','chunk_cells'))
            and digest(bodies[3])==stream.batches.start_sha,'original batch header policy differs')
        require(self._pins is None or tuple(pins)==self._pins,'original metadata inode/content changed')
        return tuple(pins),complete['batch_terminal_sha256']
    def _check(self):
        self._authority();self._metadata();self._reader.check();self._authority();self._metadata();self._reader.check()
    def _checked(self):
        try:self._check()
        except BaseException as primary:_actions((self._revoke,),primary)
    def read_part(self,name,offset,count):
        try:
            self._check();require(type(count) is int and 1<=count<=PART and type(offset) is int and offset>=0 and offset%8==0 and count%8==0,'bounded float64-aligned byte range required')
            raw=self._reader.read_part(name,offset,count);self._check();return raw
        except BaseException as primary:_actions((self._revoke,),primary)
    def _close(self,primary=None):
        if self._closed:
            if primary is not None:raise primary
            return
        errors=[]
        # Every action is independent. The content context sees no foreign primary:
        # its own reducer class is kept separate from canonical Owner uncertainty.
        def attempt(action):
            try:action()
            except BaseException as error:errors.append(error)
        if self._reader is not None:attempt(self._check)
        cm=self._cm;object.__setattr__(self,'_cm',None)
        if cm is not None:attempt(lambda:cm.__exit__(None,None,None))
        attempt(self._authority);attempt(self._metadata)
        selected=primary
        for error in errors:selected=_select(selected,error)
        if selected is not None:
            try:self._revoke()
            except BaseException as error:selected=_select(selected,error)
        object.__setattr__(self,'_closed',True)
        if selected is not None:raise selected

@contextmanager
def open_held(target,stage,held,stream):
    reader=HeldBatches(target,stage,held,stream)
    try:yield reader
    except BaseException as primary:reader._close(primary);raise
    else:reader._close()
