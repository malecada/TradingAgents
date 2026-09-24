"""Declared graph readout after GAT; padding has zero contribution."""
import torch


def mean_pool(x,mask=None,batch=None):
    valid=torch.ones(len(x),dtype=torch.bool,device=x.device) if mask is None else mask
    if valid.shape!=(len(x),) or valid.dtype!=torch.bool or not valid.any():raise ValueError('empty or malformed pooling mask')
    if batch is None:return x[valid].mean(0)
    if batch.shape!=(len(x),) or batch.dtype!=torch.long:raise ValueError('invalid graph batch')
    ids=torch.unique(batch,sorted=True)
    if (ids<0).any() or not torch.equal(ids,torch.arange(len(ids),device=batch.device)):raise ValueError('contiguous graph batch IDs required')
    if any(not (valid&(batch==i)).any() for i in ids):raise ValueError('empty admitted graph in batch')
    return torch.stack([x[valid&(batch==i)].mean(0) for i in ids])
