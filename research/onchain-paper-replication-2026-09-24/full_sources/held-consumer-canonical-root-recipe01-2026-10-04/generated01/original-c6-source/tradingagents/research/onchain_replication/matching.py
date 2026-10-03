"""Bounded torch batches; no four-index compatibility tensor or custom CUDA.

Pairs of equal shape share one batched matrix operation. Edge compatibility is
streamed in bounded chunks. GPU index-add may have rounding nondeterminism;
tied assignments are judged by objective and feasibility, never bit identity.
"""
from __future__ import annotations
from collections import defaultdict
import numpy as np
from .matching_reference import MatchResult,harden,validate_pair


def _chunks(a,b,config,device):
    import torch
    limit=config['edge_agreement_chunk_pairs']
    right_edges=b.edge_index.shape[1]
    for k,(u,v) in enumerate(a.edge_index.T):
        for start in range(0,right_edges,limit):
            stop=min(right_edges,start+limit)
            dest=torch.tensor(b.edge_index[:,start:stop].copy(),dtype=torch.long,device=device)
            x=torch.tensor(a.edge_features[k].copy(),dtype=torch.float64,device=device)
            y=torch.tensor(b.edge_features[start:stop].copy(),dtype=torch.float64,device=device)
            affinity=torch.exp(-((x-y)**2).mean(-1))
            yield int(u),int(v),dest[0],dest[1],affinity


def match_batch(pairs,config,device='cpu'):
    import torch
    if config.get('internal_precision')!='float64':raise ValueError('unverified float32 solve; select registered stable precision configuration')
    groups=defaultdict(list)
    for index,(a,b) in enumerate(pairs):
        validate_pair(a,b,config)
        groups[(len(a.node_ids),len(b.node_ids))].append((index,a,b))
    results=[None]*len(pairs)
    with torch.no_grad():
        for (n,m),group in groups.items():
            batch_size=max(1,config['max_pair_entries']//(n*m))
            for offset in range(0,len(group),batch_size):
                batch=group[offset:offset+batch_size]
                x=torch.tensor(np.stack([a.node_features for _,a,b in batch]),dtype=torch.float64,device=device)
                y=torch.tensor(np.stack([b.node_features for _,a,b in batch]),dtype=torch.float64,device=device)
                V=torch.exp(-((x[:,:,None,:]-y[:,None,:,:])**2).mean(-1))
                M=V.clone();beta=config['beta0'];iterations=0
                while beta<=config['beta_final'] and iterations<config['max_iterations']:
                    Q=config['alpha']*V
                    for k,(_,a,b) in enumerate(batch):
                        for u,v,i,j,affinity in _chunks(a,b,config,device):
                            Q[k,u].index_add_(0,i,.5*affinity*M[k,v,j])
                    logM=beta*Q
                    logM=logM-torch.logsumexp(logM,dim=2,keepdim=True)
                    logM=logM-torch.logsumexp(logM,dim=1,keepdim=True)
                    M=torch.exp(logM);beta*=1+config['beta_rate'];iterations+=1
                for k,(index,a,b) in enumerate(batch):
                    assignment=harden(M[k].cpu().numpy())
                    H=torch.tensor(assignment,dtype=torch.float64,device=device)
                    node=(H*V[k]).sum()/((n*m)**.5)
                    edge=torch.zeros((),dtype=torch.float64,device=device)
                    for u,v,i,j,affinity in _chunks(a,b,config,device):edge+=(H[u,i]*H[v,j]*affinity).sum()
                    l1,l2=a.edge_index.shape[1],b.edge_index.shape[1]
                    if l1*l2:edge=edge/(2*(l1*l2)**.5)
                    score=float(((edge+config['alpha']*node)/(1+config['alpha'])).float().cpu())
                    results[index]=MatchResult(assignment,score,'temperature_complete' if beta>config['beta_final'] else 'iteration_cap',iterations,M[k].float().cpu().numpy().copy())
    return results
