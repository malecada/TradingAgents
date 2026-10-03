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
TRANSFER_KIND='original-import-held-score-selected-transfer-v2'
COMBINED_KIND='selected-combined-f64-f32-source-closure-v2'
RAW_KIND='original-import-held-score-completed-f32-v3'
_WORKER=None
_LOCK=threading.RLock()
def require(value,message):
    if not value:raise ValueError(message)
def _policy(p,graphs,outputs):
    if type(p) is dict and type(p.get('schema_version')) is int and p['schema_version']==3:
        require(p.get('kind')==RAW_KIND,'explicit completed raw held policy kind')
        legacy=dict(p,schema_version=2,kind=TRANSFER_KIND)
        _policy(legacy,graphs,outputs)
        return p
    if type(p) is dict and type(p.get('schema_version')) is int and p['schema_version']==2:
        roles={'population_input','network_release_input','source_closure_input'}
        require(set(p)=={'schema_version','kind','targets','part_bytes','max_read_bytes','max_members'}|roles and p['kind']==TRANSFER_KIND,'selected held policy exact fields')
        require(all(type(p[k]) is str and 0<len(p[k])<=80 for k in roles) and len({p[k] for k in roles})==3,'distinct registered selected held roles')
        legacy={k:v for k,v in p.items() if k not in roles};legacy.update(schema_version=1,kind=KIND)
        _policy(legacy,graphs,outputs)
        return p
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
    # Canonical package reducer is already in the full admitted package closure.
    from . import owned_io as source_io
    cap=1048576;root_fd=file_fd=None
    def signature(s):
        return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_blocks)
    try:
        require(path.is_absolute() and path.resolve()==path and path.name not in ('','.','..'),'held source redirected')
        parent=path.parent
        root_fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        root_pin=signature(os.fstat(root_fd))
        require(stat.S_ISDIR(os.fstat(root_fd).st_mode) and signature(parent.lstat())==root_pin and parent.resolve()==parent,'held source parent changed')
        before=os.stat(path.name,dir_fd=root_fd,follow_symlinks=False)
        pin=signature(before)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=cap,'held source extent/type')
        file_fd=os.open(path.name,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=root_fd)
        require(signature(os.fstat(file_fd))==pin,'held source changed before open')
        pieces=[];count=0
        while True:
            part=os.read(file_fd,min(65536,before.st_size-count+1))
            if not part:break
            count+=len(part)
            require(count<=before.st_size and count<=cap,'held source grew during bounded read')
            pieces.append(part)
        require(count==before.st_size and signature(os.fstat(file_fd))==pin
            and signature(os.stat(path.name,dir_fd=root_fd,follow_symlinks=False))==pin
            and signature(path.lstat())==pin and path.resolve()==path,'held source changed during read')
        require(signature(os.fstat(root_fd))==root_pin and signature(parent.lstat())==root_pin
            and parent.resolve()==parent,'held source parent changed during read')
        return b''.join(pieces)
    finally:
        source_io._cleanup((() if file_fd is None else (lambda:os.close(file_fd),))
            + (() if root_fd is None else (lambda:os.close(root_fd),)))

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
    if p['schema_version'] in (2,3):_worker_current(run,p)
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
        if p['schema_version']==2:
            worker=_worker_current(run,p)
            operation=worker.context.bind(reader).claim()
            operation.dispatch()
            worker.context.check()
    held.check(owner);target.check();compact_owner.verify_current(owner)
    again=_route(target);require(again is not None and again[0] is run and again[1:3]==(name,raw),'held policy changed during readback')
    observation={'schema_version':1,'kind':KIND,'status':'local-byte-readback','target':target.key,'owner':owner.identity,'stage':stage.name,'policy_input':name,'policy_sha256':hashlib.sha256(raw).hexdigest(),'readback':result,'scientific_publication':False,'transport_authority':False,'local_bytes_retired':0}
    require(len(json.dumps(observation,sort_keys=True,allow_nan=False).encode())<=8192,'held output metadata bound')
    run.write_json(output,observation)
    held.check(owner);target.check();compact_owner.verify_current(owner)
    require(owner.active is stage and not stage.closed,'held stage changed during publication')


# No context or approval is retained across worker scopes. This capability wraps
# the real registered Context; it never replaces the original resource Owner.
def _transfer_scope(selected,item,p):
    require(type(selected) is dict and type(item) is dict and set(item)==set(selected)|{'binding_output','journal_output'} and all(item[k]==v for k,v in selected.items()),'whole selected producer/job differs')
    require(selected.get('non_tail_transport_input')==p['population_input'],'selected population input differs')

def _transfer_outputs(p,pop,tx,base,registered):
    values=list(base)+[v['output'] for v in p['targets'].values()]+[pop['receipt_output'],pop['terminal_output']]+list(tx['outputs'].values())
    require(len(base)==4 and len(values)==10 and len(set(values))==10 and set(values)==set(registered),'exact ten disjoint selected worker outputs required')
    return set(values)

def _transfer_json(run,name,limit=8192):
    require(type(name) is str and name in run.admission.inputs,'registered transfer input missing')
    raw=run.read_input(name)
    require(type(raw) is bytes and 0<len(raw)<=limit,'registered transfer input bound')
    value=json.loads(raw)
    require(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'==raw,'canonical transfer input bytes required')
    return raw,value

def _transfer_closure(value,registered,required):
    if type(value) is dict and value.get('kind')==COMBINED_KIND:return _combined_closure(value,registered,required)
    fields={'schema_version','kind','implementation_source_count','package_count','source_files','package_files','auxiliary_source_files'}
    require(type(value) is dict and set(value)==fields and type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='selected-held-transfer-source-closure-v1','typed selected implementation declaration')
    require(type(value['implementation_source_count']) is int and value['implementation_source_count']==201 and type(value['package_count']) is int and value['package_count']==150,'explicit future201/150 closure required')
    code=value['source_files'];package=value['package_files'];aux=value['auxiliary_source_files']
    require(type(code) is dict and len(code)==201 and type(package) is dict and len(package)==150 and type(aux) is dict and len(aux)==5,'exact implementation/package/auxiliary counts')
    require(set(package)==set(required) and package=={k:code.get(k) for k in required} and not set(code).intersection(aux) and registered==code|aux and len(registered)==206,'full package anchor/admission closure differs')
    for name,digest in registered.items():
        require(type(name) is str and name and not Path(name).is_absolute() and Path(name).as_posix()==name and not any(x in ('','.','..') for x in name.split('/')) and type(digest) is str and len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'typed complete source pins')
    return code

def _transfer_auxiliary(run,closure):
    # Original admission owns effective-budget authority. This checks the exact
    # auxiliary/source partition, not a new review or an allowance exemption.
    exp=run.admission.experiment;aux=closure['auxiliary_source_files']
    extension=exp['cumulative_budget_extension'];refs={'budget_extension':extension['extension'],'budget_review':extension['review'],'charter':exp['charter']}
    body=json.loads(_body(run.admission.root/refs['budget_extension']['path']))
    refs['budget_allocation']=body['allocation']
    paths=set()
    for ref in refs.values():
        require(type(ref) is dict and set(ref)=={'path','sha256'} and aux.get(ref['path'])==ref['sha256'] and ref['path'] not in paths,'original auxiliary registered references differ')
        raw=_body(run.admission.root/ref['path']);require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'original auxiliary body differs')
        paths.add(ref['path'])
    remaining=set(aux)-paths;require(len(remaining)==1,'exact separate auxiliary declaration required')
    name=next(iter(remaining));raw=_body(run.admission.root/name)
    require(len(raw)<=8192 and hashlib.sha256(raw).hexdigest()==aux[name],'bounded registered auxiliary declaration differs')
    declaration=json.loads(raw)
    expected={'schema_version':1,'kind':'selected-held-auxiliary-source-metadata-v1','program_id':run.admission.spec['program_id'],'experiment_id':run.admission.experiment_id,'implementation_source_count':201,'package_count':150,'implementation_map_sha256':hashlib.sha256(json.dumps(closure['source_files'],sort_keys=True,separators=(',',':')).encode()+b'\n').hexdigest(),'entries':[{'role':role,'reference':refs[role]} for role in sorted(refs)]}
    require(declaration==expected and json.dumps(expected,sort_keys=True,separators=(',',':')).encode()+b'\n'==raw,'complete selected auxiliary/code/case declaration differs')

def _transfer_budget(p,pop,tx,nodes,chunk,resources):
    # Conservative complete-container metadata+payload bounds, not observations.
    from . import selected_non_tail_transport as engine
    require(type(chunk) is int and chunk>0,'original positive score chunk cells')
    totals=dict(members=0,bytes=0,parts=0,commands=0,rounded=0,channel=0)
    slots={row['graph']:row for row in pop['slots']}
    require(len(slots)==2 and set(slots)==set(nodes) and all(row['role']=='score-batches' for row in slots.values()),'exact two f64-only complete containers')
    for graph,n in nodes.items():
        cells=32*n;chunks=(cells+chunk-1)//chunk
        require(8*cells<=p['max_read_bytes'] and chunks<=p['max_members'],'held original population exceeds read policy before Context birth')
        sizes=[8192]*(2+chunks)+[8*min(chunk,cells-i*chunk) for i in range(chunks)]
        require(len(sizes)<=slots[graph]['max_members'] and sum(sizes)<=slots[graph]['max_bytes'],'registered full-member slot below conservative complete bound')
        # Ledger control embeds the complete member inventory. Avoid known
        # post-birth overflow without weakening the inherited8KiB publication.
        names=['start.json','terminal.json']+[f'chunk-{i:012d}.json' for i in range(chunks)]+[f'chunk-{i:012d}.bin' for i in range(chunks)]
        prototype={'owner':'0'*64,'stage':'mcm-'+graph,'stage_intent_sha256':'0'*64,'source':'0'*40,'claim':'0'*64,'role':'score-batches','scope':{k:'0'*64 for k in ('graph','node_order','dictionary','ordered_motifs','matching','workflow')},'container_sha256':'0'*64,'members':[{'name':name,'sha256':'0'*64,'bytes':size} for name,size in zip(names,sizes,strict=True)]}
        require(len(json.dumps(prototype,sort_keys=True,separators=(',',':')).encode())+1<=8192,'complete original member ledger exceeds inherited8KiB control bound')
        totals['members']+=len(sizes);totals['bytes']+=sum(sizes)
        for size in sizes:
            for offset in range(0,size,tx['part_bytes']):
                width=min(tx['part_bytes'],size-offset)
                totals['parts']+=2;totals['commands']+=3
                totals['rounded']+=engine.charge(0,0,tx['stderr_bytes'],512)+engine.charge(width,0,tx['stderr_bytes'],512)+engine.charge(0,width,tx['stderr_bytes'],512)
                totals['channel']+=2*width+3*(tx['stderr_bytes']+2+512)
    require(totals['parts']<=tx['max_parts'] and totals['commands']<=tx['max_commands'] and totals['rounded']<=tx['max_rounded_bytes'] and totals['channel']<=tx['max_channel_bytes'],'both targets exceed finite cumulative transfer policy')
    require(totals['parts']//2<=pop['max_parts'] and totals['commands']<=pop['max_commands'] and totals['rounded']<=pop['max_rounded_bytes'],'both targets exceed proposal budget')
    require(totals['commands']*(tx['command_seconds']+tx['cleanup_seconds'])<=pop['deadline_seconds']<=resources['wall_seconds'],'conservative cumulative commands exceed native deadline')
    local=2*totals['bytes']+totals['commands']*(tx['stderr_bytes']+2)+pop['max_control_bytes']
    files=totals['members']+2*totals['commands']+16
    limits=resources['storage_budget']['limits']
    require(local<=tx['max_local_bytes'] and files<=tx['max_files'] and local+4096*files<=min(limits['max_logical_bytes'],limits['max_allocated_bytes']),'complete local transfer/recovery upper bound exceeds declared storage')
    return totals

def _transfer_preflight_legacy(run,execution,*,job_input='execution_job'):
    from ..lifecycle import ResearchRun
    from . import resource_fixture,archive_non_tail as durable,selected_non_tail_transport as engine,matching_owner,job as job_api,archive_dispatch,owned_io
    require(type(run) is ResearchRun,'actual admitted ResearchRun required before transfer scope')
    run._active();run._check_source();run._check_inputs()
    raw=run.read_input(job_input);require(type(raw) is bytes and len(raw)<=2*1024**2 and json.loads(raw)==execution,'actual complete registered worker job differs')
    resource_fixture.admitted(run.admission,execution)
    _,selected,fixture=resource_fixture.selection(execution)
    require(FIELD in selected and 'non_tail_transport_input' in selected,'explicit selected transfer job required')
    held_raw,p=_transfer_json(run,selected[FIELD]);_policy(p,selected['descriptor']['required_graphs'],run.admission.experiment['outputs'])
    require(p['schema_version']==2,'network route requires schema2; default never activates it')
    plan=json.loads(run.read_input(selected['plan_input']));item=plan['producers'][selected['producer']];_transfer_scope(selected,item,p)
    pop_raw,pop=_transfer_json(run,p['population_input']);durable.validate_policy(pop)
    require(pop['schema_version']==2 and pop['part_bytes']==p['part_bytes'],'same explicit selected population required')
    tx_raw,tx=_transfer_json(run,pop['transport_input']);engine.policy(tx,pop)
    graphs=durable._selection_graphs(run,execution,p['population_input'])
    require(graphs==set(p['targets'])==set(tx['outputs']),'full original target population differs')
    base={item['binding_output'],item['journal_output'],'cell-ledger.json','resource-summary.json'}
    outputs=_transfer_outputs(p,pop,tx,base,run.admission.experiment['outputs'])
    closure_raw,closure=_transfer_json(run,p['source_closure_input'],4*1024**2)
    code=_transfer_closure(closure,run.admission.experiment['source_files'],job_api.required_sources())
    _transfer_auxiliary(run,closure)
    _sources(run)
    fixed={'archive_non_tail.py':'2a146e27460341dcd8aec3219306a5246da0fe6f538c5df69d5e6596c2462bb3','selected_non_tail_transport.py':'abad085e10f3c3a68af89d5b8e849ca30d430ca8464bdbd89bbee1e4e15adb8e','archive_dispatch.py':'eb4dcdafe5deb5c6acba1fdf20610efc9b4ca990c3e3c81f404d8ff8ba4a56b0'}
    for module in (resource_fixture,durable,engine,archive_dispatch,owned_io):
        path=Path(module.__file__);relative='tradingagents/research/onchain_replication/'+path.name
        require(path==run.admission.root/relative and relative in code and hashlib.sha256(_body(path)).hexdigest()==code[relative],'actual selected worker module origin/body differs')
        if path.name in fixed:require(code[relative]==fixed[path.name],'accepted selected dependency differs')
    pair=json.loads(run.read_input(selected['pair_checkpoint_input']))
    matching_owner._source(run,pair['numerical_source'])
    environment=json.loads(run.read_input(execution['environment_input']))
    require(environment==matching_owner.inventory(run.admission.root,include_torch=True),'actual selected runtime differs')
    release_raw,release=_transfer_json(run,p['network_release_input'])
    expected={'schema_version':1,'kind':'registered-held-f64-network-release-v1','program_id':run.admission.spec['program_id'],'experiment_id':run.admission.experiment_id,'job_input':job_input,'job_sha256':hashlib.sha256(raw).hexdigest(),'held_policy_input':selected[FIELD],'held_policy_sha256':hashlib.sha256(held_raw).hexdigest(),'population_input':p['population_input'],'population_sha256':hashlib.sha256(pop_raw).hexdigest(),'transport_input':pop['transport_input'],'transport_sha256':hashlib.sha256(tx_raw).hexdigest(),'source_closure_input':p['source_closure_input'],'source_closure_sha256':hashlib.sha256(closure_raw).hexdigest(),'accounting_kind':'plaintext-pipe-only','execution_scope':'two-original-import-f64-targets'}
    require(release==expected,'genuine registered Root network release/input joins absent or changed')
    compact=json.loads(run.read_input(selected['compact_policy_input']))
    _transfer_budget(p,pop,tx,fixture['target_nodes'],compact['stage_policy']['score_chunk_cells'],execution['resources'])
    guard_base=run.admission.root/job_api.PREFIX/'runs'/run.admission.experiment_id
    guard,_=matching_owner.metadata(guard_base/'owner.json',run.admission.root);launch,_=matching_owner.metadata(guard_base/'launch.json',run.admission.root)
    require(launch['experiment']==run.admission.experiment_id and launch['source_commit']==run.admission.source and all(guard.get(k)==v for k,v in launch.items()),'original native release source/Owner mismatch')
    matching_owner._guard(run,execution['resources'],guard,guard_base)
    return p,outputs

class _TransferWorker:
    def __init__(self,run,execution,job_input):
        self.run=run;self.execution=execution;self.job_input=job_input;self.context=None;self.thread=threading.get_ident()
    def __enter__(self):
        global _WORKER
        from . import archive_dispatch,archive_non_tail
        with _LOCK:
            require(_WORKER is None,'another selected worker scope active')
            p,outputs=transfer_preflight(self.run,self.execution,job_input=self.job_input)
            require(all(name not in self.run._published_outputs and not os.path.lexists(self.run.directory/'outputs'/name) for name in outputs),'selected worker output already reserved before namespace birth')
            context=archive_dispatch.non_tail_context(self.run,policy_input=p['population_input'],job_input=self.job_input)
            self.context=context
            try:
                require(type(context) is archive_non_tail.Context and context.run is self.run,'actual Context required')
                context.check();_WORKER=self
            except BaseException as primary:
                archive_non_tail.close_all([lambda:context.close(primary)],primary)
        return self
    def __exit__(self,typ,primary,tb):
        global _WORKER
        from . import archive_non_tail
        failure=primary
        try:
            require(_WORKER is self and self.thread==threading.get_ident(),'selected worker ownership changed')
        except BaseException as later:failure=archive_non_tail.select(failure,later)
        try:self.context.close(failure)
        except BaseException as later:failure=archive_non_tail.select(failure,later)
        finally:
            with _LOCK:
                if _WORKER is self:_WORKER=None
        if failure is not None:raise failure
        return False

def transfer_worker(run,execution,*,job_input='execution_job'):
    return _TransferWorker(run,execution,job_input)

def _worker_current(run,p):
    if p['schema_version']==3:return _raw_current(run,p)
    from . import archive_non_tail
    with _LOCK:
        worker=_WORKER
        require(type(worker) is _TransferWorker and worker.run is run and worker.thread==threading.get_ident(),'selected route lacks original live worker scope')
        require(type(worker.context) is archive_non_tail.Context and worker.context.run is run and worker.context.input==p['population_input'],'genuine Context/selected policy differs')
        again,_=transfer_preflight(run,worker.execution,job_input=worker.job_input)
        require(again==p,'selected held policy changed');worker.context.check()
        return worker


def _combined_closure(value,registered,required):
    fields={'schema_version','kind','implementation_source_count','package_count','source_files','package_files','auxiliary_source_files'}
    require(type(value) is dict and set(value)==fields and type(value['schema_version']) is int and value['schema_version']==2 and value['kind']==COMBINED_KIND,'typed selected implementation declaration')
    require(type(value['implementation_source_count']) is int and value['implementation_source_count']==202 and type(value['package_count']) is int and value['package_count']==151,'explicit future202/151 closure required')
    code=value['source_files'];package=value['package_files'];aux=value['auxiliary_source_files']
    require(type(code) is dict and len(code)==202 and type(package) is dict and len(package)==151 and type(aux) is dict and len(aux)==5,'exact implementation/package/auxiliary counts')
    require(set(package)==set(required) and package=={k:code.get(k) for k in required} and not set(code).intersection(aux) and registered==code|aux and len(registered)==207,'full package anchor/admission closure differs')
    for name,digest in registered.items():
        require(type(name) is str and name and not Path(name).is_absolute() and Path(name).as_posix()==name and not any(x in ('','.','..') for x in name.split('/')) and type(digest) is str and len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'typed complete source pins')
    require('tradingagents/research/onchain_replication/completed_f32.py' in package,'complete raw module absent from actual anchor')
    return code

def _combined_auxiliary(run,closure):
    # Original admission owns effective-budget authority. This checks the exact
    # auxiliary/source partition, not a new review or an allowance exemption.
    exp=run.admission.experiment;aux=closure['auxiliary_source_files']
    extension=exp['cumulative_budget_extension'];refs={'budget_extension':extension['extension'],'budget_review':extension['review'],'charter':exp['charter']}
    body=json.loads(_body(run.admission.root/refs['budget_extension']['path']))
    refs['budget_allocation']=body['allocation']
    paths=set()
    for ref in refs.values():
        require(type(ref) is dict and set(ref)=={'path','sha256'} and aux.get(ref['path'])==ref['sha256'] and ref['path'] not in paths,'original auxiliary registered references differ')
        raw=_body(run.admission.root/ref['path']);require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'original auxiliary body differs')
        paths.add(ref['path'])
    remaining=set(aux)-paths;require(len(remaining)==1,'exact separate auxiliary declaration required')
    name=next(iter(remaining));raw=_body(run.admission.root/name)
    require(len(raw)<=8192 and hashlib.sha256(raw).hexdigest()==aux[name],'bounded registered auxiliary declaration differs')
    declaration=json.loads(raw)
    expected={'schema_version':1,'kind':'held-auxiliary-source-metadata-v1','program_id':run.admission.spec['program_id'],'experiment_id':run.admission.experiment_id,'implementation_source_count':202,'package_count':151,'implementation_map_sha256':hashlib.sha256(json.dumps(closure['source_files'],sort_keys=True,separators=(',',':')).encode()+b'\n').hexdigest(),'entry_count':4,'entries':[{'role':role,'reference':dict(refs[role],bytes=len(_body(run.admission.root/refs[role]['path'])))} for role in sorted(refs)]}
    require(declaration==expected and json.dumps(expected,sort_keys=True,separators=(',',':')).encode()+b'\n'==raw,'complete selected auxiliary/code/case declaration differs')

def _combined_preflight(run,execution,*,job_input='execution_job'):
    from ..lifecycle import ResearchRun
    from . import resource_fixture,archive_non_tail as durable,selected_non_tail_transport as engine,matching_owner,job as job_api,archive_dispatch,owned_io
    require(type(run) is ResearchRun,'actual admitted ResearchRun required before transfer scope')
    run._active();run._check_source();run._check_inputs()
    raw=run.read_input(job_input);require(type(raw) is bytes and len(raw)<=2*1024**2 and json.loads(raw)==execution,'actual complete registered worker job differs')
    resource_fixture.admitted(run.admission,execution)
    _,selected,fixture=resource_fixture.selection(execution)
    require(FIELD in selected and 'non_tail_transport_input' in selected,'explicit selected transfer job required')
    held_raw,p=_transfer_json(run,selected[FIELD]);_policy(p,selected['descriptor']['required_graphs'],run.admission.experiment['outputs'])
    require(p['schema_version'] in (2,3),'explicit combined f64 or raw route required')
    plan=json.loads(run.read_input(selected['plan_input']));item=plan['producers'][selected['producer']];_transfer_scope(selected,item,p)
    pop_raw,pop=_transfer_json(run,p['population_input']);durable.validate_policy(pop)
    require(pop['schema_version']==p['schema_version'] and pop['part_bytes']==p['part_bytes'],'same explicit selected population required')
    tx_raw,tx=_transfer_json(run,pop['transport_input']);engine.policy(tx,pop)
    graphs=durable._selection_graphs(run,execution,p['population_input'])
    require(graphs==set(p['targets'])==set(tx['outputs']),'full original target population differs')
    base={item['binding_output'],item['journal_output'],'cell-ledger.json','resource-summary.json'}
    outputs=_transfer_outputs(p,pop,tx,base,run.admission.experiment['outputs'])
    closure_raw,closure=_transfer_json(run,p['source_closure_input'],4*1024**2)
    code=_combined_closure(closure,run.admission.experiment['source_files'],job_api.required_sources())
    _combined_auxiliary(run,closure)
    _sources(run)
    fixed={'archive_non_tail.py':'c62e1521969b7665baca6d29b3125be9214d4eb8c4f42f980622d9d670e56fac','selected_non_tail_transport.py':'e3cea797bb51eab1d423399686dfb331b2e4697242f42c7cec1f3f4f026eb7c8','archive_dispatch.py':'eb4dcdafe5deb5c6acba1fdf20610efc9b4ca990c3e3c81f404d8ff8ba4a56b0'}
    for module in (resource_fixture,durable,engine,archive_dispatch,owned_io):
        path=Path(module.__file__);relative='tradingagents/research/onchain_replication/'+path.name
        require(path==run.admission.root/relative and relative in code and hashlib.sha256(_body(path)).hexdigest()==code[relative],'actual selected worker module origin/body differs')
        if path.name in fixed:require(code[relative]==fixed[path.name],'accepted selected dependency differs')
    pair=json.loads(run.read_input(selected['pair_checkpoint_input']))
    matching_owner._source(run,pair['numerical_source'])
    environment=json.loads(run.read_input(execution['environment_input']))
    require(environment==matching_owner.inventory(run.admission.root,include_torch=True),'actual selected runtime differs')
    release_raw,release=_transfer_json(run,p['network_release_input'])
    expected={'schema_version':1,'kind':('registered-combined-held-f64-network-release-v2' if p['schema_version']==2 else 'registered-combined-produced-f32-network-release-v2'),'program_id':run.admission.spec['program_id'],'experiment_id':run.admission.experiment_id,'job_input':job_input,'job_sha256':hashlib.sha256(raw).hexdigest(),'held_policy_input':selected[FIELD],'held_policy_sha256':hashlib.sha256(held_raw).hexdigest(),'population_input':p['population_input'],'population_sha256':hashlib.sha256(pop_raw).hexdigest(),'transport_input':pop['transport_input'],'transport_sha256':hashlib.sha256(tx_raw).hexdigest(),'source_closure_input':p['source_closure_input'],'source_closure_sha256':hashlib.sha256(closure_raw).hexdigest(),'accounting_kind':'plaintext-pipe-only','execution_scope':('two-original-import-f64-targets' if p['schema_version']==2 else 'two-original-import-f32-targets-with-local-held-readback')}
    require(release==expected,'genuine registered Root network release/input joins absent or changed')
    compact=json.loads(run.read_input(selected['compact_policy_input']))
    if p['schema_version']==2:_transfer_budget(p,pop,tx,fixture['target_nodes'],compact['stage_policy']['score_chunk_cells'],execution['resources'])
    else:
        from . import completed_f32
        expected_raw='tradingagents/research/onchain_replication/completed_f32.py'
        require(Path(completed_f32.__file__)==run.admission.root/expected_raw and hashlib.sha256(_body(Path(completed_f32.__file__))).hexdigest()==code[expected_raw],'actual completed raw adapter source differs')
        _combined_budget(p,fixture['target_nodes'],compact['stage_policy']['score_chunk_cells'])
        limits=execution['resources']['storage_budget']['limits']
        require(tx['max_local_bytes']+4096*tx['max_files']<=min(limits['max_logical_bytes'],limits['max_allocated_bytes']),'raw complete transfer reservation exceeds whole native storage budget')
        actual=completed_f32._selected(run,job_input)
        require(actual is not None and actual==(p['population_input'],pop),'actual complete raw budget/policy differs')
    guard_base=run.admission.root/job_api.PREFIX/'runs'/run.admission.experiment_id
    guard,_=matching_owner.metadata(guard_base/'owner.json',run.admission.root);launch,_=matching_owner.metadata(guard_base/'launch.json',run.admission.root)
    require(launch['experiment']==run.admission.experiment_id and launch['source_commit']==run.admission.source and all(guard.get(k)==v for k,v in launch.items()),'original native release source/Owner mismatch')
    matching_owner._guard(run,execution['resources'],guard,guard_base)
    return p,outputs

def _combined_budget(p,nodes,chunk):
    require(type(chunk) is int and chunk>0,'positive original chunk required')
    require(type(nodes) is dict and len(nodes)==2 and set(nodes)==set(p['targets']),'exact raw target held-readback population')
    for n in nodes.values():
        require(type(n) is int and n in (2,3) and 32*n*8<=p['max_read_bytes'] and (32*n+chunk-1)//chunk<=p['max_members'],'raw held readback bound before Context birth')

def transfer_preflight(run,execution,*,job_input='execution_job'):
    from ..lifecycle import ResearchRun
    from . import resource_fixture
    require(type(run) is ResearchRun,'actual admitted ResearchRun required before selection')
    run._active();run._check_source();run._check_inputs()
    _,selected,_=resource_fixture.selection(execution)
    _,p=_transfer_json(run,selected[FIELD]);_policy(p,selected['descriptor']['required_graphs'],run.admission.experiment['outputs'])
    _,closure=_transfer_json(run,p['source_closure_input'],4*1024**2)
    if type(closure) is dict and closure.get('kind')==COMBINED_KIND:return _combined_preflight(run,execution,job_input=job_input)
    require(p['schema_version']==2,'raw route requires explicit combined202 closure')
    return _transfer_preflight_legacy(run,execution,job_input=job_input)

class _RawWorker:
    def __init__(self,run,execution,job_input):
        self.run=run;self.execution=execution;self.job_input=job_input;self.thread=threading.get_ident();self.context=None;self.cm=None
    def __enter__(self):
        global _WORKER
        from . import completed_f32,archive_non_tail
        with _LOCK:
            require(_WORKER is None,'another selected worker scope active')
            p,outputs=transfer_preflight(self.run,self.execution,job_input=self.job_input)
            require(p['schema_version']==3 and all(name not in self.run._published_outputs and not os.path.lexists(self.run.directory/'outputs'/name) for name in outputs),'raw output reserved before Context birth')
            self.cm=completed_f32.completed_worker(self.run,job_input=self.job_input)
            self.context=self.cm.__enter__()
            try:
                require(type(self.context) is archive_non_tail.Context and self.context.run is self.run and self.context.policy['schema_version']==3,'genuine completed raw Context required')
                self.context.check();_WORKER=self
            except BaseException as primary:
                archive_non_tail.close_all([lambda:self.cm.__exit__(type(primary),primary,primary.__traceback__)],primary)
        return self
    def __exit__(self,typ,primary,tb):
        global _WORKER
        from . import archive_non_tail
        failure=primary
        try:require(_WORKER is self and self.thread==threading.get_ident(),'raw worker ownership changed')
        except BaseException as error:failure=archive_non_tail.select(failure,error)
        try:self.cm.__exit__(None if failure is None else type(failure),failure,None if failure is None else failure.__traceback__)
        except BaseException as error:failure=archive_non_tail.select(failure,error)
        finally:
            with _LOCK:
                if _WORKER is self:_WORKER=None
        if failure is not None:raise failure
        return False

def _raw_current(run,p):
    from . import archive_non_tail
    with _LOCK:
        worker=_WORKER
        require(type(worker) is _RawWorker and worker.run is run and worker.thread==threading.get_ident(),'raw route lacks original worker scope')
        require(type(worker.context) is archive_non_tail.Context and worker.context.run is run and worker.context.input==p['population_input'],'genuine raw Context/policy differs')
        again,_=transfer_preflight(run,worker.execution,job_input=worker.job_input);require(again==p,'raw policy changed');worker.context.check();return worker

def raw_transfer_worker(run,execution,*,job_input='execution_job'):
    return _RawWorker(run,execution,job_input)
