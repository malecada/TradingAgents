"""Unselected one-pair retention primitive; real engine, disposable local roots."""
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pytest

from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import restart_retention as m
from tradingagents.research.onchain_replication.provenance import thaw
from tests.research.onchain_replication.test_matching_reference import graph, config

POLICY=dict(max_state_bytes=1048576,normalization_chunk_entries=8,
    hardening_chunk_entries=2,hardening_buffer_bytes=10000,max_checkpoint_bytes=262144)
LIMITS=dict(max_generations=8,max_generation_bytes=262144,max_control_bytes=1048576,
    max_cumulative_bytes=4194304,max_replay_bytes=262144,max_replays=1)
BINDINGS={key:hashlib.sha256(key.encode()).hexdigest() for key in ('owner','stage','source','runtime','policy')}


def body(value):return (json.dumps(thaw(value),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def fixture(tmp_path):
    a=graph([[0.],[1.]],[]);b=graph([[0.],[1.]],[]);c=config()|{'max_iterations':1}
    identity=engine.ann.identity(a,b,c)
    pair=dict(ordinal=0,purpose_sha256='a'*64,numeric_identity=identity)
    states=[]
    def state():
        s=engine.create(a,b,c,**{k:POLICY[k] for k in engine.POLICY_FIELDS});states.append(s);return s
    event_root=tmp_path/'events';event_root.mkdir()
    def publish(expected):
        path=event_root/f'{len(list(event_root.iterdir())):04d}.json'
        with path.open('xb') as f:f.write(body(expected));f.flush();os.fsync(f.fileno())
        return m.EventRef(path,sha(body(expected)))
    def store(**changes):
        options=dict(bindings=BINDINGS,pair=pair,policy=POLICY,limits=LIMITS,replay_first=True,lease=lambda:None)
        options.update(changes)
        return m.Store(tmp_path/'store',**options)
    yield a,b,c,state,publish,store
    for s in states:
        if s['safe']:engine.close(s)


def finish_engine(s,a,b,c):
    for _ in range(1000):
        if s['phase']=='done':return engine.result(s,a,b,c)
        engine.advance(s,a,b,c,max_operations=1)
    raise AssertionError('tiny fixture did not finish')


def completed(store,result):
    return dict(schema_version=1,kind='complete',pair=dict(store.pair),
        event_ordinal=store.generations+1,score=result.score,
        convergence=result.convergence,iterations=result.iterations)


def test_three_rotations_replay_before_retirement_and_independent_score(fixture):
    a,b,c,state,publish,create=fixture;s=state();baseline=state();store=create();proofs=[]
    for _ in range(3):
        engine.advance(s,a,b,c,max_operations=1)
        proofs.append(store.checkpoint(s,a,b,c,publish_progress=publish))
    assert store.generations==3 and store.spent['generations']==3
    for p in proofs[:-1]:
        assert p['body_available'] is True  # immutable original observation
        with pytest.raises(ValueError):store.body_path(p['generation'])
    replay=store.replay_path(0)
    loaded=engine.load(replay,a,b,c,expected_sha256=proofs[0]['state_sha256'],
        **{k:POLICY[k] for k in engine.POLICY_FIELDS})
    try:replayed=finish_engine(loaded,a,b,c)
    finally:engine.close(loaded)
    actual=finish_engine(s,a,b,c);reference=finish_engine(baseline,a,b,c)
    # Literal zero-edge input: injective diagonal contributes two unit node terms / 2 / 2.
    np.testing.assert_array_equal(actual.assignment,np.eye(2,dtype=np.int8))
    assert actual.score==.5 and actual.iterations==1 and actual.convergence=='iteration_cap'
    assert (actual.score,actual.iterations,actual.convergence)==(reference.score,reference.iterations,reference.convergence)
    assert replayed.score==actual.score
    assert sha(actual.soft_assignment.tobytes())==sha(reference.soft_assignment.tobytes())
    expected=completed(store,actual);event=publish(expected)
    terminal=store.finish(event,expected=expected)
    store.lease=lambda:(_ for _ in ()).throw(AssertionError('terminal live callback'))
    result=m.verify(store.root,expected_claim=store.claim_sha256,expected_terminal=terminal)
    assert result['retired']==(0,1,2) and result['replays']==(0,)
    assert result['execution_admitted'] is False
    assert store.spent['generations']==3
    with pytest.raises(ValueError):store.checkpoint(s,a,b,c,publish_progress=publish)
    assert m.reconcile(store.root,expected_claim=store.claim_sha256)['restart_permitted'] is False
    (store.root/'terminal.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError):m.verify(store.root,expected_claim=store.claim_sha256,expected_terminal=terminal)


@pytest.mark.parametrize('field,value',[('score',.4),('iterations',2),('convergence','temperature_complete'),('event_ordinal',99),('pair',{})])
def test_completion_requires_independent_exact_event(fixture,field,value):
    a,b,c,state,publish,create=fixture;s=state();store=create()
    store.checkpoint(s,a,b,c,publish_progress=publish);result=finish_engine(s,a,b,c)
    expected=completed(store,result);wrong=expected|{field:value}
    with pytest.raises(ValueError):store.finish(publish(wrong),expected=expected)
    assert store.poisoned and store.body_path(0,inspect_failed=True).is_dir()
    assert not (store.root/'terminal.json').exists()


@pytest.mark.parametrize('fault',['extra','short','hardlink','symlink','replacement'])
def test_real_snapshot_corruption_after_callback_refused(fixture,fault):
    a,b,c,state,publish,create=fixture;s=state();store=create(replay_first=False)
    def corrupt(expected):
        ref=publish(expected);root=store.root/'generation-00000000000000000000'/'state'
        path=root/'annealing'/'M.npy'
        if fault=='extra':(root/'foreign').write_bytes(b'x')
        elif fault=='short':path.write_bytes(b'x')
        elif fault=='hardlink':os.link(path,root.parent/'borrowed')
        elif fault=='symlink':path.unlink();path.symlink_to(root/'annealing'/'Q.npy')
        else:
            original=root.with_name('displaced');root.rename(original)
            import shutil
            shutil.copytree(original,root)
        return ref
    with pytest.raises(ValueError):store.checkpoint(s,a,b,c,publish_progress=corrupt)
    assert store.poisoned and not (store.root/'progress-00000000000000000000.json').exists()
    assert m.reconcile(store.root,expected_claim=store.claim_sha256)['restart_permitted'] is False


@pytest.mark.parametrize('limit',['max_generations','max_control_bytes','max_cumulative_bytes','max_replay_bytes','max_replays','max_generation_bytes'])
def test_limits_spent_before_allocation_and_never_refunded(fixture,limit):
    a,b,c,state,publish,create=fixture;s=state()
    caps=LIMITS|{limit:1};store=create(limits=caps) if limit not in ('max_control_bytes','max_cumulative_bytes') else None
    if store is None:
        with pytest.raises(ValueError):create(limits=caps)
        return
    if limit in ('max_generations','max_replays'):
        store.checkpoint(s,a,b,c,publish_progress=publish)
        if limit=='max_replays':assert store.spent['replays']==1;return
    before=dict(store.spent)
    with pytest.raises(ValueError):store.checkpoint(s,a,b,c,publish_progress=publish)
    assert store.poisoned and all(store.spent[k]>=v for k,v in before.items())


def test_fresh_namespace_only(fixture):
    *_,create=fixture;store=create()
    with pytest.raises((ValueError,FileExistsError)):create()
    assert store.generations==0


@pytest.mark.parametrize('point',['candidate_fsync','progress','replay','retire_intent','first_unlink','last_unlink',
    'retire_complete','parent_fsync','descriptor_close','completion','terminal'])
def test_failure_matrix_never_acknowledges_or_restarts(fixture,monkeypatch,point):
    a,b,c,state,publish,create=fixture;s=state();store=create();primary=OSError('injected '+point)
    # Rotation faults start with one verified body and its retained FIRST replay.
    if point.startswith('retire') or point in ('first_unlink','last_unlink'):
        store.checkpoint(s,a,b,c,publish_progress=publish)
    previous=dict(store.spent);fired=[]
    original_write=m._write_bytes;original_fsync=os.fsync;original_unlink=os.unlink;original_close=os.close
    def fail():fired.append(point);raise primary
    def write(path,raw):
        names={'progress':'progress-','replay':'replay-','retire_intent':'-intent.json',
            'retire_complete':'-complete.json','completion':'completion.json','terminal':'terminal.json'}
        needle=names.get(point)
        if not fired and needle and needle in path.name:fail()
        return original_write(path,raw)
    def sync(fd):
        name=os.readlink(f'/proc/self/fd/{fd}')
        if not fired and ((point=='candidate_fsync' and name.endswith('/annealing/M.npy'))
            or (point=='parent_fsync' and name==str(store.root))):fail()
        return original_fsync(fd)
    unlinks=[]
    def unlink(path,*args,**kwargs):
        if point in ('first_unlink','last_unlink') and not fired:
            unlinks.append(path)
            if len(unlinks)==(1 if point=='first_unlink' else 3):fail()
        return original_unlink(path,*args,**kwargs)
    def close(fd):
        name=os.readlink(f'/proc/self/fd/{fd}')
        result=original_close(fd)
        if point=='descriptor_close' and not fired and name==str(store.root):fail()
        return result
    monkeypatch.setattr(m,'_write_bytes',write);monkeypatch.setattr(os,'fsync',sync)
    monkeypatch.setattr(os,'unlink',unlink);monkeypatch.setattr(os,'close',close)
    with pytest.raises(BaseException) as caught:
        if point in ('completion','terminal'):
            result=finish_engine(s,a,b,c);expected=completed(store,result);store.finish(publish(expected),expected=expected)
        else:store.checkpoint(s,a,b,c,publish_progress=publish)
    assert fired and store.poisoned
    if point=='descriptor_close':assert isinstance(caught.value,m.io.CleanupFailure)
    else:assert caught.value is primary or caught.value.__cause__ is primary
    assert all(store.spent[k]>=v for k,v in previous.items())
    before={p:p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    assert m.reconcile(store.root,expected_claim=store.claim_sha256)['restart_permitted'] is False
    assert all(p.read_bytes()==raw for p,raw in before.items())
    with pytest.raises(ValueError):store.checkpoint(s,a,b,c,publish_progress=publish)
    assert all(p.read_bytes()==raw for p,raw in before.items())


def test_all_cleanup_once_preserves_primary_fatal():
    primary=m.io.CleanupFailure('original fatal');calls=[]
    def bad():calls.append('bad');raise OSError('uncertain close')
    def good():calls.append('good')
    with pytest.raises(m.io.CleanupFailure) as caught:m._cleanup((bad,good),primary)
    assert caught.value is primary and calls==['bad','good']
    assert any('uncertain close' in note for note in primary.__notes__)


@pytest.mark.parametrize('limit',['max_control_bytes','max_cumulative_bytes'])
def test_cumulative_limits_refuse_second_before_namespace_allocation(fixture,limit):
    a,b,c,state,publish,create=fixture;s=state()
    cap=2*m.CONTROL+8*m.CONTROL+(2*POLICY['max_checkpoint_bytes'] if limit=='max_cumulative_bytes' else 0)
    store=create(limits=LIMITS|{limit:cap});store.checkpoint(s,a,b,c,publish_progress=publish)
    spent=dict(store.spent)
    with pytest.raises(ValueError):store.checkpoint(s,a,b,c,publish_progress=publish)
    assert store.spent==spent and not (store.root/'generation-00000000000000000001').exists()


def test_early_completion_has_explicit_no_checkpoint_disposition(fixture):
    a,b,c,state,publish,create=fixture;store=create();result=finish_engine(state(),a,b,c)
    expected=completed(store,result);terminal=store.finish(publish(expected),expected=expected)
    result=m.verify(store.root,expected_claim=store.claim_sha256,expected_terminal=terminal)
    assert result['first_checkpoint']=='completed_before_first_scheduled_checkpoint'
    assert not result['replays'] and result['generations']==0


def test_three_body_bound_and_first_replay_precedes_any_retirement(fixture,monkeypatch):
    a,b,c,state,publish,create=fixture;s=state();store=create();observations=[]
    original=store._retire
    def retire(i,reason):
        assert store.replay_path(0).is_dir()
        observations.append(len(list(store.root.glob('generation-*/state/annealing/M.npy'))))
        return original(i,reason)
    monkeypatch.setattr(store,'_retire',retire)
    for _ in range(3):store.checkpoint(s,a,b,c,publish_progress=publish)
    assert observations==[2,2] and len(list(store.root.glob('generation-*/state/annealing/M.npy')))==1


@pytest.mark.parametrize('mutation',['missing','same_extent','cross_device'])
def test_additional_real_snapshot_corruption(fixture,monkeypatch,mutation):
    a,b,c,state,publish,create=fixture;s=state();store=create(replay_first=False)
    original=os.fstat
    def event(expected):
        ref=publish(expected);path=store.root/'generation-00000000000000000000/state/annealing/Q.npy'
        if mutation=='missing':path.unlink()
        elif mutation=='same_extent':
            raw=path.read_bytes();path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
        else:
            def altered(fd):
                value=original(fd)
                if os.readlink(f'/proc/self/fd/{fd}').endswith('/annealing'):
                    fields=list(value);fields[2]+=1;return os.stat_result(fields)
                return value
            monkeypatch.setattr(os,'fstat',altered)
        return ref
    with pytest.raises((ValueError,FileNotFoundError)):
        store.checkpoint(s,a,b,c,publish_progress=event)
    assert store.poisoned


def test_duplicate_closed_store_cannot_change_successful_terminal(fixture):
    a,b,c,state,publish,create=fixture;s=state();store=create();result=finish_engine(s,a,b,c)
    expected=completed(store,result);terminal=store.finish(publish(expected),expected=expected)
    before={p:p.read_bytes() for p in store.root.rglob('*') if p.is_file()};spent=dict(store.spent)
    with pytest.raises(ValueError):store.checkpoint(s,a,b,c,publish_progress=publish)
    assert not store.poisoned and store.spent==spent
    assert {p:p.read_bytes() for p in store.root.rglob('*') if p.is_file()}==before
    m.verify(store.root,expected_claim=store.claim_sha256,expected_terminal=terminal)


def test_reconciliation_needs_original_progress_pin_and_is_read_only(fixture):
    a,b,c,state,publish,create=fixture;store=create();proof=store.checkpoint(state(),a,b,c,publish_progress=publish)
    before={p:p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    assert m.reconcile(store.root,expected_claim=store.claim_sha256)['last_available_verified_progress'] is None
    result=m.reconcile(store.root,expected_claim=store.claim_sha256,expected_progress={0:sha(body(proof))})
    assert result['last_available_verified_progress']==0 and result['restart_permitted'] is False
    assert all(p.read_bytes()==raw for p,raw in before.items())
    with pytest.raises(ValueError):m.reconcile(store.root,expected_claim=store.claim_sha256,expected_progress={0:'0'*64})


@pytest.mark.parametrize('shape',[(3,2),(2,2)])
def test_hardening_snapshot_and_literal_directed_score(tmp_path,shape):
    import math
    n,k=shape;a=graph([[j*.3] for j in range(n)],[(0,1,.2)])
    b=graph([[j*.4] for j in range(k)],[(0,1,.4)]);c=config()|{'max_iterations':1}
    opts={key:POLICY[key] for key in engine.POLICY_FIELDS}
    s=engine.create(a,b,c,**opts);baseline=engine.create(a,b,c,**opts)
    pair=dict(ordinal=7,purpose_sha256='b'*64,numeric_identity=engine.ann.identity(a,b,c))
    bindings=BINDINGS|{'source':'c'*64,'policy':'d'*64}
    store=m.Store(tmp_path/'scratch',bindings=bindings,pair=pair,policy=POLICY,
        limits=LIMITS,replay_first=True,lease=lambda:None)
    def publish(expected):
        path=tmp_path/f'event-{expected["event_ordinal"]}.json';path.write_bytes(body(expected))
        with path.open('rb') as f:os.fsync(f.fileno())
        return m.EventRef(path,sha(body(expected)))
    try:
        store.checkpoint(s,a,b,c,publish_progress=publish)
        while s['phase']=='annealing':engine.advance(s,a,b,c,max_operations=1)
        assert s['phase']=='hardening'
        proof=store.checkpoint(s,a,b,c,publish_progress=publish)
        assert 'hardening/order.npy' in proof['tree']['files']
        actual=finish_engine(s,a,b,c);original=finish_engine(baseline,a,b,c)
        assignment=actual.assignment
        assert (assignment.sum(0)<=1).all() and (assignment.sum(1)<=1).all()
        node=sum(int(assignment[u,i])*math.exp(-(.3*u-.4*i)**2) for u in range(n) for i in range(k))/math.sqrt(n*k)
        edge=int(assignment[0,0])*int(assignment[1,1])*math.exp(-.2**2)/2
        assert actual.score==pytest.approx((node+edge)/2,abs=1e-8,rel=1e-6)
        assert (actual.score,actual.iterations,actual.convergence)==(original.score,original.iterations,original.convergence)
        np.testing.assert_array_equal(actual.assignment,original.assignment)
        assert sha(actual.soft_assignment.tobytes())==sha(original.soft_assignment.tobytes())
        assert thaw(store.claim)['bindings']==bindings and thaw(store.pair)==pair
        expected=completed(store,actual);terminal=store.finish(publish(expected),expected=expected)
        m.verify(store.root,expected_claim=store.claim_sha256,expected_terminal=terminal)
    finally:engine.close(s);engine.close(baseline)


def test_retirement_preserves_original_engine_manifest_bytes(fixture):
    a,b,c,state,publish,create=fixture;s=state();store=create()
    first=store.checkpoint(s,a,b,c,publish_progress=publish)
    root=store.body_path(0);metadata={p:p.read_bytes() for p in root.rglob('*.json')}
    store.checkpoint(s,a,b,c,publish_progress=publish)
    assert all(p.exists() and p.read_bytes()==raw for p,raw in metadata.items())
    assert not list(root.rglob('*.npy'))
    with pytest.raises((ValueError,FileNotFoundError)):
        engine.load(root,a,b,c,expected_sha256=first['state_sha256'],**{k:POLICY[k] for k in engine.POLICY_FIELDS})


def test_retained_engine_metadata_has_independent_control_reservation(fixture):
    a,b,c,state,publish,create=fixture;store=create();store.checkpoint(state(),a,b,c,publish_progress=publish)
    assert store.spent['control_bytes']>=2*m.CONTROL+8*m.CONTROL+3*engine.LIMIT
