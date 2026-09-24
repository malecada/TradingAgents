"""Explicit arm assembly; all graph comparators share the frozen temporal head."""
import torch
from torch import nn
from .model import ReplicationModel
from .temporal import TemporalHead
from .baselines import PriceRecurrent,HierarchicalLSTM,DiagnosticGraph
from .graph_baselines import GINEncoder

PRICE_ARMS={'lstm','gru','hlstm','svm'}
VECTOR_WIDTHS={'node2vec':32,'watchyourstep':32,'graphwave':30,'constant_graph':32}
GRAPH_ARMS={'proposed','training_label_permutation','mcm_without_gat','gat_without_mcm','gin'}


class VectorTemporal(nn.Module):
    def __init__(self,width,task,config,constant=False):
        super().__init__();self.width=width;self.constant=constant
        self.temporal=TemporalHead(width+1,config['lstm_width'],config['attention_width'],task,config['lstm_depth'])
    def forward(self,prices,graph_vectors=None):
        if prices.ndim!=3 or prices.shape[2]!=1:raise ValueError('price sequence dimensions')
        if self.constant:graph_vectors=prices.new_zeros((*prices.shape[:2],self.width))
        if graph_vectors is None or graph_vectors.shape!=(*prices.shape[:2],self.width):raise ValueError('graph vector dimensions')
        return self.temporal(torch.cat([graph_vectors,prices],-1))


class AlternativeGraphTemporal(ReplicationModel):
    def __init__(self,config,task,arm):
        nn.Module.__init__(self);self.config=dict(config);self.task=task
        self.graph=GINEncoder() if arm=='gin' else DiagnosticGraph(config,arm)
        self.temporal=TemporalHead(33,config['lstm_width'],config['attention_width'],task,config['lstm_depth'])


def build_model(arm,task,config):
    task={'direction':'classification'}.get(task,task)
    if task not in {'classification','regression'}:raise ValueError('unknown task')
    if arm in {'lstm','gru'}:return PriceRecurrent(arm,task)
    if arm=='hlstm':return HierarchicalLSTM(task)
    if arm in {'proposed','training_label_permutation'}:return ReplicationModel(config,task)
    if arm in {'gin','gat_without_mcm','mcm_without_gat'}:return AlternativeGraphTemporal(config,task,arm)
    if arm in VECTOR_WIDTHS:return VectorTemporal(VECTOR_WIDTHS[arm],task,config,arm=='constant_graph')
    if arm=='svm':
        from .baselines import price_svm
        return price_svm(task)
    raise ValueError('unregistered model arm')
