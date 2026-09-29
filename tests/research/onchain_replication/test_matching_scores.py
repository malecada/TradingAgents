"""Synthetic parity and lifetime checks for score-only matching."""
import weakref
from dataclasses import fields
import numpy as np
import pytest
from tests.research.onchain_replication.test_matching_reference import graph,config
from tests.research.onchain_replication.test_neighborhoods import cfg
from tradingagents.research.onchain_replication import matching,mcm
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.dictionary import fit_dictionary,reorder_dictionary


def pairs():
    a=graph([[0],[.7]],[(0,1,.4)])
    b=graph([[0],[.8]],[(0,1,.5)])
    z=graph([[0],[0]],[])
    tiny=graph([[0]],[])
    return [(a,b),(graph([[.1],[.7]],[]),graph([[0],[.9],[1.2]],[(0,1,.4)])),
            (z,z),(b,a),(tiny,tiny),(a,a)]


@pytest.mark.parametrize('limit',[8,4000000])
def test_score_only_matches_legacy_and_reference_across_groups(limit):
    assert hasattr(matching,'match_scores'),'score-only consumer is missing'
    settings=config()|{'max_pair_entries':limit}
    old=matching.match_batch(pairs(),settings)
    scores=matching.match_scores(pairs(),settings)
    assert len(scores)==len(old)==6
    for pair,actual,expected in zip(pairs(),scores,old,strict=True):
        assert (actual.score,actual.iterations,actual.convergence)==(expected.score,expected.iterations,expected.convergence)
        assert actual.iterations==48 and actual.convergence=='temperature_complete'
        assert actual.score==pytest.approx(match_reference(*pair,settings).score,abs=1e-5,rel=1e-4)
        assert not any(isinstance(getattr(actual,f.name),np.ndarray) for f in fields(actual))
    assert scores[2].score==.5 and scores[4].score==.5 and scores[5].score==.75


def test_score_only_releases_assignments_and_never_constructs_diagnostics(monkeypatch):
    import torch
    assert hasattr(matching,'match_scores'),'score-only consumer is missing'
    old=matching.match_batch(pairs(),config()|{'max_pair_entries':8})
    refs=[];tensor_refs=[];assignments=[];real_harden=matching.harden;real_tensor=torch.tensor
    def tensor(value,*args,**kwargs):
        result=real_tensor(value,*args,**kwargs)
        if isinstance(value,np.ndarray) and value.dtype==np.int8:
            tensor_refs.append(weakref.ref(result))
        return result
    def harden(matrix):
        assert all(r() is None for r in refs),'earlier hard assignment still retained'
        assert all(r() is None for r in tensor_refs),'earlier hard-assignment tensor still retained'
        result=real_harden(matrix);refs.append(weakref.ref(result));assignments.append(result.copy())
        return result
    monkeypatch.setattr(matching,'harden',harden)
    monkeypatch.setattr(torch,'tensor',tensor)
    monkeypatch.setattr(matching,'MatchResult',lambda *a,**k:pytest.fail('diagnostic result allocated'))
    actual=matching.match_scores(pairs(),config()|{'max_pair_entries':8})
    assert all(r() is None for r in refs)
    assert len(tensor_refs)==6 and all(r() is None for r in tensor_refs)
    # Shape grouping processes 2x2 pairs first, then rectangular and singleton.
    for assignment,index in zip(assignments,[0,2,3,5,1,4],strict=True):
        np.testing.assert_array_equal(assignment,old[index].assignment)
    assert [s.score for s in actual]==[s.score for s in old]


def test_score_only_retains_iteration_cap_and_input_refusals():
    assert hasattr(matching,'match_scores'),'score-only consumer is missing'
    result=matching.match_scores(pairs(),config()|{'max_iterations':1})
    assert all(r.iterations==1 and r.convergence=='iteration_cap' for r in result)
    assert matching.match_scores([],config())==[]
    with pytest.raises(ValueError,match='capacity'):
        matching.match_scores(pairs(),config()|{'max_pair_entries':1})
    with pytest.raises(ValueError,match='float32 solve'):
        matching.match_scores(pairs(),config()|{'internal_precision':'float32'})


def test_mcm_score_only_preserves_features_order_and_checkpoint_resume():
    g=graph([[0],[1],[2],[3]],[(0,1,1),(2,1,2)])
    samples=sample_neighborhoods([g],cfg(),11)
    d=fit_dictionary(samples,config(),dict(size=2,partition_threshold=20,partition_size=10,hop_depth=1,maximum_neighborhood_nodes=20))
    expected=mcm.mcm_features(g,d,config())
    actual=mcm.mcm_features(g,d,config(),score_only=True)
    np.testing.assert_array_equal(actual,expected)
    reordered=reorder_dictionary(d,[1,0])
    np.testing.assert_array_equal(mcm.mcm_features(g,reordered,config(),score_only=True),expected[:,::-1])
    output=np.full_like(expected,np.nan);output[:2]=expected[:2];saved=[]
    resumed=mcm.mcm_features(g,d,config(),score_only=True,output=output,start_node=2,
        checkpoint=lambda cursor,array:saved.append((cursor,array.copy())))
    assert resumed is output and [cursor for cursor,array in saved]==[4]
    np.testing.assert_array_equal(resumed,expected)
    np.testing.assert_array_equal(saved[0][1],expected)


@pytest.mark.parametrize('reference,option',[(True,True),(False,'yes'),(False,1)])
def test_mcm_rejects_ambiguous_score_only_mode_before_graph_access(reference,option):
    with pytest.raises(ValueError,match='score-only'):
        mcm.mcm_features(None,None,None,reference=reference,score_only=option)
