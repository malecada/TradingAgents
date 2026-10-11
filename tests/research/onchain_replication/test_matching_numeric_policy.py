"""Finite synthetic selection tests; no lifecycle or native launcher."""
import numpy as np
import pytest
from tradingagents.research.onchain_replication import matching_numeric_policy as policy
from tradingagents.research.onchain_replication.matching_reference import agreement


def frozen(a, dtype=np.float64):
    a=np.asarray(a,dtype=dtype)
    return np.frombuffer(a.tobytes(),dtype=dtype).reshape(a.shape)


def test_bounded_indices_and_threshold():
    adapter=policy.NumericAgreementAdapter(policy.POLICY)
    a=frozen([[.1,.3],[.2,.7]]);indices=np.arange(1024,dtype=np.int64)%2
    out=np.full(1024,-1.)
    for count in (8,255):
        assert not adapter.fill(out,a,a,indices,indices,count,agreement,[0])
        assert np.all(out==-1)
    assert adapter.fill(out,a,a,indices,indices,1024,agreement,[0])
    assert np.all(out==.5)
    assert adapter.snapshot()['numpy_entries']==1024


def test_policy_exact_types_and_pins():
    for bad in ({},dict(policy.POLICY,atol=1e-7),dict(policy.POLICY,max_chunk_entries=True)):
        with pytest.raises(ValueError):policy.freeze(bad)
    adapter=policy.NumericAgreementAdapter(policy.POLICY)
    adapter.policy=()
    with pytest.raises(ValueError):adapter.current()


def test_refusal_preserves_output_and_scalar_exception():
    adapter=policy.NumericAgreementAdapter(policy.POLICY)
    a=frozen([[1e200,0.]]);b=frozen([[0.,0.]])
    indices=np.zeros(256,dtype=np.int64);out=np.full(256,-1.)
    assert not adapter.fill(out,a,b,indices,indices,256,agreement,[0])
    assert np.all(out==-1)
    with pytest.raises(OverflowError):agreement(a[0],b[0])

from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import matching_annealing as ann
from tradingagents.research.onchain_replication.matching_immutable_session import ImmutablePairSession
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tests.research.onchain_replication.test_matching_reference import config


def graph(n,edges,offset=0.,width=2,tied=False,extreme=False):
    nodes=np.zeros((n,4)) if tied else np.arange(n*4).reshape(n,4)*.013+offset
    idx=np.asarray([(i//n,i%n) for i in range(edges)],dtype=np.int64).reshape(-1,2).T
    features=np.zeros((edges,width)) if tied else np.arange(edges*width).reshape(edges,width)*.007+offset
    if extreme:features[:]=1e150 if offset==0 else -1e150
    return AttributedGraph(tuple(map(str,range(n))),nodes,idx,features,'a'*64,'0')


def solve(a,b,c,selected,budget=1024,checkpoint=None):
    state=engine.create(a,b,c,max_state_bytes=4*1024**2)
    session=ImmutablePairSession(a,b,c,engine=engine,annealing=ann,
        numeric_kernel_policy=dict(policy.POLICY) if selected else None)
    progress=[];saved=False
    try:
        while state['phase']!='done':
            used=session.advance(state,max_operations=budget)
            progress.append((used,state['phase'],state['annealing']['phase'],state['annealing']['cursor'],state['annealing']['iterations']))
            if checkpoint is not None and not saved:
                digest=engine.save(state,checkpoint,a,b,c,max_checkpoint_bytes=4*1024**2)
                engine.close(state)
                state=engine.load(checkpoint,a,b,c,expected_sha256=digest,max_state_bytes=4*1024**2)
                saved=True
        result=engine.result(state,a,b,c)
        counts=None if session._numeric_adapter is None else session._numeric_adapter.snapshot()
        return result,progress,counts
    finally:session.close();engine.close(state)


@pytest.mark.parametrize('n,edges,width,tied,extreme',[(3,0,2,False,False),(3,7,2,False,False),(9,81,2,False,False),(9,81,4,False,False),(9,81,2,True,False),(9,81,2,False,True)])
def test_complete_solver_reference_and_cursor(n,edges,width,tied,extreme):
    a=graph(n,edges,width=width,tied=tied,extreme=extreme)
    b=graph(n,edges,offset=.03,width=width,tied=tied,extreme=extreme)
    c=config()|{'max_iterations':3}
    original,old_progress,_=solve(a,b,c,False)
    actual,progress,counts=solve(a,b,c,True)
    ref=match_reference(a,b,c)
    assert progress==old_progress
    for comparator in (original,ref):
        np.testing.assert_allclose(actual.soft_assignment,comparator.soft_assignment,atol=1e-8,rtol=1e-6)
        assert actual.score==pytest.approx(comparator.score,abs=1e-8,rel=1e-6)
    assert np.all(actual.assignment.sum(0)<=1) and np.all(actual.assignment.sum(1)<=1)
    if edges==81 and not extreme:assert counts['numpy_chunks']>0


def test_selected_checkpoint_restores_exact_selected_path(tmp_path):
    a=graph(9,81);b=graph(9,81,.03);c=config()|{'max_iterations':3}
    reference,progress,_=solve(a,b,c,True)
    restored,restored_progress,_=solve(a,b,c,True,checkpoint=tmp_path/'checkpoint')
    np.testing.assert_array_equal(restored.soft_assignment,reference.soft_assignment)
    np.testing.assert_array_equal(restored.assignment,reference.assignment)
    assert progress==restored_progress


def test_failed_chunk_preserves_completed_prefix():
    from dataclasses import replace
    a=graph(9,81);b=graph(9,81,.03)
    bad=a.edge_features.copy();bad[20]=1e200
    a=replace(a,edge_features=bad);c=config()|{'max_iterations':2}
    observed=[]
    for selected in (False,True):
        state=engine.create(a,b,c,max_state_bytes=4*1024**2)
        session=ImmutablePairSession(a,b,c,engine=engine,annealing=ann,numeric_kernel_policy=dict(policy.POLICY) if selected else None)
        with pytest.raises(OverflowError):
            while state['phase']!='done':session.advance(state,max_operations=1024)
        observed.append((state['annealing']['cursor'],state['annealing']['Q'].copy(),state['safe']))
        session.close();engine.close(state)
    assert observed[0][0]==observed[1][0]==20*81
    assert observed[0][2] is observed[1][2] is False
    np.testing.assert_allclose(observed[0][1],observed[1][1],atol=1e-8,rtol=1e-6)


def test_live_adapter_method_mutation_refuses(monkeypatch):
    a=graph(9,81);c=config()|{'max_iterations':1}
    session=ImmutablePairSession(a,a,c,engine=engine,annealing=ann,numeric_kernel_policy=dict(policy.POLICY))
    state=engine.create(a,a,c,max_state_bytes=4*1024**2)
    monkeypatch.setattr(policy.NumericAgreementAdapter,'fill',lambda *args:True)
    with pytest.raises(ValueError,match='numeric method replaced'):session.advance(state,max_operations=1024)
    assert state['safe'] is True and state['annealing']['cursor']==0
    session.close();engine.close(state)


@pytest.mark.parametrize('budget',[255,256,1023,1024,1025])
def test_operation_chunk_boundaries(budget):
    a=graph(9,81);b=graph(9,81,.03);c=config()|{'max_iterations':1}
    old,op,_=solve(a,b,c,False,budget=budget)
    new,np_,_=solve(a,b,c,True,budget=budget)
    assert op==np_
    np.testing.assert_allclose(old.soft_assignment,new.soft_assignment,atol=1e-8,rtol=1e-6)
    assert old.score==pytest.approx(new.score,abs=1e-8,rel=1e-6)


def test_telemetry_does_not_change_result():
    from tradingagents.research.onchain_replication import phase_timing
    a=graph(9,81);b=graph(9,81,.03);c=config()|{'max_iterations':1}
    old,op,_=solve(a,b,c,True)
    totals=phase_timing.PhaseTotals()
    with phase_timing.activate(totals):new,np_,_=solve(a,b,c,True)
    assert op==np_
    np.testing.assert_array_equal(old.soft_assignment,new.soft_assignment)
    assert totals.snapshot()['numeric_counts']['agreement_numpy_entries']>0
    assert totals.snapshot()['phases']['state_scan']['calls']>0


def test_direct_native_acceptance_counted_once():
    # Synthetic dispatch fixture: tests telemetry classification, not native
    # execution or authority. Actual library use is in qualification evidence.
    from tradingagents.research.onchain_replication import phase_timing
    a=graph(9,81);b=graph(9,81,.03);c=config()|{'max_iterations':1}
    state=ann.create(a,b,c,max_state_bytes=4*1024**2)
    totals=phase_timing.PhaseTotals()
    calls=[]
    def accepted(out,left,right,li,ri,count,scalar,progress):
        for i in range(count):out[i]=.5*scalar(left[li[i]],right[ri[i]])
        progress[0]=count;calls.append(count)
        return True
    with phase_timing.activate(totals):
        while state['phase']!='done':
            ann.check(state,a,b,c)
            ann._advance_checked(state,a,b,c,max_operations=1024,edge_chunk_fill=accepted)
    counts=totals.snapshot()['numeric_counts']
    assert counts['agreement_native_entries']==sum(calls)
    assert counts['agreement_native_chunks']==len(calls)


def test_numpy_success_not_misreported_as_native():
    from tradingagents.research.onchain_replication import phase_timing
    totals=phase_timing.PhaseTotals()
    with phase_timing.activate(totals):solve(graph(9,81),graph(9,81,.03),config()|{'max_iterations':1},True)
    counts=totals.snapshot()['numeric_counts']
    assert counts['agreement_numpy_entries']>0
    assert counts.get('agreement_native_entries',0)==0
