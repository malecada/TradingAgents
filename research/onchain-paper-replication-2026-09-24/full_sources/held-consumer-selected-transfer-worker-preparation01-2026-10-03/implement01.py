from pathlib import Path
p=Path(__file__).parent
f=p/'held_score_consumer.py';s=f.read_text()
s=s.replace("_LOCK=threading.RLock()", "TRANSFER_KIND='original-import-held-score-selected-transfer-v2'\n_WORKER=None\n_LOCK=threading.RLock()")
s=s.replace("def _policy(p,graphs,outputs):\n", """def _policy(p,graphs,outputs):
    if type(p) is dict and type(p.get('schema_version')) is int and p['schema_version']==2:
        roles={'population_input','network_release_input','source_closure_input'}
        require(set(p)=={'schema_version','kind','targets','part_bytes','max_read_bytes','max_members'}|roles and p['kind']==TRANSFER_KIND,'selected held policy exact fields')
        require(all(type(p[k]) is str and 0<len(p[k])<=80 for k in roles) and len({p[k] for k in roles})==3,'distinct registered selected held roles')
        legacy={k:v for k,v in p.items() if k not in roles};legacy.update(schema_version=1,kind=KIND)
        _policy(legacy,graphs,outputs)
        return p
""")
s=s.replace("    _api(run)\n    return name", "    _api(run)\n    if p['schema_version']==2:_worker_current(run,p)\n    return name")
s=s.replace("        result=_read_all(reader,stream.cells,stream.batches.chunk_cells,p['part_bytes'],p['max_read_bytes'],p['max_members'])", """        result=_read_all(reader,stream.cells,stream.batches.chunk_cells,p['part_bytes'],p['max_read_bytes'],p['max_members'])
        if p['schema_version']==2:
            worker=_worker_current(run,p)
            operation=worker.context.bind(reader).claim()
            operation.dispatch()
            worker.context.check()
""".rstrip())
s+='''

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
    require(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\\n'==raw,'canonical transfer input bytes required')
    return raw,value

def _transfer_closure(value,registered,required):
    fields={'schema_version','kind','implementation_source_count','package_count','source_files','package_files','auxiliary_source_files'}
    require(type(value) is dict and set(value)==fields and type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='selected-held-transfer-source-closure-v1','typed selected implementation declaration')
    require(type(value['implementation_source_count']) is int and value['implementation_source_count']==201 and type(value['package_count']) is int and value['package_count']==150,'explicit future201/150 closure required')
    code=value['source_files'];package=value['package_files'];aux=value['auxiliary_source_files']
    require(type(code) is dict and len(code)==201 and type(package) is dict and len(package)==150 and type(aux) is dict and len(aux)==5,'exact implementation/package/auxiliary counts')
    require(set(package)==set(required) and package=={k:code.get(k) for k in required} and not set(code).intersection(aux) and registered==code|aux and len(registered)==206,'full package anchor/admission closure differs')
    for name,digest in registered.items():
        require(type(name) is str and name and not Path(name).is_absolute() and Path(name).as_posix()==name and not any(x in ('','.','..') for x in name.split('/')) and type(digest) is str and len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'typed complete source pins')
    return code

def _transfer_budget(p,pop,tx,nodes,chunk,resources):
    # Conservative complete-container metadata+payload bounds, not observations.
    from . import selected_non_tail_transport as engine
    require(type(chunk) is int and chunk>0,'original positive score chunk cells')
    totals=dict(members=0,bytes=0,parts=0,commands=0,rounded=0,channel=0)
    slots={row['graph']:row for row in pop['slots']}
    require(len(slots)==2 and set(slots)==set(nodes) and all(row['role']=='score-batches' for row in slots.values()),'exact two f64-only complete containers')
    for graph,n in nodes.items():
        cells=32*n;chunks=(cells+chunk-1)//chunk
        sizes=[8192]*(2+chunks)+[8*min(chunk,cells-i*chunk) for i in range(chunks)]
        require(len(sizes)<=slots[graph]['max_members'] and sum(sizes)<=slots[graph]['max_bytes'],'registered full-member slot below conservative complete bound')
        # Ledger control embeds the complete member inventory. Avoid known
        # post-birth overflow without weakening the inherited8KiB publication.
        require(len(sizes)<=16,'worker bounded complete member inventory ceiling16')
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

def transfer_preflight(run,execution,*,job_input='execution_job'):
    from ..runner import ResearchRun
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
            p,_=transfer_preflight(self.run,self.execution,job_input=self.job_input)
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
    from . import archive_non_tail
    with _LOCK:
        worker=_WORKER
        require(type(worker) is _TransferWorker and worker.run is run and worker.thread==threading.get_ident(),'selected route lacks original live worker scope')
        require(type(worker.context) is archive_non_tail.Context and worker.context.run is run and worker.context.input==p['population_input'],'genuine Context/selected policy differs')
        again,_=transfer_preflight(run,worker.execution,job_input=worker.job_input)
        require(again==p,'selected held policy changed');worker.context.check()
        return worker
'''
f.write_text(s)
f=p/'resource_fixture.py';s=f.read_text()
s=s.replace("set(s)==KEYS|{'held_score_consumer_input'})", "set(s)==KEYS|{'held_score_consumer_input'} or set(s)==KEYS|{'held_score_consumer_input','non_tail_transport_input'})")
s=s.replace("    require(s['operation']=='produce'", "    if 'non_tail_transport_input' in s:\n        require(type(s['non_tail_transport_input']) is str and bool(s['non_tail_transport_input']),'explicit selected non-tail input required')\n    require(s['operation']=='produce'",1)
old="        require(len(readbacks)==2 and not outputs.intersection(readbacks) and outputs|readbacks==set(run.admission.experiment['outputs']),'exact six held resource-only outputs required')"
s=s.replace(old,"""        if policy['schema_version']==2:
            held_score_consumer.transfer_preflight(run,job)
        else:
            require('non_tail_transport_input' not in s and 'non_tail_transport_input' not in item,'default local readback forbids implicit transport')
    """+old.strip())
# six-output validation must remain only in else
s=s.replace("    require(len(readbacks)==2", "        require(len(readbacks)==2",1)
s=s.replace("def execute(run,payload,*,job_input='execution_job'):","def _execute_original(run,payload,*,job_input='execution_job'):")
s+='''

def execute(run,payload,*,job_input='execution_job'):
    execution=json.loads(run.read_input(job_input))
    _,selected,_=selection(execution)
    if 'non_tail_transport_input' not in selected:
        return _execute_original(run,payload,job_input=job_input)
    require(job_input=='execution_job','original resource binding requires exact execution_job input')
    require(execution['payload']==payload,'selected caller payload differs from registered bytes')
    # Full original preflight, source/runtime/native checks precede Context and
    # original Owner birth. This does not start another ResearchRun or sampling.
    preflight(run,execution)
    from . import held_score_consumer
    with held_score_consumer.transfer_worker(run,execution,job_input=job_input):
        return _execute_original(run,payload,job_input=job_input)
'''
f.write_text(s)
