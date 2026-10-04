"""BTC subset transforms bind exact parent edges and rebuild exact node volumes."""
from dataclasses import replace
from fractions import Fraction
import numpy as np
from .btc_store import validate_exact
from .btc_weekly import ExactBTCGraph
from .subsets import filter_graph
from .cache import cache_key


def filter_btc_graph(value,variant,*,cohort=None,cohort_hash=None):
    validate_exact(value)
    graph,receipt=filter_graph(value.graph,variant,cohort=cohort,cohort_hash=cohort_hash,
        exact_incident_volumes=value.incident_satoshis)
    retained=set(graph.node_ids)
    mask=[value.graph.node_ids[a] in retained and value.graph.node_ids[b] in retained for a,b in value.graph.edge_index.T]
    exact=tuple(amount for amount,keep in zip(value.edge_satoshis,mask,strict=True) if keep)
    features=np.zeros((len(graph.node_ids),4));volumes=[[Fraction(0),Fraction(0)] for _ in graph.node_ids]
    for (a,b),count,amount in zip(graph.edge_index.T,graph.edge_aggregates[:,0],exact,strict=True):
        features[a,1]+=count;features[b,0]+=count;volumes[a][1]+=amount;volumes[b][0]+=amount
    for i,(incoming,outgoing) in enumerate(volumes):features[i,2:]=float(incoming/100000000),float(outgoing/100000000)
    encode=lambda items:[[format(x.numerator,'x'),format(x.denominator,'x')] for x in items]
    receipt={**receipt,'schema_version':3,'exact_parent_hash':cache_key({
        'edge_satoshis':encode(value.edge_satoshis),'incident_satoshis':encode(value.incident_satoshis),
        'fee_satoshis':value.fee_satoshis,'observed_chain_order_checked':value.observed_chain_order_checked}),
        'fee_policy':'origin known fees retained; subset is an edge treatment, not a new transaction population',
        'node_volume_policy':'sum retained exact rational satoshis before conversion to native binary64'}
    graph=replace(graph,node_features=np.log1p(features),graph_config_hash=cache_key({'parent_config':value.graph.graph_config_hash,'variant':receipt}))
    result=ExactBTCGraph(graph,exact,tuple(a+b for a,b in volumes),value.fee_satoshis,value.observed_chain_order_checked)
    validate_exact(result)
    return result,receipt
