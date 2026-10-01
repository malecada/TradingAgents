"""Actual admitted compact dictionary through required-graph MCM publication."""
from pathlib import Path
from types import SimpleNamespace
import json
import shutil
import pytest
import numpy as np
from tests.research.test_lifecycle import git
from tests.research.onchain_replication import test_compact_dictionary as dictionary
from tradingagents.research.onchain_replication.provenance import file_hash,thaw
from tradingagents.research.onchain_replication.neighborhoods import graph_hash,NeighborhoodIndex
from tradingagents.research.onchain_replication.matching_reference import match_reference

ROOT = Path(__file__).resolve().parents[3]
KERNEL = 'research/onchain-paper-replication-2026-09-24/full_sources/mcm-array-kernel-2026-10-01/kernel.py'


@pytest.fixture
def admitted(request,monkeypatch):
    training = dictionary.samples.publication.sampling.training
    original = training.first.Tests.fixture; option = getattr(request,'param','valid')
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            policy = {'schema_version':1,'max_entries':1000,'max_workflow_metadata_bytes':1000000,
                'numeric':{'schema_version':1,'max_buffer_bytes':65536,'edge_chunk':2,
                    'max_output_bytes':4000,'max_numeric_bytes':69536}}
            output = {'schema_version':1,'backend':t.item['native_backend'],
                'max_artifact_bytes':12192,'max_workflow_output_bytes':1000000}
            if option == 'numeric': policy['numeric']['max_numeric_bytes'] = 1
            if option == 'budget': output['max_workflow_output_bytes'] = 1
            t.input('compact_mcm',policy); t.input('compact_mcm_output',output)
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item.update(compact_mcm_input='compact_mcm',compact_mcm_output_input='compact_mcm_output')
            if option == 'route': t.item['compact_mcm_input'] = 'sample'
            target = t.root/KERNEL; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/KERNEL,target); git(t.root,'add','--',KERNEL)
            if option != 'source': t.exp['source_files'][KERNEL] = file_hash(target)
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen = dictionary.admitted.__wrapped__(SimpleNamespace(param='valid'),monkeypatch)
    proof,t = next(gen)
    try: yield dictionary.api().produce(proof,input_name='compact_dictionary'),t
    finally:
        try: next(gen)
        except StopIteration: pass


def api():
    from tradingagents.research.onchain_replication import compact_mcm
    return compact_mcm


def target(produced):
    training = produced._proof._published._draws._training
    key = training.descriptor['required_graphs'][0]
    return key,next(g for g in training.graphs if graph_hash(g) == key)


def test_actual_required_graph_mcm_matches_scalar_and_saved_scores(admitted):
    produced,t = admitted; m = api(); key,g = target(produced)
    d = produced.dictionary; matching = thaw(produced._proof.owner.matching)
    reference = np.asarray([[match_reference(NeighborhoodIndex(g).neighborhood(i,d.config),motif,matching).score
        for motif in d.representatives] for i in range(len(g.node_ids))],dtype=np.float32)
    result = m.produce(produced,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
    result.check(); np.testing.assert_array_equal(result.matrix,reference)
    assert result.record['completed_cells'] == reference.size
    assert result.record['dictionary_receipt_sha256'] == produced.receipt_sha256
    assert result.record['representation_admitted'] is False
    assert result.record['graph_hash'] == key
    assert (result.directory/'complete.json').exists()
    stage = produced._proof.owner.stages['mcm-'+key]
    assert stage.closed and stage.contract['pairs'] == reference.size
    with pytest.raises(ValueError): m.produce(produced,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')


@pytest.mark.parametrize('admitted',['numeric','budget','route','source'],indirect=True)
def test_preflight_refuses_before_mcm_stage_or_attempt(admitted):
    produced,t = admitted; m = api(); key,g = target(produced); owner = produced._proof.owner
    with pytest.raises(ValueError): m.produce(produced,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
    assert list(owner.stages) == ['dictionary'] and not owner.poisoned
    assert not m.directory(produced,key).exists()


def test_foreign_graph_cannot_consume_dictionary(admitted):
    produced,t = admitted; m = api()
    with pytest.raises(ValueError): m.produce(produced,graph_hash='f'*64,input_name='compact_mcm',output_input='compact_mcm_output')
    assert list(produced._proof.owner.stages) == ['dictionary']


def test_second_pair_failure_preserves_first_score_and_failed_attempt(admitted,monkeypatch):
    produced,t = admitted; m = api(); key,g = target(produced); calls = []; create = m.compact_matcher.engine.create
    def failed(*args,**kwargs):
        calls.append(1)
        if len(calls) == 2: raise RuntimeError('synthetic MCM second pair')
        return create(*args,**kwargs)
    monkeypatch.setattr(m.compact_matcher.engine,'create',failed)
    with pytest.raises(RuntimeError,match='second pair'): m.produce(produced,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
    owner = produced._proof.owner; root = owner.root/('mcm-'+key)
    terminal = json.loads((root/'matching/terminal.json').read_bytes())
    assert terminal['state']['completed_pairs'] == 1 and terminal['status'] == 'failed'
    assert owner.poisoned and (m.directory(produced,key)/'failed.json').is_file()
    assert not (root/'stage-complete.json').exists()


def test_seal_callback_cannot_change_returned_matrix_before_publication(admitted,monkeypatch):
    produced,t = admitted; m = api(); key,g = target(produced); owner = produced._proof.owner
    kernel = m._kernel(); original = kernel.mcm; finished = owner._finish_stage; values = []
    def fit(*args,**kwargs):
        value = original(*args,**kwargs); values.append(value['mcm']); return value
    def seal(*args,**kwargs):
        value = finished(*args,**kwargs); values[0][0,0] += .125; return value
    monkeypatch.setattr(kernel,'mcm',fit); monkeypatch.setattr(m,'_kernel',lambda:kernel)
    monkeypatch.setattr(owner,'_finish_stage',seal)
    with pytest.raises(ValueError,match='matrix'): m.produce(produced,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
    assert owner.poisoned and owner.stages['mcm-'+key].closed
    assert (m.directory(produced,key)/'failed.json').exists()


def test_final_live_callback_cannot_hide_changed_completed_stage(admitted,monkeypatch):
    produced,t = admitted; m = api(); key,g = target(produced); lease = produced.lease
    def changed():
        lease()
        if (m.directory(produced,key)/'complete.json').exists():
            (produced._proof.owner.root/('mcm-'+key)/'orphan').write_bytes(b'retained')
    monkeypatch.setattr(produced,'lease',changed)
    with pytest.raises(ValueError): m.produce(produced,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
    assert produced._proof.owner.poisoned


def test_nested_cleanup_uncertainty_remains_fatal_through_producer(admitted,monkeypatch):
    produced,t = admitted; m = api(); key,g = target(produced)
    holder={}; construct=m.MCMScoreStream; real_close=m.os.close; broken=[]
    def build(*args,**kwargs):
        obj=construct(*args,**kwargs);holder['stream']=obj;return obj
    def create(*args,**kwargs):
        broken.append(holder['stream'].active.record_fd)
        raise RuntimeError('synthetic primary MCM construction')
    def close(fd):
        if fd in broken:raise OSError('synthetic retained tail descriptor')
        real_close(fd)
    monkeypatch.setattr(m,'MCMScoreStream',build)
    monkeypatch.setattr(m.compact_matcher.engine,'create',create)
    monkeypatch.setattr(m.os,'close',close)
    try:
        with pytest.raises(m.io.CleanupFailure) as caught:
            m.produce(produced,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
        assert isinstance(caught.value.__cause__,RuntimeError)
        assert produced._proof.owner.poisoned and (m.directory(produced,key)/'failed.json').exists()
        obj=holder['stream'];assert obj.closed and obj.batches.closed and obj.active.closed
        for fd in (obj.fd,obj.batches.fd,obj.active.fd):
            with pytest.raises(OSError):m.os.fstat(fd)
    finally:
        # The injected error deliberately did not release this fixture-owned fd.
        # Only the test harness closes it; production performs no uncertain retry.
        for fd in broken:real_close(fd)


@pytest.mark.parametrize('mode',['success','failure'])
def test_final_producer_descriptor_close_is_fatal_and_releases_lock(admitted,monkeypatch,mode):
    produced,t = admitted; m=api(); key,g=target(produced); owner=produced._proof.owner
    root=m.directory(produced,key); opened=m.io._open; real_close=m.os.close; captured=[]
    def opening(path):
        value=opened(path)
        if Path(path)==root and not captured:captured.append(value[1])
        return value
    def close(fd):
        if captured and fd==captured[0]:raise OSError('synthetic retained producer descriptor')
        real_close(fd)
    def fail(*args,**kwargs):raise RuntimeError('synthetic primary numerical failure')
    monkeypatch.setattr(m.io,'_open',opening);monkeypatch.setattr(m.os,'close',close)
    if mode=='failure':monkeypatch.setattr(m.compact_matcher.engine,'create',fail)
    try:
        with pytest.raises(BaseException) as caught:
            m.produce(produced,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
        assert not isinstance(caught.value,Exception),'root close masked fatal uncertainty'
        assert owner.poisoned and (root/'failed.json').exists()
        if mode=='failure':assert isinstance(caught.value.__cause__,RuntimeError)
        assert owner._transition.acquire(blocking=False),'root close skipped lock release'
        owner._transition.release()
    finally:
        for fd in captured:real_close(fd)
