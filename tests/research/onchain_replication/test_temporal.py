import torch
from tradingagents.research.onchain_replication.temporal import TemporalHead


def test_attention_mask_and_future_padding_invariance():
    torch.manual_seed(11)
    model=TemporalHead(input_width=3,hidden_width=8,attention_width=4,task='classification')
    x=torch.randn(2,3,3);mask=torch.tensor([[1,1,0],[1,1,1]],dtype=torch.bool)
    y,attention=model(x,mask,return_attention=True)
    assert attention[0,2]==0
    torch.testing.assert_close(attention.sum(1),torch.ones(2))
    changed=x.clone();changed[0,2]=1000
    torch.testing.assert_close(model(changed,mask),y)
    torch.testing.assert_close(model(x[:1,:2]),y[:1])
