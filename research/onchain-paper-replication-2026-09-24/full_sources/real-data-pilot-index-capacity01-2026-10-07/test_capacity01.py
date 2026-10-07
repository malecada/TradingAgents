"""Reviewed offline: invented graphs in tmp_path, no network/subprocess/real reads."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_capacity',HERE/'candidate/index_capacity.py')
capacity=importlib.util.module_from_spec(spec);spec.loader.exec_module(capacity)


def fixture(tmp_path):
    inputs={};mapping={}
    for i in range(7):
        p=tmp_path/str(i);p.mkdir();n=8+i;e=n+2
        arrays={'node_features':np.zeros((n,4)), 'edge_index':np.vstack([np.arange(e)%n,(np.arange(e)+1)%n]).astype(np.int64), 'edge_features':np.zeros((e,2))}
        desc={}
        for name,a in arrays.items():
            f=p/(name+'.npy');np.save(f,a);raw=f.read_bytes();desc[name]={'path':f.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        h=hashlib.sha256(str(i).encode()).hexdigest();manifest={'graph_hash':h,'metadata':{'asset':'ETH'},'arrays':desc};f=p/'manifest.json';f.write_text(json.dumps(manifest));raw=f.read_bytes()
        role='graph_'+str(i);inputs[role]={'path':str(f.relative_to(tmp_path)),'sha256':hashlib.sha256(raw).hexdigest()};mapping[h]=role
    config={'maximum_neighborhood_nodes':10,'size':32,'hop_depth':1}
    numeric={'schema_version':1,'edge_chunk':4,'max_buffer_bytes':100000,'max_output_bytes':100000,'max_numeric_bytes':200000}
    return inputs,mapping,numeric,config


def test_exact_constructor_and_output_formula():
    from tradingagents.research.onchain_replication.array_neighborhoods import ArrayNeighborhoodIndex
    from tradingagents.research.onchain_replication.contracts import GraphSnapshot
    g=GraphSnapshot('ETH','2022-01-01T00:00:00Z','2022-01-08T00:00:00Z','2022-01-09T00:00:00Z',('a'*64,),'b'*64,('a','b','c'),np.arange(12,dtype=np.float64).reshape(3,4),np.array([[0,1,2],[1,2,0]],dtype=np.int64),np.arange(6,dtype=np.float64).reshape(3,2),3,3,{})
    v=capacity.demand(3,3,32,16,2,3)
    with ArrayNeighborhoodIndex(g,max_buffer_bytes=v['output_inclusive_buffer_bytes'],edge_chunk=2) as index:
        assert index.buffer_allowance==v['index_additive_bytes']
        result=index.neighborhood(0,{'hop_depth':1,'maximum_neighborhood_nodes':3})
        for name in ('node_features','edge_features','edge_index'):
            np.testing.assert_array_equal(getattr(result,name),getattr(g,name))
    with ArrayNeighborhoodIndex(g,max_buffer_bytes=v['output_inclusive_buffer_bytes']-1,edge_chunk=2) as index:
        with pytest.raises(ValueError,match='output buffer'):index.neighborhood(0,{'hop_depth':1,'maximum_neighborhood_nodes':3})


def test_seven_graph_exact_boundary_and_no_array_load(tmp_path):
    inputs,mapping,numeric,config=fixture(tmp_path)
    with patch.object(np,'load',side_effect=AssertionError('array load forbidden')):
        report=capacity.inspect(tmp_path,inputs,mapping,numeric,config)
        numeric['max_buffer_bytes']=report['max_buffer_required'];numeric['max_output_bytes']=report['max_output_required'];numeric['max_numeric_bytes']=sum(numeric[k] for k in ('max_buffer_bytes','max_output_bytes'))
        assert len(capacity.validate(tmp_path,inputs,mapping,numeric,config)['graphs'])==7
        for field,message in [('max_buffer_bytes','index allowance'),('max_output_bytes','output allowance'),('max_numeric_bytes','numeric allowance')]:
            bad=dict(numeric);bad[field]-=1
            with pytest.raises(ValueError,match=message):capacity.validate(tmp_path,inputs,mapping,bad,config)


@pytest.mark.parametrize('mutation,message', [('missing','seven'),('manifest','SHA'),('hash','join'),('extent','extent'),('width','width'),('symlink','symlink'),('boolean','schema')])
def test_metadata_refusals(tmp_path,mutation,message):
    inputs,mapping,numeric,config=fixture(tmp_path);role=next(iter(inputs));manifest=tmp_path/inputs[role]['path'];edge=manifest.parent/'edge_features.npy'
    if mutation=='missing':mapping.pop(next(iter(mapping)))
    elif mutation=='manifest':manifest.write_bytes(manifest.read_bytes()+b' ')
    elif mutation=='hash':mapping['f'*64]=mapping.pop(next(iter(mapping)))
    elif mutation=='extent':edge.write_bytes(edge.read_bytes()+b' ')
    elif mutation=='symlink':edge.rename(edge.with_name('moved.npy'));edge.symlink_to('moved.npy')
    elif mutation=='boolean':numeric['edge_chunk']=True
    elif mutation=='width':
        np.save(edge,np.zeros((5,4)));data=json.loads(manifest.read_bytes());data['arrays']['edge_features']['bytes']=edge.stat().st_size;manifest.write_text(json.dumps(data));inputs[role]['sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match=message):capacity.validate(tmp_path,inputs,mapping,numeric,config)
