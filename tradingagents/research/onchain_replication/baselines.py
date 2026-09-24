"""Frozen price baselines and named diagnostics; no empirical I/O at import."""
import math
import numpy as np
import torch
from torch import nn
from .temporal import initialize_linear


def initialize_recurrent(layer):
    bound=1/math.sqrt(layer.hidden_size)
    for name,p in layer.named_parameters():
        if 'bias' in name:nn.init.zeros_(p)
        else:nn.init.uniform_(p,-bound,bound)


def head(width,task):
    if task not in ('classification','regression'):raise ValueError('unknown task')
    result=nn.Linear(width,2 if task=='classification' else 1);initialize_linear(result);return result


class PriceRecurrent(nn.Module):
    def __init__(self,kind,task):
        super().__init__()
        if kind not in ('lstm','gru'):raise ValueError('unknown price recurrence')
        self.recurrent=(nn.LSTM if kind=='lstm' else nn.GRU)(1,64,batch_first=True)
        initialize_recurrent(self.recurrent);self.output=head(64,task)

    def forward(self,x):
        if x.ndim!=3 or x.shape[1:]!=(28,1) or not torch.isfinite(x).all():raise ValueError('28 complete standardized closes required')
        sequence,_=self.recurrent(x);return self.output(sequence[:,-1])


class HierarchicalLSTM(nn.Module):
    """Four shared seven-day lower sequences, then a four-step upper sequence."""
    def __init__(self,task):
        super().__init__();self.lower=nn.LSTM(1,128,batch_first=True);self.upper=nn.LSTM(128,128,batch_first=True)
        initialize_recurrent(self.lower);initialize_recurrent(self.upper);self.output=head(128,task)

    def forward(self,x):
        if x.ndim!=3 or x.shape[1:]!=(28,1) or not torch.isfinite(x).all():raise ValueError('four complete seven-day chunks required')
        lower,_=self.lower(x.reshape(-1,7,1));upper,_=self.upper(lower[:,-1].reshape(len(x),4,128))
        return self.output(upper[:,-1])


def price_svm(task):
    from sklearn.svm import SVC,SVR
    if task=='classification':return SVC(C=1,kernel='rbf',gamma='scale',class_weight=None,probability=False,tol=.001,max_iter=-1,cache_size=200)
    if task=='regression':return SVR(C=1,epsilon=.1,kernel='rbf',gamma='scale',tol=.001,max_iter=-1,cache_size=200)
    raise ValueError('unknown task')


def training_controls(training_labels,input_closes):
    y=np.asarray(training_labels);x=np.asarray(input_closes)
    if y.ndim!=1 or not len(y) or not np.isin(y,[0,1]).all() or x.ndim!=2 or x.shape[1]<2 or not np.isfinite(x).all():raise ValueError('control population invalid')
    return {'training_majority':[float(y.mean())]*len(x),'last_direction':(x[:,-1]>x[:,-2]).astype(float).tolist()}


def permute_training_labels(labels):
    labels=np.asarray(labels)
    return labels[np.random.Generator(np.random.PCG64(20260924)).permutation(len(labels))].copy()


class DiagnosticGraph(nn.Module):
    def __init__(self,config,arm):
        super().__init__();self.arm=arm
        from .model import GraphEncoder
        if arm=='constant_graph':return
        from .gat import GraphAttention
        encoder=GraphEncoder(config)
        if arm=='mcm_without_gat':self.mlp=encoder.mlp
        elif arm=='gat_without_mcm':
            self.gat=encoder.gat
            self.gat[0]=GraphAttention(4,config['gat_widths'][0],config['gat_heads'][0],concat=config['gat_concatenate'][0],activation=config['gat_activation'][0],dropout=0.,slope=config['leaky_relu_slope'])
        else:raise ValueError('unknown graph diagnostic')

    def forward(self,mcm,edge_index,node_mask=None,batch=None):
        from .pooling import mean_pool
        if self.arm=='constant_graph':return mcm.new_zeros(32)
        if node_mask is not None:mcm=mcm.masked_fill(~node_mask[:,None],0.)
        if not torch.isfinite(mcm).all():raise ValueError('nonfinite admitted diagnostic input')
        if self.arm=='mcm_without_gat':h=self.mlp(mcm)
        else:
            h=mcm
            for layer in self.gat:h=layer(h,edge_index,node_mask)
        return mean_pool(h,node_mask,batch)
