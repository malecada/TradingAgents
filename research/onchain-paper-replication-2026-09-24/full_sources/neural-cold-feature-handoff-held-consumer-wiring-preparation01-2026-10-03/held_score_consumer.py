"""Explicit imported held-stage local byte readback; no remote/science authority."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import threading

FIELD='held_score_consumer_input'
KIND='original-import-held-score-readback-v1'
SELF='tradingagents/research/onchain_replication/held_score_consumer.py'
PREFIX='research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03'
SOURCES={PREFIX+'/owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb',PREFIX+'/exact_members02.py':'ea1ffcef833344ff1a5fbd89bc2f79ade1414c90a3159329c1f3bdee86bfe0cb',PREFIX+'/held_score_reader.py':'3836bbcdc8b5b1be6a08c47a6d97c76c7c0875eeba7e91e6d363bdc6b4ade209','tradingagents/research/onchain_replication/mcm_score_stream.py':'ee7931cea3d28ad0719b5f3db171a5d5d3ab95db9ff7cad0cc8379101948b79e'}
_LOCK=threading.RLock()
def require(value,message):
    if not value:raise ValueError(message)
def _policy(p,graphs,outputs):
    require(type(p) is dict and set(p)=={'schema_version','kind','targets','part_bytes','max_read_bytes','max_members'},'held consumer policy fields')
    require(type(p['schema_version']) is int and p['schema_version']==1 and p['kind']==KIND,'held consumer policy kind')
    require(type(p['targets']) is dict and set(p['targets'])==set(graphs) and bool(graphs),'held consumer target population')
    names=[]
    for h,value in p['targets'].items():
        require(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h),'held target hash')
        require(type(value) is dict and set(value)=={'output'},'held output fields')
        n=value['output'];require(type(n) is str and n and Path(n).name==n and n.endswith('.json') and n in outputs,'held output unregistered')
        names.append(n)
    require(len(names)==len(set(names)),'held duplicate outputs')
    require(type(p['part_bytes']) is int and 8<=p['part_bytes']<=1048576 and p['part_bytes']%8==0,'held part bound/alignment')
    require(type(p['max_read_bytes']) is int and 0<p['max_read_bytes']<=2**40,'held aggregate bound')
    require(type(p['max_members']) is int and 0<p['max_members']<=32767,'held member bound')
    return p

def _body(path):
    require(path.resolve()==path and not path.is_symlink(),'held source redirected')
    before=path.stat();require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=1048576,'held source extent/type')
    raw=path.read_bytes();after=path.stat()
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns) and len(raw)==before.st_size,'held source changed')
    return raw

def _sources(run):
    from . import mcm_score_stream
    root=run.admission.root;registered=run.admission.experiment['source_files']
    require(Path(__file__).resolve()==root/SELF and Path(mcm_score_stream.__file__).resolve()==root/'tradingagents/research/onchain_replication/mcm_score_stream.py','held source module origin')
    for name,expected in {**SOURCES,SELF:registered.get(SELF)}.items():
        require(type(expected) is str and len(expected)==64 and registered.get(name)==expected and hashlib.sha256(_body(root/name)).hexdigest()==expected,'held selected source closure')

def _api(run):
    _sources(run);root=run.admission.root
    with _LOCK:
        result=None
        for alias,name in [('owned_io','owned_io.py'),('exact_members02','exact_members02.py'),('held_score_reader_selected','held_score_reader.py')]:
            path=root/PREFIX/name
            if alias in sys.modules:
                module=sys.modules[alias];require(Path(getattr(module,'__file__','')).resolve()==path,'held helper module alias collision')
            else:
                spec=importlib.util.spec_from_file_location(alias,path);module=importlib.util.module_from_spec(spec)
                sys.modules[alias]=module
                try:spec.loader.exec_module(module)
                except BaseException:
                    if sys.modules.get(alias) is module:del sys.modules[alias]
                    raise
            result=module
        _sources(run)
        return result

def _route(target):
    from . import imported_mcm_identity,compact_owner
    require(type(target) is imported_mcm_identity.Target and type(target.owner) is compact_owner.Owner,'genuine imported held target required')
    target.check()
    prepared=target.execution._stage.prepared
    selection=prepared._selection_now();selected=selection['selected'];item=selection['producer']
    for value in (selected,item):
        require(not any(type(k) is str and k.startswith('held_score_') and k!=FIELD for k in value),'unknown held selection')
    if FIELD not in selected and FIELD not in item:return None
    name=selected.get(FIELD)
    require(type(name) is str and name and item.get(FIELD)==name,'held job/plan selection differs')
    target.check();owner=target.owner;run=owner.bound._run
    require(owner.bound.record.get('resource_only') is True and name in run.admission.inputs,'held policy not registered resource input')
    raw=run.read_input(name);require(len(raw)<=8192,'held policy metadata bound')
    p=_policy(json.loads(raw),selected['descriptor']['required_graphs'],run.admission.experiment['outputs'])
    reserved={v for obj in (selected,item) for k,v in obj.items() if type(k) is str and k.endswith('_output') and type(v) is str}
    require(not any(v['output'] in reserved for v in p['targets'].values()),'held output conflicts with original producer output')
    require(target.key in p['targets'],'held target not selected')
    _sources(run)
    return run,name,raw,p

def preflight(target):
    route=_route(target)
    if route is None:return None
    run,name,raw,p=route
    cells=32*len(target.graph.node_ids);chunk=target.owner.policy['score_chunk_cells']
    require(type(chunk) is int and chunk>0 and 8*cells<=p['max_read_bytes'] and (cells+chunk-1)//chunk<=p['max_members'],'held original population exceeds read policy before birth')
    output=p['targets'][target.key]['output'];path=run.directory/'outputs'/output
    require(output not in run._published_outputs and not os.path.lexists(path),'held readback output already reserved')
    _api(run)
    return name

def _read_all(reader,cells,chunk_cells,part_bytes,max_bytes,max_members):
    require(type(cells) is int and cells>0 and type(chunk_cells) is int and chunk_cells>0,'held original denominator')
    count=(cells+chunk_cells-1)//chunk_cells
    require(count<=max_members and 8*cells<=max_bytes,'held complete read exceeds finite policy')
    names=tuple('chunk-%012d.bin'%i for i in range(count))
    require(reader.members==names,'held exact ordered member population')
    digest=hashlib.sha256();total=parts=0
    for i,name in enumerate(names):
        size=8*min(chunk_cells,cells-i*chunk_cells)
        for offset in range(0,size,part_bytes):
            width=min(part_bytes,size-offset);raw=reader.read_part(name,offset,width)
            require(type(raw) is bytes and len(raw)==width,'held short/nonbyte read')
            digest.update(raw);total+=width;parts+=1
    require(total==8*cells,'held read denominator differs')
    return {'members':count,'parts':parts,'bytes':total,'sha256':digest.hexdigest()}

def consume(target,stage,held,stream):
    from . import compact_owner,mcm_score_stream
    route=_route(target);require(route is not None,'held consumer unselected')
    run,name,raw,p=route;owner=target.owner
    require(type(stage) is compact_owner.Stage and type(held) is compact_owner._HeldTransition and type(stream) is mcm_score_stream.MCMScoreStream,'genuine held caller objects required')
    held.check(owner);require(owner.active is stage and not stage.closed and stage.owner is owner,'held stage not active')
    output=p['targets'][target.key]['output'];require(output not in run._published_outputs and not os.path.lexists(run.directory/'outputs'/output),'held readback already published')
    api=_api(run)
    with api.open_held(target,stage,held,stream) as reader:
        result=_read_all(reader,stream.cells,stream.batches.chunk_cells,p['part_bytes'],p['max_read_bytes'],p['max_members'])
    held.check(owner);target.check();compact_owner.verify_current(owner)
    again=_route(target);require(again is not None and again[0] is run and again[1:3]==(name,raw),'held policy changed during readback')
    observation={'schema_version':1,'kind':KIND,'status':'local-byte-readback','target':target.key,'owner':owner.identity,'stage':stage.name,'policy_input':name,'policy_sha256':hashlib.sha256(raw).hexdigest(),'readback':result,'scientific_publication':False,'transport_authority':False,'local_bytes_retired':0}
    require(len(json.dumps(observation,sort_keys=True,allow_nan=False).encode())<=8192,'held output metadata bound')
    run.write_json(output,observation)
    held.check(owner);target.check();compact_owner.verify_current(owner)
    require(owner.active is stage and not stage.closed,'held stage changed during publication')
