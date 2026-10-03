"""Prospective finite genuine cold proof. Imported numerical APIs require guard.

This module never creates a lifecycle claim, substitutes a terminal, or resumes
an identity. The maintained job worker supplies the genuinely admitted run.
"""
import gc
import hashlib
import json
from pathlib import Path
import threading
import weakref
from types import SimpleNamespace

KIND='genuine-compact-cold-engineering-proof-v1'
PROGRAM='compact-cold-engineering-20261003'
IDENTITIES={'materialize':'compact-cold-inputs-20261003-01','compare':'compact-cold-comparison-20261003-01'}
CELL={'materialize':'cold-input-materialization','compare':'cold-genuine-comparison'}
ROOT=Path(__file__).resolve().parents[3]
ARTIFACT='research_artifacts/compact-cold-engineering-20261003'
EXECUTION={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536}
CONFIG_PINS={'recipe': '35a10c4b1e342afe2bff01e6d655b4d93312e07302b2061a237dcea861f56570', 'configs': '1ceae44792c7ff3ff76ce15a7cf79b0267e4a919f56917473862ddf432935a1f', 'model': '29af65736dddfbd22b5ce94c6ff3e507041b00dc81dfcc94c6919a615a68dcb7', 'training': '99fb74a84b85ddff9589e5a8706f8b5ef3807a3f065dfb7091a220a28af63bb3'}
SESSION={}
LOCK=threading.Lock()


def require(value,message):
    if not value:raise ValueError(message)


def _read(run,name):return json.loads(run.read_input(name))


def selected(run,payload):
    """Return exact registered phase, or None only for truly absent selection."""
    name=payload.get('cold_proof_input')
    if name is None:
        require(not any(j.get('cold_proof_input') is not None for j in payload.get('representation_jobs',{}).values()),'unselected cold proof producer')
        return None
    require(set(payload)=={'cold_proof_input','representation_jobs'},'proof payload membership differs')
    from ..lifecycle import ResearchRun
    from . import job,resources
    from .provenance import canonical_bytes,file_hash
    require(type(run) is ResearchRun and type(name) is str,'genuine proof run/input required')
    run._active();run._check_source();run._check_inputs()
    p=_read(run,name)
    require(set(p)=={'schema_version','kind','phase','experiment','output','inputs','source_files','watch','max_file_bytes','max_total_bytes'}
        and type(p['schema_version']) is int and p['schema_version']==1 and p['kind']==KIND,'proof policy schema')
    phase=p['phase'];require(phase in IDENTITIES and p['experiment']==IDENTITIES[phase]==run.admission.experiment_id,'finite proof identity differs')
    require(run.admission.spec['program_id']==PROGRAM and run.admission.experiment['cells']==[CELL[phase]],'separate finite engineering program/cell required')
    require(p['output']=='proof-'+phase+'.json' and p['output'] in run.admission.experiment['outputs'],'proof output differs')
    require(type(p['max_file_bytes']) is int and p['max_file_bytes']==4*1024**2 and type(p['max_total_bytes']) is int and p['max_total_bytes']==256*1024**2,'proof finite payload caps differ')
    inputs={'recipe','model','training','configs','anchor','future_resources'} if phase=='materialize' else {'population','model','training'}
    require(type(p['inputs']) is dict and set(p['inputs'])==inputs and all(type(n) is str and n in run.admission.inputs for n in p['inputs'].values()),'proof input routes differ')
    for role in sorted(set(p['inputs']) & set(CONFIG_PINS)):
        require(hashlib.sha256(canonical_bytes(_read(run,p['inputs'][role]))).hexdigest()==CONFIG_PINS[role],'proof frozen configuration differs: '+role)
    execution=_read(run,'execution_job')
    require(execution['kind']=='fit' and canonical_bytes(execution['payload'])==canonical_bytes(payload),'proof job payload differs')
    require(p['watch']==execution['resources']['storage_budget'],'proof whole-tree watch differs')
    watch=Path(p['watch']['root']);require(watch.is_absolute() and watch.resolve()==watch and (run.admission.root/ARTIFACT).is_relative_to(watch),'proof artifact outside watch')
    require(type(p['source_files']) is dict and p['source_files'],'proof source closure absent')
    required=job.required_sources()|{'tradingagents/research/onchain_replication/compact_cold_proof.py','tradingagents/research/onchain_replication/compact_cold_proof_inputs.py'}
    require(required<=set(p['source_files']),'proof source closure incomplete')
    for rel,sha in p['source_files'].items():
        require(run.admission.experiment['source_files'].get(rel)==sha and file_hash(ROOT/rel)==sha and file_hash(run.admission.root/rel)==sha,'proof source changed: '+rel)
    args=SimpleNamespace(root=run.admission.root,registration=run.admission.registration,experiment=run.admission.experiment_id,source=run.admission.source)
    base=run.admission.root/job.PREFIX/'runs'/run.admission.experiment_id
    owner=json.loads((base/'owner.json').read_bytes());r=execution['resources']
    live=resources.assert_guarded_worker(base/'guard',job._command(args,'worker'),required_paths=[Path(x) for x in r['disk_paths']],wall_seconds=r['wall_seconds'],memory_max_bytes=r['memory_max_bytes'],memory_high_bytes=r['memory_high_bytes'],disk_floor_bytes=r['disk_floor_bytes'])
    require(live.get('owner_identity')==owner and type(live.get('monitor_pid')) is int and live['monitor_pid']==owner['monitor_pid'] and job.same_process_alive(owner['monitor_pid'],owner['monitor_start_ticks']),'proof live native owner differs')
    require(all(k in live and canonical_bytes(live[k])==canonical_bytes(v) for k,v in r.items()),'proof native resource readback differs')
    if phase=='materialize':require(payload['representation_jobs']=={},'materialization cannot fit representations')
    else:
        require(set(payload['representation_jobs'])=={'cold-proof'},'proof representation cardinality differs')
        j=payload['representation_jobs']['cold-proof'];item=_read(run,j['plan_input'])['producers'][j['producer']]
        require(j.get('cold_proof_input')==item.get('cold_proof_input')==name,'proof both-plan route differs')
        require(j.get('compact_cold_handoff_input')==item.get('compact_cold_handoff_input') and type(j.get('compact_cold_handoff_input')) is str,'proof requires admitted cold route')
    return p


def _directory(run):return run.admission.root/ARTIFACT/run.admission.experiment_id


def _write(path,value,cap):
    from . import cold_files
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    require(len(raw)<=cap,'proof JSON cap exceeded')
    info=path.parent.lstat()
    cold_files.write_once(path.parent,(info.st_dev,info.st_ino),path.name,raw,cap)


def _population(run,p):
    from .job_payload import population_from_record
    return population_from_record(_read(run,p['inputs']['population']))


def _batches(examples):
    """Actual consecutive eligible rows, including a calendar gap and short tail."""
    from datetime import datetime,timedelta
    rows=examples.train;n=len(rows);require(n>=32 and n%16,'proof needs full and short train batches')
    groups=[list(range(i,min(i+16,n))) for i in range(0,n,16)]
    gapped=[b for b in groups if len(b)==16 and any(datetime.fromisoformat(rows[v].decision_at.replace('Z','+00:00'))-datetime.fromisoformat(rows[u].decision_at.replace('Z','+00:00'))>timedelta(days=1) for u,v in zip(b,b[1:]))]
    require(gapped,'actual eligible row batch has no calendar gap')
    normal=[b for b in groups if len(b)==16 and b not in gapped]
    require(normal,'actual full ordinary batch missing')
    return [('full',normal[0]),('gapped',gapped[0]),('short',groups[-1])]


def _tree(value):
    import torch
    if isinstance(value,torch.Tensor):return value.detach().cpu().clone()
    if isinstance(value,dict):return {k:_tree(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return type(value)(_tree(v) for v in value)
    return value


def _equal(a,b,path='root'):
    import torch
    require(type(a) is type(b),'comparison type '+path)
    if isinstance(a,torch.Tensor):require(a.dtype==b.dtype and a.shape==b.shape and torch.equal(a,b),'non-bitwise tensor '+path);return 1
    if isinstance(a,dict):
        require(a.keys()==b.keys(),'comparison keys '+path);return sum(_equal(a[k],b[k],path+'/'+str(k)) for k in a)
    if isinstance(a,(tuple,list)):
        require(len(a)==len(b),'comparison length '+path);return sum(_equal(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b,strict=True)))
    require(a==b,'comparison scalar '+path);return 0


def _alias_probe(features,examples,batches):
    keys=max(({h for i in indices for h in examples.train[i].graph_hashes} for _,indices in batches),key=len)
    before=features.live_tensor_bytes();require(before==0,'unexpected entry tensor alias')
    first=features.load_batch(sorted(keys));held=features.live_tensor_bytes()
    require(held==576*len(keys),'actual fixed tensor payload differs from frozen graph shape')
    refused=False
    try:
        second=features.load_batch(sorted(keys))
    except ValueError as error:
        require(str(error)=='aggregate native batch allowance exceeded before allocation','unexpected second-batch refusal')
        refused=True
    require(refused,'second live maximum batch unexpectedly admitted')
    del first;gc.collect();require(features.live_tensor_bytes()==0,'held batch not released')
    return {'distinct_graphs':len(keys),'held_tensor_bytes':held,'second_live_batch_refused':True,'released_tensor_bytes':0}


def _trajectory(run,p,prepared,task,branch):
    """Unchanged full joint model; exact inputs/gradients/optimizer/RNG/reload."""
    import torch
    from .evaluation import batch_factory
    from .model import ReplicationModel
    from .checkpoints import seed_all,save_checkpoint,load_checkpoint,capture_rng
    from .provenance import canonical_bytes,digest
    from . import compact_native_producer
    examples,scaler=_population(run,p)
    cfg=_read(run,p['inputs']['model']);train=_read(run,p['inputs']['training'])
    require(cfg['mcm_input']==32 and cfg['lookback_days']==28 and train['batch_size']==16,'full model/batch dimensions differ')
    rng=seed_all(11);model=ReplicationModel(cfg,'classification' if task=='direction' else 'regression',execution=EXECUTION)
    optimizer=torch.optim.Adam(model.parameters(),lr=train['learning_rate'],betas=tuple(train['betas']),eps=train['epsilon'],weight_decay=train['weight_decay'])
    batches=_batches(examples);batcher=batch_factory('proposed',task,examples.train,scaler,prepared.features)
    provenance={'source_hashes':list(examples.source_hashes),'config_hash':digest(canonical_bytes({'model':cfg,'training':train,'execution':EXECUTION,'task':task})),
        'input_hash':examples.train_hash,'dictionary_hash':prepared.binding['dictionary_hash'],'fold_id':'synthetic-cold','cell_id':CELL['compare'],'source_commit':run.admission.source}
    result={'initial':_tree(model.state_dict()),'alias_probe':_alias_probe(prepared.features,examples,batches),'steps':[]}
    for number,(label,indices) in enumerate(batches):
        inputs,targets=batcher(indices);sequences=inputs['graph_sequences'];by_hash={};originals={}
        for row,index in zip(sequences,indices,strict=True):
            require(len(row)==28,'lookback cardinality differs')
            for graph,h in zip(row,examples.train[index].graph_hashes,strict=True):
                if h in originals:require(graph is originals[h],'repeated graph hash lacks exact object sharing')
                else:originals[h]=graph
        # Input-gradient probe clones fixed MCM leaves once per distinct graph;
        # it does not mutate the leased map or cache learned embeddings.
        fixed=_tree(originals)
        for h,graph in originals.items():by_hash[h]={k:(v.detach().clone().requires_grad_(True) if k=='mcm' else v.detach().clone()) for k,v in graph.items()}
        differentiable={'prices':inputs['prices'].detach().clone().requires_grad_(True),'graph_sequences':[[by_hash[h] for h in examples.train[i].graph_hashes] for i in indices]}
        del row,graph,sequences,originals,inputs
        optimizer.zero_grad(set_to_none=True);model.train();output=model(**differentiable)
        loss=torch.nn.functional.cross_entropy(output,targets) if task=='direction' else torch.nn.functional.mse_loss(output,targets)
        loss.backward()
        gradients={k:_tree(v.grad) for k,v in model.named_parameters()}
        require(all(v is not None for v in gradients.values()),'joint parameter gradient absent')
        for group,parameters in model.parameter_groups().items():require(any(q.grad is not None and torch.count_nonzero(q.grad).item()>0 for q in parameters),'joint block lacks nonzero gradient: '+group)
        observed={'label':label,'indices':indices,'decisions':[examples.train[i].decision_at for i in indices],
            'fixed':fixed,'output':_tree(output),'loss':_tree(loss),'parameter_gradients':gradients,
            'price_gradient':_tree(differentiable['prices'].grad),'mcm_gradients':{h:_tree(g['mcm'].grad) for h,g in by_hash.items()}}
        require(all(v is not None for v in observed['mcm_gradients'].values()),'MCM input gradient absent')
        torch.nn.utils.clip_grad_norm_(model.parameters(),train['gradient_clip_norm']);optimizer.step()
        observed.update(model=_tree(model.state_dict()),optimizer=_tree(optimizer.state_dict()),rng=_tree(capture_rng(rng)))
        result['steps'].append(observed)
        del differentiable,by_hash,output,loss,targets,fixed,gradients,observed
        gc.collect();require(prepared.features.live_tensor_bytes()==0,'fixed feature alias survived batch')
        if number==0:
            path=save_checkpoint(_directory(run)/branch/task/'checkpoint',model,optimizer,rng,provenance,epoch=0,batch=1,logs=[])
            # Consume RNG before reload, then prove the maintained loader restores
            # the checkpoint's actual state and continuation, including all groups.
            restored=ReplicationModel(cfg,'classification' if task=='direction' else 'regression',execution=EXECUTION)
            restored_optimizer=torch.optim.Adam(restored.parameters(),lr=train['learning_rate'],betas=tuple(train['betas']),eps=train['epsilon'],weight_decay=train['weight_decay'])
            state=load_checkpoint(path,restored,restored_optimizer,rng,provenance)
            require(state['epoch']==0 and state['batch']==1 and state['logs']==[],'checkpoint cursor differs')
            _equal(_tree(model.state_dict()),_tree(restored.state_dict()));_equal(_tree(optimizer.state_dict()),_tree(restored_optimizer.state_dict()))
            _equal(result['steps'][-1]['rng'],_tree(capture_rng(rng)))
            model=restored;optimizer=restored_optimizer
            del state,restored,restored_optimizer
    return result


def _save_tensor(path,value,cap):
    import io,torch
    from . import cold_files
    raw=io.BytesIO();torch.save(value,raw);body=raw.getvalue();require(len(body)<=cap,'proof tensor artifact exceeds file cap')
    info=path.parent.lstat();cold_files.write_once(path.parent,(info.st_dev,info.st_ino),path.name,body,cap)
    return hashlib.sha256(body).hexdigest()


def observe(run,published,terminal,resident):
    """Source-pinned observation at actual terminal mint; no injected callback."""
    payload=_read(run,'execution_job')['payload']
    p=selected(run,payload)
    if p is None:return
    require(p['phase']=='compare','materializer cannot observe terminal')
    from . import compact_terminal,compact_publication,compact_closure,compact_training,compact_mcm
    require(type(terminal) is compact_terminal.Receipt and type(published) is compact_publication.Published,'genuine terminal/publication required')
    terminal.check();terminal._verify(full=True)
    closure=published._closure;require(type(closure) is compact_closure.Receipt,'genuine closure required')
    training=compact_mcm._training(closure._dictionary);require(type(training) is compact_training.Training,'genuine training required')
    require(terminal._owner.bound._run is run and training.owner is terminal._owner,'original same-run ancestry differs')
    require(LOCK.acquire(blocking=False),'concurrent proof observation')
    try:
        require(not SESSION,'proof observation already reserved')
        SESSION['state']='reserved';SESSION['experiment']=run.admission.experiment_id
        roots={'terminal':terminal,'published':published,'closure':closure,'training':training,'dictionary':closure._dictionary,'owner':terminal._owner}
        for i,g in enumerate(training.graphs):
            roots['graph-'+str(i)]=g
            for name in ('node_features','edge_index','edge_features'):roots['graph-'+str(i)+'-'+name]=getattr(g,name)
        for i,g in enumerate(closure._graphs):roots['mcm-'+str(i)]=g._features._mcm;roots['matrix-'+str(i)]=g._features._mcm.matrix
        SESSION['refs']={k:weakref.ref(v) for k,v in roots.items()}
        SESSION['alias']=training.graphs[0]
        SESSION['alias_names']={k for k,v in roots.items() if v is SESSION['alias'] or any(v is getattr(SESSION['alias'],n) for n in ('node_features','edge_index','edge_features'))}
        del roots,g
        SESSION['resident_hashes']=dict(resident.features.verified_hashes())
        SESSION['files']={}
        for task in ('direction','regression'):
            result=_trajectory(run,p,resident,task,'resident')
            path=_directory(run)/('resident-'+task+'.pt')
            SESSION['files'][task]=_save_tensor(path,result,p['max_file_bytes']);del result;gc.collect()
        terminal.check();terminal._verify(full=True)
        SESSION['state']='resident-complete'
    except BaseException:
        SESSION['state']='failed';raise
    finally:LOCK.release()


def _release(run):
    require(SESSION.get('state')=='resident-complete' and SESSION['experiment']==run.admission.experiment_id,'proof observation incomplete/foreign')
    gc.collect();alive={k for k,r in SESSION['refs'].items() if r() is not None}
    require(alive==SESSION['alias_names'],'unexpected ancestry retained while external graph alias held: '+str(sorted(alive)))
    SESSION.pop('alias');gc.collect();remaining={k for k,r in SESSION['refs'].items() if r() is not None}
    require(not remaining,'ancestry retained after external alias dropped: '+str(sorted(remaining)))
    return {'observed':sorted(SESSION['refs']),'deliberate_alias_survivors':sorted(alive),'remaining':[]}


def execute(run,payload):
    p=selected(run,payload);require(p is not None,'explicit proof dispatch required')
    from . import cold_files
    from .provenance import durable_mkdir
    directory=_directory(run);durable_mkdir(directory.parent);cold_files.durable_birth(directory)
    _write(directory/'start.json',{'kind':KIND,'phase':p['phase'],'experiment':run.admission.experiment_id,'source':run.admission.source},p['max_file_bytes'])
    try:
        if p['phase']=='materialize':result=materialize(run,p)
        else:
            from . import compact_native_producer
            from .job_payload import _produce_eager_graphs
            from .graph_store import load_graph
            examples,scaler=_population(run,p);_batches(examples)
            j=payload['representation_jobs']['cold-proof'];item=_read(run,j['plan_input'])['producers'][j['producer']]
            prepared=_produce_eager_graphs(run,j['descriptor'],item,j,lambda graphs:compact_native_producer.produce(run,'cold-proof',j,graphs,examples),lambda path,sha:load_graph(path,sha,resident=True))
            compact_native_producer.finalize(prepared)
            release=_release(run);require(prepared.features.verified_hashes()==SESSION['resident_hashes'],'detached features differ')
            import torch
            counts={}
            for task in ('direction','regression'):
                resident_path=directory/('resident-'+task+'.pt')
                require(hashlib.sha256(resident_path.read_bytes()).hexdigest()==SESSION['files'][task],'resident oracle bytes changed')
                previous=torch.load(resident_path,map_location='cpu',weights_only=True)
                actual=_trajectory(run,p,prepared,task,'detached');counts[task]=_equal(previous,actual)
                _save_tensor(directory/('detached-'+task+'.pt'),actual,p['max_file_bytes'])
                del previous,actual;gc.collect()
            compact_native_producer.finalize(prepared)
            result={'status':'complete','release':release,'bitwise_tensor_comparisons':counts,'feature_hashes':prepared.features.verified_hashes(),'memory_saving_proved':False,'fullgraph_capacity_proved':False}
            SESSION['state']='complete'
        files=[f for f in directory.rglob('*') if f.is_file()]
        require(all(not f.is_symlink() and f.stat().st_size<=p['max_file_bytes'] for f in files) and sum(f.stat().st_size for f in files)<=p['max_total_bytes'],'proof final payload capacity differs')
        _write(directory/'complete.json',result,p['max_file_bytes']);run.write_json(p['output'],result)
        return [{'id':CELL[p['phase']],'status':'complete'}],result
    except BaseException as error:
        try:_write(directory/'failed.json',{'status':'failed','type':type(error).__name__,'retained':True},p['max_file_bytes'])
        except BaseException as failure:
            from .cold_files import preserve
            selected_error=preserve(error,failure);raise selected_error
        raise


def materialize(run,p):
    from .compact_cold_proof_inputs import materialize as build
    return build(run,p,_directory(run))
