"""Isolated CPU first-order streamed execution of the unchanged GAT equations.

Prospective engineering candidate only; not integrated or empirically admitted.
Node attention dot products avoid explicit edge/head/width attention products.
Message aggregation saves h/scalar attention/endpoints once and recomputes each
bounded edge block in backward. Floating reduction order can differ from eager
execution; only the frozen numerical oracle can establish accepted agreement.
"""
from __future__ import annotations
import math
import torch
from torch import nn
from torch.nn import functional as F
from torch.autograd.function import once_differentiable

MAX_BLOCK_EDGES = 65536


def _block_limit(value):
    if type(value) is not int or not 0 < value <= MAX_BLOCK_EDGES:
        raise ValueError('positive integer block_edges <=65536 required')
    return value


def _audit(audit, phase, size):
    if audit is not None:
        audit[phase+'_max_edges'] = max(audit[phase+'_max_edges'], size)
        audit[phase+'_blocks'] += 1


class _WeightedAggregate(torch.autograd.Function):
    @staticmethod
    def forward(ctx, h, attention, source, target, block_edges, audit):
        ctx.save_for_backward(h, attention, source, target)
        ctx.block_edges = block_edges
        ctx.audit = audit
        out = torch.zeros_like(h)
        for start in range(0, source.numel(), block_edges):
            stop = min(start + block_edges, source.numel())
            # Private output mutation occurs inside custom forward, where no
            # per-block autograd graph is constructed or retained.
            messages = h.index_select(0, source[start:stop]) * attention[start:stop, :, None]
            out.index_add_(0, target[start:stop], messages)
            _audit(audit, 'forward', stop-start)
            del messages
        return out

    @staticmethod
    @once_differentiable
    def backward(ctx, grad_output):
        h, attention, source, target = ctx.saved_tensors
        grad_h = torch.zeros_like(h) if ctx.needs_input_grad[0] else None
        grad_attention = torch.zeros_like(attention) if ctx.needs_input_grad[1] else None
        for start in range(0, source.numel(), ctx.block_edges):
            stop = min(start + ctx.block_edges, source.numel())
            incoming = grad_output.index_select(0, target[start:stop])
            if grad_h is not None:
                messages = incoming * attention[start:stop, :, None]
                grad_h.index_add_(0, source[start:stop], messages)
                del messages
            if grad_attention is not None:
                local = h.index_select(0, source[start:stop])
                grad_attention[start:stop] = (incoming * local).sum(-1)
                del local
            _audit(ctx.audit, 'backward', stop-start)
            del incoming
        return grad_h, grad_attention, None, None, None, None


def weighted_aggregate(h, attention, source, target, *, block_edges=MAX_BLOCK_EDGES, audit=None):
    """Full-neighbor weighted sum, CPU float32/float64, first derivatives only.

    Contiguous one-dimensional endpoint vectors define original edge order.
    h and attention may be strided views; no eager contiguous copy is required.
    An optional fresh empty audit dict receives four finite block counters.
    No numerical arrays or per-edge trace are retained by that audit.
    """
    block_edges = _block_limit(block_edges)
    if not all(isinstance(value, torch.Tensor) for value in (h,attention,source,target)):
        raise TypeError('tensor aggregate inputs required')
    if h.ndim != 3 or any(size <= 0 for size in h.shape):
        raise ValueError('aggregate requires nonempty node/head/width dimensions')
    if h.device.type != 'cpu' or h.dtype not in (torch.float32,torch.float64):
        raise ValueError('candidate supports CPU float32/float64 only')
    if attention.device != h.device or attention.dtype != h.dtype:
        raise ValueError('aggregate attention dtype/device differs')
    if source.ndim != 1 or target.ndim != 1 or source.shape != target.shape:
        raise ValueError('aggregate endpoint dimensions differ')
    if source.dtype != torch.long or target.dtype != torch.long or source.device != h.device or target.device != h.device:
        raise ValueError('aggregate requires same-device int64 endpoints')
    if not source.is_contiguous() or not target.is_contiguous():
        raise ValueError('aggregate requires contiguous endpoint vectors')
    if attention.shape != (source.numel(),h.shape[1]):
        raise ValueError('aggregate scalar attention dimensions differ')
    if source.numel() and (source.min() < 0 or target.min() < 0 or source.max() >= len(h) or target.max() >= len(h)):
        raise ValueError('aggregate endpoint outside node population')
    if audit is not None:
        if type(audit) is not dict or audit:
            raise ValueError('fresh empty aggregate audit dictionary required')
        audit.update(forward_max_edges=0,backward_max_edges=0,forward_blocks=0,backward_blocks=0)
    return _WeightedAggregate.apply(h,attention,source,target,block_edges,audit)


class GraphAttention(nn.Module):
    def __init__(self,input_width,head_width,heads,*,concat=True,activation='elu',dropout=0.,slope=.2,block_edges=MAX_BLOCK_EDGES):
        super().__init__()
        self.block_edges = _block_limit(block_edges)
        self.weight=nn.Parameter(torch.empty(heads,input_width,head_width))
        self.a_source=nn.Parameter(torch.empty(heads,head_width))
        self.a_target=nn.Parameter(torch.empty(heads,head_width))
        self.concat=concat;self.activation=activation;self.dropout=dropout;self.slope=slope
        for weight in self.weight:nn.init.xavier_uniform_(weight,gain=1.)
        bound=math.sqrt(6/(2*head_width+1))
        nn.init.uniform_(self.a_source,-bound,bound);nn.init.uniform_(self.a_target,-bound,bound)

    def forward(self,x,edge_index,node_mask=None):
        if x.device.type != 'cpu' or edge_index.device.type != 'cpu':raise ValueError('streamed candidate is CPU-only')
        n=len(x)
        if x.ndim!=2 or not n or edge_index.ndim!=2 or edge_index.shape[0]!=2:raise ValueError('invalid GAT shape')
        if edge_index.dtype!=torch.long:raise ValueError('GAT integer edges required')
        if edge_index.numel() and (edge_index.min()<0 or edge_index.max()>=n):raise ValueError('GAT endpoint')
        valid=torch.ones(n,dtype=torch.bool,device=x.device) if node_mask is None else node_mask
        if valid.shape!=(n,) or valid.dtype!=torch.bool or not valid.any():raise ValueError('invalid node mask')
        source,target=edge_index
        keep=(source!=target)&valid[source]&valid[target]
        source=source[keep];target=target[keep]
        # Aggregated graph contract: duplicate neighbors are rejected, not counted twice.
        if torch.unique(torch.stack([source,target]),dim=1).shape[1]!=len(source):raise ValueError('duplicate GAT edge')
        nodes=torch.arange(n,device=x.device)[valid]
        source=torch.cat([source,nodes]);target=torch.cat([target,nodes])
        clean=torch.where(valid[:,None],x,torch.zeros_like(x))
        h=torch.einsum('nf,hfd->nhd',clean,self.weight)
        source_score=(h*self.a_source).sum(-1)
        target_score=(h*self.a_target).sum(-1)
        e=F.leaky_relu(source_score[source]+target_score[target],self.slope)
        index=target[:,None].expand_as(e)
        maximum=torch.full((n,self.weight.shape[0]),-torch.inf,dtype=e.dtype,device=e.device)
        maximum.scatter_reduce_(0,index,e,reduce='amax',include_self=True)
        numer=torch.exp(e-maximum[target])
        denom=torch.zeros_like(maximum).scatter_add(0,index,numer)
        attention=F.dropout(numer/denom[target],p=self.dropout,training=self.training)
        out=weighted_aggregate(h,attention,source,target,block_edges=self.block_edges)
        if self.activation=='elu':out=F.elu(out)
        elif self.activation!='identity':raise ValueError('unknown GAT activation')
        return out.reshape(n,-1) if self.concat else out.mean(1)
