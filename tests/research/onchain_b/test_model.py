import torch

from tradingagents.research.onchain_b import config
from tradingagents.research.onchain_b import model as M

CFG = config.load('model')


def test_encoder_permutation_invariant():
    torch.manual_seed(0)
    enc = M.GraphEncoder(CFG)
    K, E = 30, 80
    mcm = torch.randn(K, 32)
    ei = torch.randint(0, K, (2, E))
    v = enc(mcm, ei)
    p = torch.randperm(K)
    inv = torch.argsort(p)
    v2 = enc(mcm[p], inv[ei])
    assert v.shape == (32,) and torch.allclose(v, v2, atol=1e-5)


def test_isolated_nodes_get_self_only():
    enc = M.GraphEncoder(CFG)
    mcm = torch.randn(5, 32)
    ei = torch.zeros((2, 0), dtype=torch.long)
    assert torch.isfinite(enc(mcm, ei)).all()


def test_full_model_gradients_everywhere():
    torch.manual_seed(1)
    m = M.FullModel('classification', CFG)
    prices = torch.randn(4, 28)
    gv = torch.randn(4, 28, 32, requires_grad=True)
    out = m(prices, gv)
    assert out.shape == (4, 2)
    out.sum().backward()
    for name, p in m.named_parameters():
        if name.startswith('encoder.'):
            continue   # encoder is exercised through encode_weeks, not through this forward
        assert p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0, name
    assert gv.grad.abs().sum() > 0


def test_encoder_gradients_everywhere():
    torch.manual_seed(4)
    enc = M.GraphEncoder(CFG)
    v = enc(torch.randn(20, 32), torch.randint(0, 20, (2, 50)))
    v.sum().backward()
    for name, p in enc.named_parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0, name


def test_attention_ignores_padding():
    torch.manual_seed(2)
    att = M.AttentionLSTM(3, 8, 4)
    x = torch.randn(2, 6, 3)
    a = att(x, lengths=torch.tensor([6, 4]))
    x2 = x.clone()
    x2[1, 4:] = 99.0
    b = att(x2, lengths=torch.tensor([6, 4]))
    assert torch.allclose(a[1], b[1], atol=1e-6)


def test_price_baselines_shapes():
    for kind in ('lstm', 'gru', 'hlstm'):
        m = M.PriceModel(kind, 'regression', CFG)
        assert m(torch.randn(3, 28)).shape == (3, 1)


def test_synthetic_learning():
    torch.manual_seed(3)
    m = M.PriceModel('lstm', 'regression', CFG)
    opt = torch.optim.Adam(m.parameters(), 1e-2)
    x = torch.randn(64, 28)
    y = x[:, -1:] * 2 + 1
    first = None
    for _ in range(500):
        opt.zero_grad()
        loss = ((m(x) - y) ** 2).mean()
        loss.backward()
        opt.step()
        first = first or loss.item()
    assert loss.item() < 0.2 * first
