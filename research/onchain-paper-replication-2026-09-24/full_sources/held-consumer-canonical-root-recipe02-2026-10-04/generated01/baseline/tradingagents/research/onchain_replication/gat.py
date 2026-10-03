"""Sparse incoming-neighbor graph attention implementing paper Eqs4–8."""
from __future__ import annotations
import math
import torch
from torch import nn
from torch.nn import functional as F


class GraphAttention(nn.Module):
    def __init__(self,input_width,head_width,heads,*,concat=True,activation='elu',dropout=0.,slope=.2):
        super().__init__()
        self.weight=nn.Parameter(torch.empty(heads,input_width,head_width))
        self.a_source=nn.Parameter(torch.empty(heads,head_width))
        self.a_target=nn.Parameter(torch.empty(heads,head_width))
        self.concat=concat;self.activation=activation;self.dropout=dropout;self.slope=slope
        for weight in self.weight:nn.init.xavier_uniform_(weight,gain=1.)
        bound=math.sqrt(6/(2*head_width+1))
        nn.init.uniform_(self.a_source,-bound,bound);nn.init.uniform_(self.a_target,-bound,bound)

    def forward(self,x,edge_index,node_mask=None):
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
        e=F.leaky_relu((h[source]*self.a_source).sum(-1)+(h[target]*self.a_target).sum(-1),self.slope)
        index=target[:,None].expand_as(e)
        maximum=torch.full((n,self.weight.shape[0]),-torch.inf,dtype=e.dtype,device=e.device)
        maximum.scatter_reduce_(0,index,e,reduce='amax',include_self=True)
        numer=torch.exp(e-maximum[target])
        denom=torch.zeros_like(maximum).scatter_add(0,index,numer)
        attention=F.dropout(numer/denom[target],p=self.dropout,training=self.training)
        messages=h[source]*attention[:,:,None]
        out=torch.zeros_like(h).index_add(0,target,messages)
        if self.activation=='elu':out=F.elu(out)
        elif self.activation!='identity':raise ValueError('unknown GAT activation')
        return out.reshape(n,-1) if self.concat else out.mean(1)
