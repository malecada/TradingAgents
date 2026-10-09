"""File-streamed graph checkpoints; no pickle and no full JSON array materialization."""
from pathlib import Path
import json
import os
import numpy as np
from .contracts import GraphSnapshot,validate_graph
from .neighborhoods import graph_hash
from .provenance import canonical_bytes,file_hash,sync_directory,durable_mkdir


def save_graph(directory,graph):
    directory=Path(directory);durable_mkdir(directory.parent);directory.mkdir();sync_directory(directory.parent)
    arrays={'node_features':graph.node_features,'edge_index':graph.edge_index,'edge_features':graph.edge_features,'node_ids':np.asarray(graph.node_ids)}
    if graph.edge_aggregates is not None:arrays['edge_aggregates']=graph.edge_aggregates
    for name,value in arrays.items():
        with (directory/(name+'.npy')).open('xb') as stream:np.save(stream,value,allow_pickle=False);stream.flush();os.fsync(stream.fileno())
    meta={name:getattr(graph,name) for name in ('asset','start_utc','end_utc','available_at','source_hashes','graph_config_hash','raw_count','admitted_count')}
    meta['exclusion_counts']=dict(graph.exclusion_counts)
    manifest={'metadata':meta,'graph_hash':graph_hash(graph),'arrays':{name:{'path':name+'.npy','sha256':file_hash(directory/(name+'.npy')),'bytes':(directory/(name+'.npy')).stat().st_size} for name in arrays}}
    with (directory/'manifest.json').open('xb') as stream:stream.write(canonical_bytes(manifest)+b'\n');stream.flush();os.fsync(stream.fileno())
    sync_directory(directory);return directory/'manifest.json'


def load_graph(manifest_path,expected_hash):
    path=Path(manifest_path)
    if file_hash(path)!=expected_hash:raise ValueError('graph manifest hash differs')
    manifest=json.loads(path.read_bytes());arrays={}
    for name,info in manifest['arrays'].items():
        if name not in {'node_features','edge_index','edge_features','node_ids','edge_aggregates'} or info['path']!=name+'.npy':raise ValueError('invalid graph member')
        member=path.parent/info['path']
        if member.is_symlink() or file_hash(member)!=info['sha256']:raise ValueError('graph member hash differs')
        arrays[name]=np.load(member,allow_pickle=False,mmap_mode='r')
    arrays['node_ids']=tuple(arrays['node_ids'].tolist());g=GraphSnapshot(**manifest['metadata'],**arrays)
    validate_graph(g)
    if graph_hash(g)!=manifest['graph_hash']:raise ValueError('graph content identity differs')
    return g
