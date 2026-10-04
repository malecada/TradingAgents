"""Admitted optional index execution and retained-sample numeric limits."""
import json


def validate_neighborhood_policy(value):
    if value is None:return None
    fields={'schema_version','mode','max_buffer_bytes','edge_chunk','max_sample_array_bytes'}
    if (not isinstance(value,dict) or set(value)!=fields
            or type(value['schema_version']) is not int or value['schema_version']!=1
            or value['mode']!='array'
            or any(type(value[k]) is not int or value[k]<=0 for k in ('max_buffer_bytes','edge_chunk','max_sample_array_bytes'))):
        raise ValueError('neighborhood execution policy differs')
    return dict(value)


def read_neighborhood_policy(run,input_name):
    if input_name is None:return None
    if not isinstance(input_name,str) or not input_name:raise ValueError('neighborhood policy input required')
    value=validate_neighborhood_policy(json.loads(run.read_input(input_name)))
    if value is None:raise ValueError('neighborhood policy object required')
    return value


def require_neighborhood_arm(arm,policy):
    if policy is not None and arm not in {'proposed','mcm_without_gat','training_label_permutation'}:
        raise ValueError('neighborhood policy unused by representation arm')


def open_array_index(graph,policy):
    from .array_neighborhoods import ArrayNeighborhoodIndex
    return ArrayNeighborhoodIndex(graph,max_buffer_bytes=policy['max_buffer_bytes'],edge_chunk=policy['edge_chunk'])


def sample_array_bytes(graph):
    return sum(getattr(graph,k).nbytes for k in ('node_features','edge_index','edge_features'))


def check_sample_records(value,policy):
    """Check exact float64/int64 decoder sizes before constructing any arrays.

    Retained prior samples plus twice one graph's payload fit the separate sample
    and buffer allowances. Parsed JSON/Python metadata is outside these bounds.
    """
    if policy is None:return
    def rectangle(rows,integer=False):
        if not isinstance(rows,(list,tuple)):raise ValueError('sample array rows required')
        width=None
        for row in rows:
            if not isinstance(row,(list,tuple)):raise ValueError('sample array row required')
            if width is None:width=len(row)
            if len(row)!=width:raise ValueError('ragged sample array')
            if any(type(x) not in ((int,) if integer else (int,float)) for x in row):raise ValueError('sample array scalar differs')
        return len(rows),width or 0
    total=0
    for graph in value['graphs']:
        n,nw=rectangle(graph['node_features']);directions,e=rectangle(graph['edge_index'],True)
        erows,ew=rectangle(graph['edge_features'])
        if (n!=len(graph['node_ids']) or n<1 or nw<1 or directions!=2 or erows!=e
                or type(graph['edge_width']) is not int or graph['edge_width']<1
                or (e and ew!=graph['edge_width'])):
            raise ValueError('sample array dimensions differ')
        size=8*(n*nw+2*e+erows*ew);total+=size
        if total>policy['max_sample_array_bytes']:raise ValueError('retained sample array allowance exceeded')
        if 2*size>policy['max_buffer_bytes']:raise ValueError('sample array decoder buffer allowance exceeded')
