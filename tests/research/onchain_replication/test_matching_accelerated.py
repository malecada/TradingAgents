import numpy as np
import pytest
from tests.research.onchain_replication.test_matching_reference import graph,config
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tradingagents.research.onchain_replication.matching import match_batch


def test_batched_cpu_float32_parity():
    pairs=[(graph([[0],[.7]],[(0,1,.4)]),graph([[0],[.8]],[(0,1,.5)])),(graph([[.1],[.7]],[]),graph([[0],[.9],[1.2]],[(0,1,.4)]))]
    actual=match_batch(pairs,config(),'cpu')
    for (a,b),result in zip(pairs,actual):
        ref=match_reference(a,b,config())
        assert result.score==pytest.approx(ref.score,abs=1e-5,rel=1e-4)
        np.testing.assert_array_equal(result.assignment,ref.assignment)
        np.testing.assert_allclose(result.soft_assignment,ref.soft_assignment,atol=1e-5,rtol=1e-4)


def test_gpu_parity_if_available():
    import torch
    if not torch.cuda.is_available():pytest.skip('CUDA unavailable; C06 GPU evidence pending')
    a=graph([[0],[.7]],[(0,1,.4)])
    assert match_batch([(a,a)],config(),'cuda')[0].score==pytest.approx(.75,abs=1e-5,rel=1e-4)


def test_iterative_roundoff_does_not_change_tie_free_assignment():
    from dataclasses import replace
    left=replace(graph([[0],[1]],[(0,0,1),(1,0,1),(1,1,1)]),node_features=np.array([[2.923997199959756,2.131121357306771,2.183779735468542,.11380495908177168],[2.208093314522163,.41052433048985126,1.2757754686028373,.032298459433414806]]),edge_features=np.array([[1.6891679315913142,1.7840614016646477],[.012256645264611565,.3713692248356135],[1.5925255954100948,1.3060037550011354]]))
    right=replace(graph([[0],[1],[2]],[(0,1,1),(0,2,1),(1,2,1),(2,2,1)]),node_features=np.array([[.7472641472867964,.6897062654799825,1.9641323086740476,2.4332680264908837],[.0819936611723775,2.2041341518243063,2.936631910603662,1.743843880152853],[.013270876805726028,2.297030527472103,1.3699248259743853,2.696854690695402]]),edge_features=np.array([[1.9355508793220288,.9751960580257151],[1.511672984645969,1.5142386262358833],[1.7256187908828513,1.6758922511164993],[.6394688056647806,.5347504795775198]]))
    reference=match_reference(left,right,config());accelerated=match_batch([(left,right)],config(),'cpu')[0]
    np.testing.assert_array_equal(accelerated.assignment,reference.assignment)
    np.testing.assert_allclose(accelerated.soft_assignment,reference.soft_assignment,atol=1e-5,rtol=1e-4)
    assert abs(accelerated.score-reference.score)<1e-5
