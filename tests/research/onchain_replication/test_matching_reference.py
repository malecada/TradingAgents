import itertools,json,math
from pathlib import Path
import numpy as np
import pytest
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.matching_reference import harden,score_assignment,match_reference


def config():return json.loads((Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text())

def graph(x,edges):
    return GraphSnapshot('ETH','2024-01-01T00:00:00Z','2024-01-08T00:00:00Z','2024-01-09T00:00:00Z',('a'*64,),'b'*64,tuple(map(str,range(len(x)))),np.asarray(x,dtype=float).reshape(len(x),-1),np.asarray([(a,b) for a,b,v in edges],dtype=np.int64).reshape(-1,2).T,np.asarray([v for a,b,v in edges],dtype=float).reshape(len(edges),1),len(edges),len(edges),{})

def oracle(a,b,m):
    # Independently spell out Eq1 using Python scalars and supplied assignments.
    node=0.;edge=0.
    for u,i in zip(*np.nonzero(m)):
        node+=math.exp(-sum((float(x)-float(y))**2 for x,y in zip(a.node_features[u],b.node_features[i]))/a.node_features.shape[1])
    for k,(u,v) in enumerate(a.edge_index.T):
        for l,(i,j) in enumerate(b.edge_index.T):
            edge+=int(m[u,i])*int(m[v,j])*math.exp(-(float(a.edge_features[k,0])-float(b.edge_features[l,0]))**2)
    if a.edge_index.shape[1] and b.edge_index.shape[1]:edge/=2*math.sqrt(a.edge_index.shape[1]*b.edge_index.shape[1])
    else:edge=0.
    return (edge+node/math.sqrt(len(a.node_ids)*len(b.node_ids)))/2

def test_hard_assignment_is_injective():
    out=harden(np.array([[.9,.8,0],[.7,.6,.1]]))
    assert out[0,0]==1 and out.shape==(2,3)
    assert (out.sum(0)<=1).all() and (out.sum(1)<=1).all()
    np.testing.assert_array_equal(harden(np.ones((2,3))),[[1,0,0],[0,1,0]])

def test_literal_directed_and_zero_edge_scores():
    a=graph([[0],[1]],[(0,1,2)])
    assert score_assignment(a,a,np.eye(2),config())==pytest.approx(.75)
    z=graph([[0],[1]],[])
    assert score_assignment(z,z,np.eye(2),config())==pytest.approx(.5)
    with pytest.raises(ValueError):score_assignment(a,a,np.ones((2,2)),config())

@pytest.mark.parametrize('n,m',[(1,3),(2,2),(3,2),(4,4)])
def test_scores_against_exhaustive_independent_bound(n,m):
    a=graph([[i*.31] for i in range(n)],[(i,i+1,i*.4) for i in range(n-1)])
    b=graph([[i*.43] for i in range(m)],[(i+1,i,i*.2) for i in range(m-1)])
    scores=[]
    for rows in itertools.combinations(range(n),min(n,m)):
        for cols in itertools.permutations(range(m),min(n,m)):
            assignment=np.zeros((n,m));assignment[rows,cols]=1
            expected=oracle(a,b,assignment)
            assert score_assignment(a,b,assignment,config())==pytest.approx(expected,abs=1e-8,rel=1e-6)
            scores.append(expected)
    result=match_reference(a,b,config())
    assert result.score<=max(scores)+1e-8
    assert result.iterations==48
    assert result.convergence=='temperature_complete'

def test_extreme_finite_features_and_capacity():
    a=graph([[1e150],[-1e150]],[(0,1,1)])
    assert math.isfinite(match_reference(a,a,config()).score)
    with pytest.raises(ValueError,match='capacity'):match_reference(a,a,config()|{'max_pair_entries':1})


def test_single_iteration_matches_literal_half_coefficient():
    a=graph([[0],[.4]],[(0,1,.1)])
    b=graph([[.1],[.7]],[(0,1,.3)])
    V=np.array([[math.exp(-(x[0]-y[0])**2) for y in b.node_features] for x in a.node_features])
    Q=V.copy();Q[0,0]+=.5*math.exp(-.2**2)*V[1,1]
    expected=np.exp(Q);expected/=expected.sum(1,keepdims=True);expected/=expected.sum(0,keepdims=True)
    result=match_reference(a,b,config()|{'beta_final':1.})
    np.testing.assert_allclose(result.soft_assignment,expected,atol=1e-8,rtol=1e-6)
