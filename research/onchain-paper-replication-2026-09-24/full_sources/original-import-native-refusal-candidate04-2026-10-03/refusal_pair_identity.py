"""Bounded independent identities for the registered two-node synthetic target.

Uses decoded safe little-endian values only; no numerical array or matcher.
Selected source hashes are pinned below and rejoined to the admitted capsule.
The original array-neighborhood and ndarray conversion route still needs its
separately guarded genuine proof; this module grants no execution authority.
"""
import ast,hashlib,json,math,struct
from pathlib import Path
from raw_receipts01 import body,require,digest
from original_semantics import motif_record_identity

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def key(value):return digest(canonical(value))
def pair_body(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
# FORMULA_SOURCE is generated from frozen03's selected source inventory, not
# supplied by a retained matching event or caller-provided identity receipt.
FORMULA_SOURCE={'tradingagents/research/onchain_replication/array_neighborhoods.py': '4130af3869fb6615ba0898c5b25f1297f236e2df6b4dbe37d705dc2459982d6d', 'tradingagents/research/onchain_replication/matching_identity.py': 'f011658abf3b56b04a0ec33a7bdfed2c68e2e2e79791aa96c5ca7f8fd1653f89', 'tradingagents/research/onchain_replication/matching_annealing.py': '602636b8311431bd2f7d4d28ed59627e9ac576341b0dbcc6f0d41225dc79b7d1', 'tradingagents/research/onchain_replication/matching_pair.py': '3fc8a0666b2b4bf334411a85decd7dbf484b038827255714c6727ffe3846621c', 'tradingagents/research/onchain_replication/compact_matcher.py': '6a7e6e0c1918db7a42edc8fe8737f2b77497c0e32583c184e338e286fa47ad70', 'tradingagents/research/onchain_replication/matching_checkpoint.py': '6ef36f12a8e601177c0dde507f99d80853df80ad46cfd7f0321e5c0d655ab9df', 'tradingagents/research/onchain_replication/matching_hardening.py': '3ed02e0df1508a7f963d3652cfea252b759c701235589ea5855cdd560e520f80', 'tradingagents/research/onchain_replication/matching_sparse.py': '06f2d312a1527f335decc8e0c4d1283448a28e783d5e64018d70e9bf3416883e', 'tradingagents/research/onchain_replication/neighborhoods.py': 'b53901125dc20dbb8a38b6e0e539866fb04109053afbcba0d75b2a2a8dc38271', 'tradingagents/research/onchain_replication/contracts.py': '3f88e9e56f2bfca059e2ef9da2b01ae593444b05e1067154653ea6a5479fea1a', 'tradingagents/research/onchain_replication/serialization.py': 'f711a0a931fe9fb91aadf0ad7ba6e68b638f3874e736790e05edd21acdefc65b', 'tradingagents/research/onchain_replication/cache.py': '5fbbe0df14cfc1802dd1df4da6c8bdbd1153a9fcbb4c89dd202e791d1811ddba', 'tradingagents/research/onchain_replication/provenance.py': 'd29f7f5c2fc5d0def6538d3a1eb13dc051c672d8ea38257af333930f87b9ff1b'}

def source_check(root,source_files):
    for name,expected in FORMULA_SOURCE.items():
        require(source_files.get(name)==expected and digest(body(root,name,131072))==expected,'selected identity formula source differs')

def decode_array(raw,*,name):
    require(raw[:8]==b'\x93NUMPY\x01\x00' and 10<=len(raw)<=65536,'bounded safe NPYv1 required')
    size=struct.unpack('<H',raw[8:10])[0];require(size<=10000 and 10+size<=len(raw),'NPY header extent differs')
    h=ast.literal_eval(raw[10:10+size].decode('ascii').strip());require(type(h) is dict and set(h)=={'descr','fortran_order','shape'} and h['fortran_order'] is False,'NPY schema differs')
    shape=h['shape'];require(type(shape) is tuple and all(type(n) is int and 0<=n<=4 for n in shape),'tiny target shape bound')
    data=raw[10+size:]
    if name=='node_ids':
        require(shape==(2,) and type(h['descr']) is str and h['descr'].startswith('<U'),'two-node Unicode target required');width=int(h['descr'][2:]);require(0<width<=128 and len(data)==8*width,'node text extent differs')
        result=[data[i*4*width:(i+1)*4*width].decode('utf-32-le').rstrip('\0') for i in range(2)]
        require(all(result) and len(set(result))==2,'distinct nonempty target nodes required');return result
    expected='<i8' if name=='edge_index' else '<f8';require(h['descr']==expected and len(shape)==2,'explicit little-endian target dtype required')
    count=shape[0]*shape[1];require(len(data)==8*count,'numeric target extent differs');flat=list(struct.unpack('<'+str(count)+('q' if name=='edge_index' else 'd'),data))
    if name=='node_features':require(shape==(2,4),'target node dimensions differ')
    elif name=='edge_index':require(shape[0]==2 and all(0<=x<2 for x in flat),'target edge endpoints differ')
    else:require(name=='edge_features' and shape[1]==2,'target edge feature dimensions differ')
    require(all(math.isfinite(x) for x in flat),'nonfinite target values');return [flat[i*shape[1]:(i+1)*shape[1]] for i in range(shape[0])]

def target_record(root,manifest_path,manifest,inputs):
    require(set(manifest)=={'metadata','graph_hash','arrays'} and set(manifest['arrays'])=={'node_ids','node_features','edge_index','edge_features'},'exact tiny target manifest fields required')
    values={}
    for name,row in manifest['arrays'].items():
        require(set(row)=={'path','sha256','bytes'},'registered target member schema differs');path=str(Path(manifest_path).parent/row['path'])
        require(any(v['path']==path and v['sha256']==row['sha256'] for v in inputs.values()),'target body not registered')
        raw=body(root,path,65536);require(type(row['bytes']) is int and len(raw)==row['bytes'] and digest(raw)==row['sha256'],'target body hash/extent differs');values[name]=decode_array(raw,name=name)
    require(len(values['edge_index'][0])==len(values['edge_index'][1])==len(values['edge_features']),'target edge denominator differs')
    metadata=manifest['metadata'];require(set(metadata)=={'asset','start_utc','end_utc','available_at','source_hashes','graph_config_hash','raw_count','admitted_count','exclusion_counts'},'weekly graph fields differ')
    record=metadata|values|{'edge_aggregates':None};require(key(record)==manifest['graph_hash'],'registered weekly graph identity differs');return record

def local_record(graph,center,config,parent):
    # ArrayNeighborhoodIndex._select: undirected hop expansion, ascending global
    # node indices, induced directed columns retained in original edge order.
    hops=config['hop_depth'];limit=config['maximum_neighborhood_nodes'];require(type(hops) is int and hops>=0 and type(limit) is int and limit>=1,'original neighborhood config differs')
    selected={center};frontier={center};left,right=graph['edge_index']
    for _ in range(hops):
        following=set()
        for a,b in zip(left,right,strict=True):
            if a in frontier:following.add(b)
            if b in frontier:following.add(a)
        following-=selected;selected|=following;require(len(selected)<=limit,'neighborhood capacity exceeded, no truncation');frontier=following
        if not frontier:break
    indices=sorted(selected);mapping={node:i for i,node in enumerate(indices)};keep=[i for i,(a,b) in enumerate(zip(left,right,strict=True)) if a in selected and b in selected]
    return {'node_ids':[graph['node_ids'][i] for i in indices],'node_features':[graph['node_features'][i] for i in indices],'edge_index':[[mapping[graph['edge_index'][axis][i]] for i in keep] for axis in (0,1)],'edge_features':[graph['edge_features'][i] for i in keep],'edge_width':2,'parent_hash':parent,'center_id':graph['node_ids'][center]}

def expected_pairs(root,manifest_path,manifest,inputs,*,numeric,dictionary_config,matching,context,backend,workload,source_files):
    source_check(root,source_files);graph=target_record(root,manifest_path,manifest,inputs)
    components={name+'.py:onchain_replication':source_files['tradingagents/research/onchain_replication/'+name+'.py'] for name in ('matching_checkpoint','matching_annealing','matching_hardening','matching_sparse','matching_identity')}
    motifs=numeric['ordered_motifs'];require(len(motifs)==32,'original32 pair denominator required');result=[]
    for center in range(2):
        local=local_record(graph,center,dictionary_config,manifest['graph_hash']);left,_=motif_record_identity(local)
        for motif,right in enumerate(motifs):
            purpose={'schema_version':1,'kind':'mcm','workload_sha256':workload,'graph_hash':manifest['graph_hash'],'center_index':center,'center_id':graph['node_ids'][center],'motif_index':motif,'typed_graphs':[left,right]}
            ordered={'left':left,'right':right,'configuration':digest(pair_body(matching))}
            identity={'ordered_pair':ordered,'context':context,'backend':backend,'numerical_components':components}
            result.append((key(purpose),digest(pair_body(identity))))
    return result
