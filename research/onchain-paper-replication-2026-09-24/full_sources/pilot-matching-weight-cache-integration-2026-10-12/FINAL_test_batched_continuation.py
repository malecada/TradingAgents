"""Offline synthetic byte/ordering controls; no Run or empirical admission."""
import hashlib
import json
import os
from dataclasses import fields
from types import SimpleNamespace
import pytest
from tradingagents.research.onchain_replication import batched_continuation as c
from tradingagents.research.onchain_replication.batched_journal import BatchJournal, body, digest
from tradingagents.research.onchain_replication import batched_numeric_execution as ne


def journal(path):
    return BatchJournal(path,batch_cells=2,max_cells=6,max_bytes=100000,max_body_bytes=8192,boundary=lambda:None)


def numeric(path):
    obj=ne.NumericExecution.__new__(ne.NumericExecution)
    obj.root=path;obj.fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY);obj.root_pin=ne.sig(os.fstat(obj.fd))[:2]
    os.mkdir(path/'numeric-batches')
    obj.batches_fd=os.open(path/'numeric-batches',os.O_RDONLY|os.O_DIRECTORY);obj.batches_pin=ne.sig(os.fstat(obj.batches_fd))[:2]
    obj.origins_fd=os.open(path/'numeric-origins.bin',os.O_CREAT|os.O_RDWR,0o600);obj.origin_sig=ne.sig(os.fstat(obj.origins_fd))
    obj.cells=6;obj.batch_cells=2;obj.max_summary_bytes=50000;obj.max_origin_bytes=54
    obj.closed=obj.poisoned=obj.finished=False;obj.buffer=bytearray();obj.ordinal=obj.batch=0
    obj.summary_bytes=obj.computed=obj.reused=0;obj.elapsed_seconds=0.0
    obj.summary_inventory=hashlib.sha256();obj.origin_hash=hashlib.sha256();obj.summary_hash=hashlib.sha256()
    obj.memo=SimpleNamespace(active=False,occurrences=0,executor=SimpleNamespace(checkpoints=0,reserved_bytes=0,completed_operations=4,advance_calls=2,abandoned_call_operation_limit=0))
    obj.memo.restore_ordinal=lambda n:setattr(obj.memo,'occurrences',n)
    obj._poison=lambda:setattr(obj,'poisoned',True)
    return obj


def close_numeric(n):
    for fd in (n.origins_fd,n.batches_fd,n.fd):os.close(fd)


def fixture(tmp_path, batches=2):
    j=journal(tmp_path/'parent');n=numeric(j.root)
    descriptor={'test':'deterministic-three-batch'}
    contract=dict(source_sha256='a'*64,config_sha256='b'*64,dictionary_sha256='c'*64,graph_hash='d'*64,
                  node_order_hash='e'*64,descriptor_sha256=digest(body(descriptor)),workflow_identity='tiny',cells=6,batch_cells=2)
    decoded=[]
    for index in range(batches):
        start=2*index
        tasks=iter([({'ordinal':ordinal},None,None) for ordinal in range(start,start+2)])
        j.run_batch_stream(2,tasks,lambda a,b,k:(0.25,1,'temperature_complete'),descriptor)
        origins=b''.join(ne.RECORD.pack(0,ordinal) for ordinal in range(start,start+2))
        summary=body(dict(format=ne.FORMAT,batch=index,start=start,stop=start+2,computed=2,reused=0,
                          origin_sha256=digest(origins),receipt_sha256='a'*64,receipt_framing='u64be-length/canonical-json-newline',
                          counters={'calls':index+1},elapsed_seconds=0.0,old_per_occurrence_execution_credit=False))
        n.import_completed_batch(origins,summary)
        commit=c.commit_batch(j,n,digest(body(contract)))
        blobs=tuple(j._read(f'{index:08d}'+s)[0] for s in c.SUFFIXES)+(origins,summary,commit)
        decoded.append((blobs,c._decode_batch(blobs,index,start,2,6,contract)))
    return j,n,contract,decoded


def test_complete_prefix_restores_exact_order_origins_and_is_single_use(tmp_path):
    j,n,contract,batches=fixture(tmp_path)
    successor=journal(tmp_path/'successor');new=numeric(successor.root);delivered=[]
    prefix=c.CompletedPrefix('failed','fresh','tiny',contract['graph_hash'],4,tuple(b for _,b in batches),
        n.origin_hash.hexdigest(),'f'*64,digest(body(contract)),(('attempts',1),),'9'*64)
    # Explicit parser-only synthetic seal. No fake Run crosses verify_prefix.
    c._VERIFIED[prefix]=tuple(getattr(prefix,f.name) for f in fields(prefix))
    try:
        c.restore_prefix(prefix,successor,new,lambda *args:delivered.append(args))
        assert [r[0] for r in delivered]==[0,1,2,3]
        assert os.pread(new.origins_fd,36,0)==os.pread(n.origins_fd,36,0)
        assert new.memo.occurrences==successor.cells==4
        assert new.memo.executor.checkpoints==0
        assert new.continuation['spent_counters']=={'attempts':1}
        assert new.continuation['memo_reset_count']==1
        with pytest.raises(ValueError,match='verified unused'):c.restore_prefix(prefix,successor,new,lambda *args:None)
    finally:
        j.close();successor.close();close_numeric(n);close_numeric(new)


@pytest.mark.parametrize('index',range(6))
def test_corrupt_each_recovered_body_refused(tmp_path,index):
    j,n,contract,batches=fixture(tmp_path,1)
    try:
        blobs=list(batches[0][0]);blobs[index]=blobs[index][:-1]+b'!'
        with pytest.raises((ValueError,KeyError,UnicodeError)):
            c._decode_batch(tuple(blobs),0,0,2,6,contract)
    finally:j.close();close_numeric(n)


@pytest.mark.parametrize('field',['descriptor_sha256','source_sha256','config_sha256','dictionary_sha256','graph_hash','node_order_hash'])
def test_wrong_contract_refused(tmp_path,field):
    j,n,contract,batches=fixture(tmp_path,1)
    try:
        contract[field]='0'*64
        with pytest.raises(ValueError):c._decode_batch(batches[0][0],0,0,2,6,contract)
    finally:j.close();close_numeric(n)


def test_wrong_order_and_missing_commit_refused(tmp_path):
    j,n,contract,batches=fixture(tmp_path)
    try:
        with pytest.raises(ValueError):c._decode_batch(batches[1][0],0,0,2,6,contract)
        with pytest.raises(ValueError):c._decode_batch(batches[0][0][:-1],0,0,2,6,contract)
    finally:j.close();close_numeric(n)


def test_fake_run_cannot_produce_authority():
    with pytest.raises(ValueError,match='genuine'):c.verify_prefix(SimpleNamespace(), 'input',expected_contract={})


@pytest.mark.parametrize('failed_name',['00000000.pending.json','00000000.records.tmp','00000000.complete.tmp'])
def test_score_write_crash_has_no_reusable_commit(tmp_path,failed_name):
    j=journal(tmp_path/'crash');write=j._write
    def fail(name,*args):
        if name==failed_name:raise OSError('injected write crash')
        return write(name,*args)
    j._write=fail
    try:
        with pytest.raises(OSError):j.run_batch_stream(2,iter([({'ordinal':i},None,None) for i in range(2)]),lambda *a:(0.25,1,'temperature_complete'),{})
        assert not (j.root/'00000000.prefix.json').exists()
        assert j.cells==j.batch==0
    finally:j.close()


def test_commit_failure_cannot_credit_numeric_only_batch(tmp_path):
    j,n,contract,batches=fixture(tmp_path,1)
    try:
        assert (j.root/'00000000.prefix.json').is_file()
        # An incomplete next batch has neither matching score cursor nor commit.
        n.ordinal+=1
        with pytest.raises(ValueError,match='boundary'):c.commit_batch(j,n,digest(body(contract)))
        assert not (j.root/'00000001.prefix.json').exists()
    finally:j.close();close_numeric(n)


def test_equal_forged_prefix_not_accepted(tmp_path):
    from dataclasses import replace
    j,n,contract,batches=fixture(tmp_path,1)
    p=c.CompletedPrefix('failed','fresh','tiny',contract['graph_hash'],2,(batches[0][1],),'a'*64,'b'*64,digest(body(contract)),(),'9'*64)
    c._VERIFIED[p]=tuple(getattr(p,f.name) for f in fields(p))
    forged=replace(p)
    try:
        with pytest.raises(ValueError,match='verified unused'):c.restore_prefix(forged,j,n,lambda *a:None)
        assert p in c._VERIFIED
    finally:j.close();close_numeric(n)


def test_restored_sink_failure_poisoned_and_not_reusable(tmp_path):
    j,n,contract,batches=fixture(tmp_path,1)
    dest=journal(tmp_path/'dest');new=numeric(dest.root)
    p=c.CompletedPrefix('failed','fresh','tiny',contract['graph_hash'],2,(batches[0][1],),'a'*64,'b'*64,digest(body(contract)),(),'9'*64)
    c._VERIFIED[p]=tuple(getattr(p,f.name) for f in fields(p))
    def fail(*args):raise OSError('sink failed')
    try:
        with pytest.raises(OSError,match='sink failed'):c.restore_prefix(p,dest,new,fail)
        assert dest.poisoned and new.poisoned and p not in c._VERIFIED
        with pytest.raises(ValueError):c.restore_prefix(p,dest,new,lambda *a:None)
    finally:j.close();dest.close();close_numeric(n);close_numeric(new)


def test_reconstructed_purpose_keys_required(tmp_path):
    j,n,contract,batches=fixture(tmp_path,1)
    p=c.CompletedPrefix('failed','fresh','tiny',contract['graph_hash'],2,(batches[0][1],),'a'*64,'b'*64,digest(body(contract)),(),'9'*64)
    c._VERIFIED[p]=tuple(getattr(p,f.name) for f in fields(p))
    try:
        c.verify_purposes(p,iter([({'ordinal':i},None,None) for i in range(2)]))
        with pytest.raises(ValueError,match='purpose'):
            c.verify_purposes(p,iter([({'ordinal':i,'wrong':True},None,None) for i in range(2)]))
    finally:j.close();close_numeric(n)


@pytest.mark.parametrize('target',['origins','summary','directory'])
@pytest.mark.parametrize('after',[False,True])
def test_numeric_fsync_crash_never_produces_prefix_commit(tmp_path,monkeypatch,target,after):
    j=journal(tmp_path/'crash');n=numeric(j.root)
    origins=b''.join(ne.RECORD.pack(0,i) for i in range(2))
    summary=body(dict(batch=0,start=0,stop=2,origin_sha256=digest(origins),elapsed_seconds=0.0,computed=2,reused=0))
    original=os.fsync
    def fsync(fd):
        selected=(fd==n.origins_fd if target=='origins' else fd==n.batches_fd if target=='directory' else fd not in (n.origins_fd,n.batches_fd,n.fd,j.fd))
        if selected and not after:raise OSError('fsync crash')
        original(fd)
        if selected and after:raise OSError('fsync crash')
    monkeypatch.setattr(os,'fsync',fsync)
    try:
        with pytest.raises(OSError):n.import_completed_batch(origins,summary)
        assert not (j.root/'00000000.prefix.json').exists()
        assert n.batch==0
    finally:j.close();close_numeric(n)


def test_optional_phase_totals_validation():
    from tradingagents.research.onchain_replication.phase_timing import PhaseTotals
    value=PhaseTotals().snapshot();ne.validate_phase_totals(value)
    value['numeric_counts']['arbitrary']=1
    with pytest.raises(ValueError):ne.validate_phase_totals(value)


@pytest.mark.parametrize('streamed,real_memo,complete',[(False,False,False),(True,False,False),(True,True,False),(True,True,True)])
def test_three_batch_driver_continuation_matches_uninterrupted_and_finishes(tmp_path,monkeypatch,streamed,real_memo,complete):
    import struct
    from tests.research.onchain_replication.test_matching_reference import graph
    from tradingagents.research.onchain_replication import batched_driver as driver
    from tradingagents.research.onchain_replication import adaptive_edge_policy,compiled_normalization_policy,compiled_edge_owner,matching_numeric_policy
    from tradingagents.research.onchain_replication.neighborhoods import graph_hash,node_order_hash
    from tradingagents.research.onchain_replication.array_neighborhoods import ArrayNeighborhoodIndex
    class Memo:
        def __init__(self,*args,**kwargs):
            for module in (adaptive_edge_policy,compiled_normalization_policy,compiled_edge_owner,matching_numeric_policy):module.attach(self,None)
            self.active=False;self.occurrences=0;self.counters={'calls':0};self.poisoned=False
            self.executor=SimpleNamespace(checkpoints=0,reserved_bytes=0,completed_operations=0,advance_calls=0,abandoned_call_operation_limit=0)
        def begin_batch(self):self.active=True
        def end_batch(self):self.active=False
        def restore_ordinal(self,n):assert self.occurrences==0;self.occurrences=n
        def _poison(self):self.poisoned=True;self.active=False
        def close(self):pass
        def __call__(self,a,b,purpose):
            ordinal=self.occurrences;score=float(.25+.01*float(a.node_features[0,0]));self.occurrences+=1;self.counters['calls']+=1
            self.executor.completed_operations+=2;self.executor.advance_calls+=1
            self.last_receipt=dict(schema_version=2,kind='engineering_numeric_occurrence',ordinal=ordinal,purpose_sha256=purpose,
                mode='computed',origin_purpose_sha256=purpose,origin_ordinal=ordinal,score_f64_be=struct.pack('>d',score).hex(),
                iterations=1,convergence='temperature_complete',cached=False,checkpoint_attempt_delta=0,checkpoint_reserved_byte_delta=0,
                retained_cache_bytes=0,old_per_occurrence_execution_credit=False,boundary_validated_batch_complete=False)
            return score,1,'temperature_complete'
    if not real_memo:monkeypatch.setattr(ne.reuse,'NumericReuseExecutor',Memo)
    from tests.research.onchain_replication.test_matching_reference import config as actual_config
    from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY as actual_policy
    actual_schedule=dict(max_checkpoints=2,calls_per_checkpoint=10,operations_per_call=1024,max_total_checkpoints=10,max_total_checkpoint_bytes=4*1024**2)
    g=graph([[0.],[1.],[2.]],[]);extract={'hop_depth':0,'maximum_neighborhood_nodes':3}
    with ArrayNeighborhoodIndex(g,max_buffer_bytes=100000,edge_chunk=4) as index:motif=index.neighborhood(0,extract)
    dictionary=SimpleNamespace(representatives=(motif,)*32,config=extract)
    descriptor=dict(rows=3,cells=96,motifs=32,graph_hash=graph_hash(g),node_order_hash=node_order_hash(g.node_ids),workload_sha256='1'*64,purpose_schema_version=2)
    batch_size=40 if complete else 32;parent_batches=3 if complete else 2;imported=96 if complete else 64
    contract=dict(source_sha256='a'*64,config_sha256='b'*64,dictionary_sha256='c'*64,graph_hash=descriptor['graph_hash'],node_order_hash=descriptor['node_order_hash'],descriptor_sha256=digest(body(descriptor)),workflow_identity='tiny',cells=96,batch_cells=batch_size,numerical_contract_sha256='f'*64)
    import time
    boundaries={}
    def make(name):
        times=[time.perf_counter()];boundaries[name]=times
        j=BatchJournal(tmp_path/name,batch_cells=batch_size,max_cells=96,max_bytes=100000,max_body_bytes=8192,boundary=lambda:times.append(time.perf_counter()))
        n=ne.NumericExecution(j.root,actual_config()|{'max_iterations':1} if real_memo else {}, actual_policy if real_memo else {}, actual_schedule if real_memo else {}, lambda *a:None,cells=96,batch_cells=batch_size,max_origin_bytes=864,max_summary_bytes=25000,max_entries=2,max_retained_bytes=4096,max_key_bytes=2048,
            numeric_kernel_policy=dict(matching_numeric_policy.POLICY) if real_memo and name=='successor-full' else None)
        output=bytearray(384)
        def consumer(ordinal,center,motif,payload):output[ordinal*4:ordinal*4+len(payload)]=payload
        return j,n,output,consumer
    def drive(j,n,consumer,**kw):
        actual_descriptor=kw.pop('actual_descriptor',descriptor)
        return driver.drive(g,dictionary,descriptor=actual_descriptor,policy={'max_buffer_bytes':100000,'edge_chunk':4,'extraction_limit':3},
            journal=j,executor=n,numeric=n,consumer=consumer,max_chunk_bytes=128,max_closure_token_bytes=4096,
            continuation_contract_sha256=contract['numerical_contract_sha256'],**kw)
    baseline,bn,expected,bc=make('baseline')
    drive(baseline,bn,bc);baseline_binding=bn.finish();bn.close()
    parent,pn,partial,pc=make('parent-full')
    def stop(j,b,*args):
        if b==parent_batches-1:raise RuntimeError('synthetic stop after durable batches')
    with pytest.raises(RuntimeError,match='synthetic stop'):drive(parent,pn,pc,post_batch=stop,final_batches=lambda *a:None)
    batches=[]
    for i in range(parent_batches):
        start=i*batch_size;width=min(batch_size,96-start)
        blobs=tuple((parent.root/(f'{i:08d}'+s)).read_bytes() for s in c.SUFFIXES)
        blobs+=(os.pread(pn.origins_fd,9*width,9*start),(parent.root/'numeric-batches'/f'{i:012d}.json').read_bytes(),(parent.root/f'{i:08d}.prefix.json').read_bytes())
        batches.append(c._decode_batch(blobs,i,start,batch_size,96,contract))
    pn.close()
    prefix=c.CompletedPrefix('failed','fresh','tiny',contract['graph_hash'],imported,tuple(batches),'a'*64,'b'*64,contract['numerical_contract_sha256'],(('attempts',1),),'9'*64,((digest(body(descriptor)),body(descriptor)),))
    reader=None
    if streamed:
        from dataclasses import replace
        recovered={};refs=[]
        for i,batch in enumerate(batches):
            row=[]
            for k,raw in enumerate(batch.score_bodies+(batch.origins,batch.summary,batch.commit)):
                role=f'b{i}-r{k}';recovered[role]=raw;row.append((role,digest(raw)))
            refs.append(tuple(row))
        class Reader:
            def __init__(self):self.reads=0
            def read_inputs(self,names,**bounds):
                assert bounds=={'max_each_bytes':1024**2,'max_total_bytes':4*1024**2}
                self.reads+=1;return {name:recovered[name] for name in names}
        reader=Reader();manifest=body({})
        prefix=replace(prefix,batches=tuple(refs),manifest_sha256=digest(manifest))
        c._READERS[prefix]=(reader,body(contract),False,'test-manifest')
        # Explicit synthetic already-verified grant: this exercises stream I/O
        # and restoration, never claims genuine lifecycle admission.
        def input_fixture(run,name,**bounds):
            assert run is reader and name=='test-manifest';return manifest
        def authority_fixture(run,value):assert run is reader and value=={}
        monkeypatch.setattr(c,'_bounded_input',input_fixture)
        monkeypatch.setattr(c,'_authority',authority_fixture)
    c._VERIFIED[prefix]=tuple(getattr(prefix,f.name) for f in fields(prefix))
    successor,sn,actual,sc=make('successor-full')
    successor_descriptor={**descriptor,'workload_sha256':'2'*64}
    result=drive(successor,sn,sc,completed_prefix=prefix,actual_descriptor=successor_descriptor)
    binding=sn.finish()
    assert actual==expected and result['completed_cells']==96
    assert binding['origin_sha256']==baseline_binding['origin_sha256']
    assert (successor.root/'00000000.pending.json').read_bytes()==(parent.root/'00000000.pending.json').read_bytes()
    assert json.loads((successor.root/'00000002.pending.json').read_bytes())['workload_sha256']==digest(body(descriptor if complete else successor_descriptor))
    assert binding['continuation']['imported_cells']==imported
    assert binding['continuation']['newly_computed']==(0 if complete else 1 if real_memo else 32)
    if complete:assert binding['continuation']['new_operation_counters']['advance_calls']==0
    assert binding['continuation']['memo_reset_count']==1
    assert ('numeric_kernel_policy' in binding)==real_memo
    assert ne.verify(sn.root,binding)['cells']==96
    if streamed:assert reader.reads==parent_batches*2
    sn.close()
    if real_memo:
        gaps={name:max((b-a for a,b in zip(values,values[1:])),default=0.) for name,values in boundaries.items()}
        print('SYNTHETIC_SAFE_POINT_DELAYS '+json.dumps(gaps,sort_keys=True))


def test_registered_descriptor_reader_refuses_oversize_before_read(tmp_path,monkeypatch):
    path=tmp_path/'oversize';path.write_bytes(b'12345')
    run=SimpleNamespace(admission=SimpleNamespace(root=tmp_path,inputs={'x':{'path':'oversize','sha256':digest(b'12345')}}))
    def no_read(*args):raise AssertionError('must inspect size before reading')
    monkeypatch.setattr(os,'read',no_read)
    with pytest.raises(ValueError,match='type/size/device'):c._registered_body(run,'x',4)


@pytest.mark.parametrize('redirect',['symlink','hardlink'])
def test_registered_descriptor_reader_refuses_redirects(tmp_path,redirect):
    source=tmp_path/'source';source.write_bytes(b'1234');path=tmp_path/'body'
    if redirect=='symlink':path.symlink_to(source)
    else:os.link(source,path)
    run=SimpleNamespace(admission=SimpleNamespace(root=tmp_path,inputs={'x':{'path':'body','sha256':digest(b'1234')}}))
    with pytest.raises(ValueError):c._registered_body(run,'x',4)


def test_streamed_registered_batch_rereads_mutation_and_does_not_retain_bodies(tmp_path):
    j,n,contract,batches=fixture(tmp_path,1)
    blobs=batches[0][0];mapping={f'r{i}':b for i,b in enumerate(blobs)}
    refs=tuple((name,digest(value)) for name,value in mapping.items());calls=[]
    class Reader:
        def read_inputs(self,names,**bounds):
            calls.append((names,bounds));return {name:mapping[name] for name in names}
    reader=Reader()
    prefix=c.CompletedPrefix('failed','fresh','tiny',contract['graph_hash'],2,(refs,),'a'*64,'b'*64,digest(body(contract)),(),'9'*64)
    c._READERS[prefix]=(reader,body(contract),False,'manifest')
    try:
        first=c._load_batch(prefix,0)
        assert first.records==batches[0][1].records
        assert all(type(item) is tuple and all(type(x) is str for x in item) for item in prefix.batches[0])
        mapping['r1']=mapping['r1'][:-1]+b'!'
        with pytest.raises(ValueError,match='body changed'):c._load_batch(prefix,0)
        assert len(calls)==2 and calls[0][1]=={'max_each_bytes':1024**2,'max_total_bytes':4*1024**2}
    finally:j.close();close_numeric(n)


def test_legacy_requires_actual_counter_body_and_never_synthesizes_commit(tmp_path):
    j,n,contract,batches=fixture(tmp_path,1)
    blobs=list(batches[0][0]);counter=json.loads(blobs[5]);counter['policy']='legacy-recovered-prefix-v1';blobs[5]=body(counter)
    legacy=c._decode_batch(tuple(blobs),0,0,2,6,contract,legacy=True)
    prefix=c.CompletedPrefix('failed','fresh','tiny',contract['graph_hash'],2,(legacy,),'a'*64,'b'*64,digest(body(contract)),(),'9'*64)
    c._VERIFIED[prefix]=tuple(getattr(prefix,f.name) for f in fields(prefix))
    dest=journal(tmp_path/'legacy');new=numeric(dest.root)
    try:
        c.restore_prefix(prefix,dest,new,lambda *a:None)
        assert not (dest.root/'00000000.prefix.json').exists()
        assert (dest.root/'00000000.legacy-prefix-counter.json').read_bytes()==blobs[5]
        counter.pop('operation_counters');blobs[5]=body(counter)
        with pytest.raises(ValueError):c._decode_batch(tuple(blobs),0,0,2,6,contract,legacy=True)
    finally:j.close();dest.close();close_numeric(n);close_numeric(new)


@pytest.mark.parametrize('selected',[None,'v1','v2'])
def test_actual_numeric_constructor_source_guard_and_complete_pair(tmp_path,selected):
    from tests.research.onchain_replication.test_matching_reference import config
    from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY
    from tradingagents.research.onchain_replication.contracts import AttributedGraph
    from tradingagents.research.onchain_replication.matching_numeric_policy import POLICY as KERNEL_POLICY, CACHE_POLICY
    from tradingagents.research.onchain_replication.phase_timing import PhaseTotals,activate
    import numpy as np
    graph=AttributedGraph(('0',),np.array([[0.]]),np.empty((2,0),dtype=np.int64),np.empty((0,1)), 'a'*64,'0')
    schedule=dict(max_checkpoints=2,calls_per_checkpoint=10,operations_per_call=1024,max_total_checkpoints=2,max_total_checkpoint_bytes=1024**2)
    root=tmp_path/'real-numeric';root.mkdir();totals=PhaseTotals()
    selected_policy=None if selected is None else dict(CACHE_POLICY if selected=='v2' else KERNEL_POLICY)
    with activate(totals):
        numeric=ne.NumericExecution(root,config()|{'max_iterations':1},POLICY,schedule,lambda *args:None,
            cells=1,batch_cells=1,max_origin_bytes=9,max_summary_bytes=8192,max_entries=2,max_retained_bytes=4096,max_key_bytes=2048,
            numeric_kernel_policy=selected_policy)
        try:
            score,iterations,status=numeric(graph,graph,'b'*64)
            assert score==.5 and iterations==1
            binding=numeric.finish()
            assert ne.verify(root,binding)['cells']==1
            assert numeric.memo.executor.completed_operations>0 and numeric.memo.executor.advance_calls>0
            summary=json.loads((root/'numeric-batches'/'000000000000.json').read_bytes())
            ne.validate_phase_totals(summary['phase_totals'])
            assert ('numeric_kernel_policy' in binding)==(selected is not None)
            if selected is not None:assert binding['numeric_kernel_policy']==selected_policy
        finally:numeric.close()


@pytest.mark.parametrize('after',[False,True])
def test_prefix_commit_fsync_failure_cannot_credit_next_batch(tmp_path,monkeypatch,after):
    j,n,contract,batches=fixture(tmp_path,1)
    # First completed commit remains immutable; the next marker cannot be
    # credited while only an attempted next numeric write exists.
    original=os.fsync
    def failure(fd):
        if after:original(fd)
        raise OSError('commit durability failure')
    monkeypatch.setattr(os,'fsync',failure)
    try:
        with pytest.raises(OSError):j._write('00000001.prefix.json',b'partial',8192)
        assert (j.root/'00000000.prefix.json').read_bytes()==batches[0][0][5]
        with pytest.raises(ValueError):
            incomplete=list(batches[0][0]);incomplete[5]=(j.root/'00000001.prefix.json').read_bytes()
            c._decode_batch(tuple(incomplete),1,2,2,6,contract)
    finally:j.close();close_numeric(n)


def test_retained_partial_operations_cannot_be_refunded():
    completed={'completed_operations':100,'checkpoint_attempts':2}
    partial={'completed_operations':9,'checkpoint_attempts':1}
    with pytest.raises(ValueError,match='refund'):
        c._check_spent({'completed_operations':108,'checkpoint_attempts':3},partial,completed)
    with pytest.raises(ValueError,match='refund'):
        c._check_spent({'completed_operations':109,'checkpoint_attempts':2},partial,completed)
    c._check_spent({'completed_operations':109,'checkpoint_attempts':3},partial,completed)
