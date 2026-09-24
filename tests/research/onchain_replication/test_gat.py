import math
import numpy as np
import torch
from tradingagents.research.onchain_replication.gat import GraphAttention


def test_three_node_directed_attention_against_scalar_calculation():
    layer=GraphAttention(1,1,1,concat=False,activation='identity').double()
    with torch.no_grad():layer.weight.fill_(1);layer.a_source.fill_(1);layer.a_target.fill_(1)
    x=torch.tensor([[1.],[2.],[3.]],dtype=torch.float64)
    edges=torch.tensor([[0,2,1],[1,1,1]]) # explicit self should appear only once
    out=layer(x,edges)
    weights=[math.exp(3),math.exp(4),math.exp(5)]
    expected=sum(w*v for w,v in zip(weights,[1,2,3]))/sum(weights)
    np.testing.assert_allclose(out.detach().numpy().ravel(),[1,expected,3],atol=1e-8)


def test_padding_and_relabeling():
    torch.manual_seed(11);layer=GraphAttention(2,3,2,concat=True)
    x=torch.tensor([[1.,0.],[0.,2.],[.2,.8]])
    edges=torch.tensor([[0,1],[1,2]])
    y=layer(x,edges)
    perm=torch.tensor([2,0,1]);inverse=torch.argsort(perm)
    torch.testing.assert_close(layer(x[perm],inverse[edges]),y[perm])
    padded=layer(torch.cat([x,torch.full((1,2),99.)]),edges,node_mask=torch.tensor([1,1,1,0],dtype=torch.bool))
    torch.testing.assert_close(padded[:3],y);assert torch.count_nonzero(padded[3])==0
