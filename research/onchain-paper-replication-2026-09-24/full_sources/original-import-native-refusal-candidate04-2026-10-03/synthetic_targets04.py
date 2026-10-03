"""Exact selected deterministic synthetic target generator functions; no IO."""
import hashlib,json,struct,math
from pathlib import Path
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def sha(raw):return hashlib.sha256(raw).hexdigest()

def require(v,m):
    if not v:raise ValueError(m)

def npy(dtype,shape,values):
    require(type(shape) is tuple and shape and all(type(x) is int and 0<x<=32 for x in shape),'finite tiny shape required')
    require(len(values)==math.prod(shape),'NPY values/shape differ')
    if dtype in ('<f8','<i8'):
        require(all(type(x) in (int,float) and not isinstance(x,bool) and math.isfinite(x) for x in values),'finite primitive values required')
        raw=struct.pack('<'+str(len(values))+('d' if dtype=='<f8' else 'q'),*values)
    elif dtype.startswith('<U') and dtype[2:].isdigit():
        width=int(dtype[2:]);require(1<=width<=64 and all(type(x) is str and len(x)<=width for x in values),'bounded Unicode values required')
        raw=b''.join(x.encode('utf-32-le')+b'\0'*(4*(width-len(x))) for x in values)
    else:raise ValueError('explicit safe numeric/Unicode dtype required; no pickle')
    header=repr({'descr':dtype,'fortran_order':False,'shape':shape}).encode('ascii')
    header+=b' '*((-10-len(header)-1)%64)+b'\n'
    require(len(header)<=10000 and len(raw)<=65536,'tiny NPY extent exceeded')
    return b'\x93NUMPY\x01\x00'+struct.pack('<H',len(header))+header+raw

def graphs():
    provenance={'schema_version':1,'kind':'synthetic-original-import-targets','generator':'registered-explicit-arrays-v1','node_denominators':[2,3]}
    files={'fixture_inputs/target-provenance.json':canonical(provenance)};source=sha(files['fixture_inputs/target-provenance.json']);result=[]
    recipes=[([[1.,0.,0.,1.],[0.,1.,1.,0.]],[[0,1],[1,0]],[[1.,0.],[0.,1.]]),([[1.,1.,0.,0.],[0.,1.,0.,1.],[1.,0.,1.,0.]],[[0,1,2],[1,2,0]],[[1.,0.],[0.,1.],[1.,1.]])]
    for i,(nf,ei,ef) in enumerate(recipes,1):
        n=len(nf);ids=[f'synthetic-{i}-{j:02d}' for j in range(n)];prefix=f'fixture_inputs/target-{i:02d}'
        config={'schema_version':1,'data_kind':'synthetic','node_width':4,'edge_width':2,'explicit_recipe':i}
        metadata={'asset':'ETH','start_utc':f'2022-01-{10 if i==1 else 17:02d}T00:00:00Z','end_utc':f'2022-01-{17 if i==1 else 24:02d}T00:00:00Z','available_at':f'2022-01-{17 if i==1 else 24:02d}T00:00:00Z','source_hashes':[source],'graph_config_hash':sha(canonical(config)),'raw_count':len(ef),'admitted_count':len(ef),'exclusion_counts':{}}
        value=metadata|{'node_ids':ids,'node_features':nf,'edge_index':ei,'edge_features':ef,'edge_aggregates':None};identity=sha(canonical(value))
        arrays={'node_ids':npy('<U'+str(max(map(len,ids))),(n,),ids),'node_features':npy('<f8',(n,4),sum(nf,[])),'edge_index':npy('<i8',(2,len(ef)),sum(ei,[])),'edge_features':npy('<f8',(len(ef),2),sum(ef,[]))}
        manifest={'metadata':metadata,'graph_hash':identity,'arrays':{name:{'path':name+'.npy','sha256':sha(raw),'bytes':len(raw)} for name,raw in arrays.items()}}
        for name,raw in arrays.items():files[prefix+'/'+name+'.npy']=raw
        path=prefix+'/manifest.json';files[path]=canonical(manifest)+b'\n';result.append({'graph_hash':identity,'nodes':n,'manifest':path,'sha256':sha(files[path])})
    return sorted(result,key=lambda x:x['graph_hash']),files
