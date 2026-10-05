"""Finite selected payload accounting; neither scientific nor launch authority."""
import hashlib
import json
import re

KINDS = {'score-tail-f64':80,'score-batch-f64':8,'mcm-output-f32':4}
ASSUMPTION = ('Historical proof authenticates prior full byte and semantic recovery against '
 'the original roster. It does not establish current remote byte availability; '
 'every future restore/use must freshly retrieve and authenticate its bytes.')

def require(ok, message):
    if not ok: raise ValueError(message)

def raw(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def sha(value):return hashlib.sha256(value).hexdigest()

def validate(value):
    require(type(value) is dict and set(value)=={'schema_version','format','assumption','graphs','local_free_floor_bytes','max_control_bytes'},'typed payload policy fields')
    require(type(value['schema_version']) is int and value['schema_version']==1 and value['format']=='typed-payload-budget-v1' and value['assumption']==ASSUMPTION,'explicit selected historical recovery assumption required')
    require(type(value['local_free_floor_bytes']) is int and value['local_free_floor_bytes']>=0,'typed floor')
    require(type(value['max_control_bytes']) is int and 0<value['max_control_bytes']<2**63,'typed cumulative metadata allowance')
    graphs=value['graphs'];require(type(graphs) is dict and 0<len(graphs)<=1024,'finite typed graph roster')
    for graph, entry in graphs.items():
        require(type(graph) is str and re.fullmatch('[0-9a-f]{64}',graph),'typed graph hash')
        require(type(entry) is dict and set(entry)=={'rows','chunk_cells','kinds'},'typed graph fields')
        require(all(type(entry[k]) is int and 0<entry[k]<2**63 for k in ('rows','chunk_cells')) and entry['chunk_cells']<=65536,'typed population bound')
        require(type(entry['kinds']) is dict and set(entry['kinds'])==set(KINDS),'all three original payload types must be explicitly budgeted')
        for kind, budget in entry['kinds'].items():
            require(type(budget) is dict and set(budget)=={'max_operations','max_preserved_bytes','max_recovered_bytes','max_chunks','chunk_bytes'},'typed budget fields')
            require(all(type(v) is int and 0<v<2**63 for v in budget.values()),'finite positive typed budget')
            require(budget['chunk_bytes']<=4*1024**2 and budget['chunk_bytes']%KINDS[kind]==0,'aligned native-bounded typed part')
            if kind=='score-batch-f64':require(budget['chunk_bytes']>=entry['chunk_cells']*8,'original bounded f64 batch must fit registered part')
            require(budget['max_preserved_bytes']>=entry['rows']*32*KINDS[kind],'full original graph payload allowance required')
    return value

def capacity(value):
    validate(value);result=dict(logical_bytes=0,rounded_bytes=0,commands=0,chunks=0)
    for graph in value['graphs'].values():
        for b in graph['kinds'].values():
            # reserve whole finite registered byte envelope; each read rounds at
            # most one transport block above its actual decoded payload.
            p,r,n=b['max_preserved_bytes'],b['max_recovered_bytes'],b['max_chunks']
            result['logical_bytes']+=2*p+r
            result['rounded_bytes']+=2*p+r+2*n*65536
            result['commands']+=4*n
            result['chunks']+=n
    require(all(v<2**63 for v in result.values()),'typed capacity overflow')
    return result
