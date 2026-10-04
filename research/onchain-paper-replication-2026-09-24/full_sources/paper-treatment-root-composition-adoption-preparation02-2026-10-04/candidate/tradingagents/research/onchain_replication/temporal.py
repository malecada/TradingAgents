"""Packed causal LSTM with final-state-query additive temporal attention."""
from __future__ import annotations
import math
import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence,pad_packed_sequence


def initialize_linear(layer):
    nn.init.xavier_uniform_(layer.weight,gain=1.)
    if layer.bias is not None:nn.init.zeros_(layer.bias)


class TemporalHead(nn.Module):
    def __init__(self,input_width,hidden_width,attention_width,task,depth=1):
        super().__init__()
        if task not in ('classification','regression'):raise ValueError('unknown prediction task')
        self.lstm=nn.LSTM(input_width,hidden_width,num_layers=depth,batch_first=True)
        bound=1/math.sqrt(hidden_width)
        for name,p in self.lstm.named_parameters():
            if 'bias' in name:nn.init.zeros_(p)
            else:nn.init.uniform_(p,-bound,bound)
        self.query=nn.Linear(hidden_width,attention_width,bias=True)
        self.key=nn.Linear(hidden_width,attention_width,bias=False)
        self.alignment=nn.Linear(attention_width,1,bias=False)
        self.output=nn.Linear(hidden_width,2 if task=='classification' else 1)
        for layer in (self.query,self.key,self.alignment,self.output):initialize_linear(layer)

    def forward(self,x,mask=None,*,return_attention=False):
        if x.ndim!=3:raise ValueError('temporal input dimensions')
        valid=torch.ones(x.shape[:2],dtype=torch.bool,device=x.device) if mask is None else mask
        if valid.shape!=x.shape[:2] or valid.dtype!=torch.bool:raise ValueError('temporal mask dimensions')
        lengths=valid.sum(1)
        prefix=torch.arange(x.shape[1],device=x.device)[None,:]<lengths[:,None]
        if not torch.equal(prefix,valid) or (lengths==0).any():raise ValueError('nonempty valid prefixes required')
        packed=pack_padded_sequence(x,lengths.cpu(),batch_first=True,enforce_sorted=False)
        encoded,_=self.lstm(packed)
        h,_=pad_packed_sequence(encoded,batch_first=True,total_length=x.shape[1])
        last=h[torch.arange(len(x),device=x.device),lengths-1]
        logits=self.alignment(torch.tanh(self.query(last)[:,None,:]+self.key(h))).squeeze(-1)
        attention=torch.softmax(logits.masked_fill(~valid,-torch.inf),dim=1)
        context=(attention[:,:,None]*h).sum(1)
        out=self.output(context)
        return (out,attention) if return_attention else out
