"""MCM-MLP → directed GAT → mean pool → price join → LSTM → additive attention → head (spec §8).

Also the price-only baselines (LSTM, GRU, two-level HLSTM). Pure torch; the GAT
uses edge lists with incoming edges plus one self loop per node.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


def output_width(task):
    return 2 if task == 'classification' else 1


class GATLayer(nn.Module):
    def __init__(self, inp, width, heads, concat, slope):
        super().__init__()
        self.W = nn.Linear(inp, heads * width, bias=False)
        self.a_src = nn.Parameter(torch.empty(heads, width))
        self.a_dst = nn.Parameter(torch.empty(heads, width))
        self.heads, self.width, self.concat, self.slope = heads, width, concat, slope
        nn.init.xavier_uniform_(self.W.weight)
        bound = (6.0 / (2 * width + 1)) ** 0.5
        nn.init.uniform_(self.a_src, -bound, bound)
        nn.init.uniform_(self.a_dst, -bound, bound)
        self.bias = nn.Parameter(torch.zeros(heads * width if concat else width))

    def forward(self, h, edge_index):
        K = h.shape[0]
        src, dst = edge_index
        keep = src != dst                                  # observed self-transfers: self is added once below
        src, dst = src[keep], dst[keep]
        loop = torch.arange(K, device=h.device)
        src = torch.cat([src, loop])                       # incoming edges + self once
        dst = torch.cat([dst, loop])
        Wh = self.W(h).view(K, self.heads, self.width)
        e = F.leaky_relu((Wh[src] * self.a_src).sum(-1) + (Wh[dst] * self.a_dst).sum(-1), self.slope)   # (E, heads)
        e_max = torch.full((K, self.heads), -1e30, dtype=e.dtype).index_reduce_(0, dst, e, 'amax', include_self=True)
        ex = torch.exp(e - e_max[dst])
        denom = torch.zeros(K, self.heads, dtype=e.dtype).index_add_(0, dst, ex)
        alpha = ex / denom[dst]
        out = torch.zeros(K, self.heads, self.width, dtype=h.dtype).index_add_(0, dst, alpha.unsqueeze(-1) * Wh[src])
        out = out.reshape(K, -1) if self.concat else out.mean(1)
        return out + self.bias


class GraphEncoder(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        w = cfg['mlp_widths']
        self.mlp = nn.Sequential(nn.Linear(cfg['mcm_input'], w[0]), nn.ReLU(), nn.Linear(w[0], w[1]), nn.ReLU())
        self.gat1 = GATLayer(w[1], cfg['gat_widths'][0], cfg['gat_heads'][0], cfg['gat_concat'][0], cfg['leaky_relu_slope'])
        self.gat2 = GATLayer(cfg['gat_widths'][0] * cfg['gat_heads'][0], cfg['gat_widths'][1], cfg['gat_heads'][1],
                             cfg['gat_concat'][1], cfg['leaky_relu_slope'])

    def forward(self, mcm, edge_index):
        h = self.mlp(mcm)
        h = F.elu(self.gat1(h, edge_index))
        h = self.gat2(h, edge_index)
        return h.mean(0)


class AttentionLSTM(nn.Module):
    def __init__(self, input_width, lstm_width, attention_width):
        super().__init__()
        self.lstm = nn.LSTM(input_width, lstm_width, batch_first=True)
        self.Wq = nn.Linear(lstm_width, attention_width)
        self.Wk = nn.Linear(lstm_width, attention_width)
        self.v = nn.Linear(attention_width, 1, bias=False)
        for name, p in self.lstm.named_parameters():
            if 'weight' in name:
                nn.init.uniform_(p, -1 / lstm_width ** 0.5, 1 / lstm_width ** 0.5)
            else:
                nn.init.zeros_(p)

    def forward(self, seq, lengths=None):
        B, T, _ = seq.shape
        H, _ = self.lstm(seq)
        if lengths is None:
            lengths = torch.full((B,), T, dtype=torch.long)
        last = H[torch.arange(B), lengths - 1]
        score = self.v(torch.tanh(self.Wq(last).unsqueeze(1) + self.Wk(H))).squeeze(-1)         # (B, T)
        mask = torch.arange(T).unsqueeze(0) < lengths.unsqueeze(1)
        score = score.masked_fill(~mask, -1e30)
        w = torch.softmax(score, 1)
        return (w.unsqueeze(-1) * H).sum(1)


class FullModel(nn.Module):
    def __init__(self, task, cfg):
        super().__init__()
        self.encoder = GraphEncoder(cfg)
        self.seq = AttentionLSTM(cfg['graph_vector_width'] + 1, cfg['lstm_width'], cfg['attention_width'])
        self.head = nn.Linear(cfg['lstm_width'], output_width(task))

    def forward(self, prices, graph_vectors):
        x = torch.cat([prices.unsqueeze(-1), graph_vectors], -1)
        return self.head(self.seq(x))


class PriceModel(nn.Module):
    def __init__(self, kind, task, cfg):
        super().__init__()
        b = cfg['baselines']
        self.kind = kind
        if kind == 'lstm':
            self.rnn = nn.LSTM(1, b['lstm']['width'], batch_first=True)
            width = b['lstm']['width']
        elif kind == 'gru':
            self.rnn = nn.GRU(1, b['gru']['width'], batch_first=True)
            width = b['gru']['width']
        elif kind == 'hlstm':
            h = b['hlstm']
            self.lower = nn.LSTM(1, h['lower'], batch_first=True)
            self.upper = nn.LSTM(h['lower'], h['upper'], batch_first=True)
            self.chunks, self.chunk_len, width = h['chunks'], h['chunk_len'], h['upper']
        else:
            raise ValueError(kind)
        self.head = nn.Linear(width, output_width(task))

    def forward(self, prices):
        x = prices.unsqueeze(-1)
        if self.kind == 'hlstm':
            B = x.shape[0]
            chunks = x.reshape(B * self.chunks, self.chunk_len, 1)
            _, (h, _) = self.lower(chunks)
            _, (h2, _) = self.upper(h[-1].reshape(B, self.chunks, -1))
            return self.head(h2[-1])
        _, h = self.rnn(x)
        h = h[0] if isinstance(h, tuple) else h
        return self.head(h[-1])
