"""Durable exact-rational BTC sidecars, inseparable from a graph manifest."""
from fractions import Fraction
import json,os
from pathlib import Path
import numpy as np
from .btc_weekly import ExactBTCGraph
from .contracts import validate_graph
from .graph_store import save_graph,load_graph
from .provenance import file_hash,digest,canonical_bytes,durable_mkdir,sync_directory


def validate_exact(value):
    graph=value.graph;validate_graph(graph)
    if graph.asset!='BTC' or graph.edge_aggregates is None:raise ValueError('BTC raw aggregates required')
    if len(value.edge_satoshis)!=graph.edge_index.shape[1] or len(value.incident_satoshis)!=len(graph.node_ids):raise ValueError('exact sidecar dimensions')
    if type(value.fee_satoshis) is not int or value.fee_satoshis<0:raise ValueError('exact fee required')
    if any(type(v) is not Fraction or v<0 for v in value.incident_satoshis):raise ValueError('exact rational incident sidecar required')
    if type(value.observed_chain_order_checked) is not bool:raise ValueError('explicit chain-order qualification required')
    incident=[Fraction(0) for _ in graph.node_ids]
    node_values=[[Fraction(0),Fraction(0)] for _ in graph.node_ids]
    features=np.zeros((len(graph.node_ids),4))
    for (a,b),amount,native in zip(graph.edge_index.T,value.edge_satoshis,graph.edge_aggregates[:,1],strict=True):
        if type(amount) is not Fraction or amount<0 or float(amount/100000000)!=native:raise ValueError('exact edge/native aggregate mismatch')
        incident[a]+=amount;incident[b]+=amount
        node_values[a][1]+=amount;node_values[b][0]+=amount
    for (a,b),count in zip(graph.edge_index.T,graph.edge_aggregates[:,0],strict=True):
        if count<=0 or count!=int(count):raise ValueError('positive integer edge count required')
        features[a,1]+=count;features[b,0]+=count
    for i,(incoming,outgoing) in enumerate(node_values):
        features[i,2:]=float(incoming/100000000),float(outgoing/100000000)
    if tuple(incident)!=value.incident_satoshis:raise ValueError('exact incident sidecar differs from edges')
    if not np.array_equal(np.log1p(features),graph.node_features):raise ValueError('exact node features differ from edges')


def _write(path,values):
    # Hex is lossless and avoids Python's decimal digit limit for exact large denominators.
    with path.open('xb') as stream:
        for value in values:stream.write((format(value.numerator,'x')+'/'+format(value.denominator,'x')+'\n').encode('ascii'))
        stream.flush();os.fsync(stream.fileno())


def save_btc_graph(directory,value):
    validate_exact(value);directory=Path(directory);durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    graph_manifest=save_graph(directory/'graph',value.graph)
    for name,values in (('edge_satoshis',value.edge_satoshis),('incident_satoshis',value.incident_satoshis)):_write(directory/(name+'.hex'),values)
    manifest={'schema_version':1,'encoding':'hex numerator/denominator, one exact rational per line',
        'graph_manifest_sha256':file_hash(graph_manifest),'fee_satoshis':value.fee_satoshis,
        'observed_chain_order_checked':value.observed_chain_order_checked,
        'qualification':'observed-source overlap only; unobserved prevouts and canonical chain remain provider/provenance dependent',
        'sidecars':{name:{'sha256':file_hash(directory/(name+'.hex')),'count':len(values)} for name,values in (('edge_satoshis',value.edge_satoshis),('incident_satoshis',value.incident_satoshis))}}
    with (directory/'manifest.json').open('xb') as stream:stream.write(canonical_bytes(manifest));stream.flush();os.fsync(stream.fileno())
    sync_directory(directory);return directory/'manifest.json'


def load_btc_graph(manifest_path,expected_hash):
    path=Path(manifest_path);raw=path.read_bytes()
    if digest(raw)!=expected_hash:raise ValueError('BTC manifest hash differs')
    metadata=json.loads(raw)
    if metadata['schema_version']!=1 or set(metadata['sidecars'])!={'edge_satoshis','incident_satoshis'}:raise ValueError('BTC sidecar schema differs')
    graph=load_graph(path.parent/'graph/manifest.json',metadata['graph_manifest_sha256']);values={}
    for name,info in metadata['sidecars'].items():
        member=path.parent/(name+'.hex')
        if member.is_symlink() or file_hash(member)!=info['sha256']:raise ValueError('BTC sidecar hash differs')
        result=[]
        with member.open('rt',encoding='ascii') as stream:
            for line in stream:
                if len(result)>=info['count']:raise ValueError('BTC sidecar count differs')
                a,b=line.rstrip('\n').split('/');result.append(Fraction(int(a,16),int(b,16)))
        if len(result)!=info['count'] or file_hash(member)!=info['sha256']:raise ValueError('BTC sidecar count/hash changed')
        values[name]=tuple(result)
    exact=ExactBTCGraph(graph,values['edge_satoshis'],values['incident_satoshis'],metadata['fee_satoshis'],metadata['observed_chain_order_checked'])
    validate_exact(exact);return exact
