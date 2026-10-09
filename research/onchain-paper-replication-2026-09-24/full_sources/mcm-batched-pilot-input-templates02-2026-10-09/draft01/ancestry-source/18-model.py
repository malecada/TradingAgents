"""Full trainable MLP→GAT→pooled graph/price→attention LSTM path."""
from __future__ import annotations
import torch
from torch import nn
from .gat import GraphAttention
from .pooling import mean_pool
from .temporal import TemporalHead,initialize_linear


class GraphEncoder(nn.Module):
    def __init__(self,config):
        super().__init__();self.config=dict(config)
        widths=[config['mcm_input'],*config['mlp_widths']]
        blocks=[]
        for a,b in zip(widths,widths[1:]):
            linear=nn.Linear(a,b);initialize_linear(linear);blocks.extend([linear,nn.ReLU()])
        self.mlp=nn.Sequential(*blocks)
        layers=[];width=widths[-1]
        for heads,out,concat,activation in zip(config['gat_heads'],config['gat_widths'],config['gat_concatenate'],config['gat_activation'],strict=True):
            layers.append(GraphAttention(width,out,heads,concat=concat,activation=activation,dropout=config['gat_dropout'],slope=config['leaky_relu_slope']))
            width=out*heads if concat else out
        if width!=config['graph_vector_width']:raise ValueError('graph output width mismatch')
        self.gat=nn.ModuleList(layers)

    def forward(self,mcm,edge_index,node_mask=None,batch=None):
        if batch is not None and edge_index.numel() and (batch[edge_index[0]]!=batch[edge_index[1]]).any():raise ValueError('edge crosses graph batch')
        if node_mask is not None:
            if node_mask.shape!=(len(mcm),) or node_mask.dtype!=torch.bool:raise ValueError('invalid node mask')
            mcm=mcm.masked_fill(~node_mask[:,None],0.)
        if not torch.isfinite(mcm).all():raise ValueError('nonfinite admitted MCM')
        h=self.mlp(mcm)
        for layer in self.gat:h=layer(h,edge_index,node_mask)
        return mean_pool(h,node_mask,batch)


class ReplicationModel(nn.Module):
    def __init__(self,config,task):
        super().__init__();self.config=dict(config);self.task=task
        self.graph=GraphEncoder(config)
        self.temporal=TemporalHead(config['graph_vector_width']+config['price_input_width'],config['lstm_width'],config['attention_width'],task,config['lstm_depth'])

    def forward(self,graph_sequences,prices,mask=None):
        if prices.ndim!=3 or len(graph_sequences)!=len(prices):raise ValueError('graph/price sequence batch mismatch')
        valid=torch.ones(prices.shape[:2],dtype=torch.bool,device=prices.device) if mask is None else mask
        rows=[];encoded_graphs={}
        for b,sequence in enumerate(graph_sequences):
            if len(sequence)!=prices.shape[1]:raise ValueError('graph/price lookback mismatch')
            vectors=[]
            for t,graph in enumerate(sequence):
                if not valid[b,t]:vectors.append(prices.new_zeros(self.config['graph_vector_width']))
                elif graph is None:raise ValueError('missing valid graph step')
                else:
                    key=id(graph)
                    if key not in encoded_graphs:encoded_graphs[key]=self.graph(**graph)
                    vectors.append(encoded_graphs[key])
            rows.append(torch.stack(vectors))
        embeddings=torch.stack(rows)
        return self.temporal(torch.cat([embeddings,prices],dim=-1),valid)

    def parameter_groups(self):
        return {'mlp':list(self.graph.mlp.parameters()),'gat':list(self.graph.gat.parameters()),
                'lstm':list(self.temporal.lstm.parameters()),
                'attention':list(self.temporal.query.parameters())+list(self.temporal.key.parameters())+list(self.temporal.alignment.parameters()),
                'head':list(self.temporal.output.parameters())}
