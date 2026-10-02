"""Finite registered one-graph neural resource checks; never a financial fit.

Full graph allocation/allocator retention are not bounded by checkpointing.
Only the existing owned whole-job guard supplies hard resource containment.
"""
import gc
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import resource
import time
from types import SimpleNamespace
from .score_batches import CleanupFailure

from ..lifecycle import ResearchRun, _immutable, current_metadata_scope
from .provenance import canonical_bytes, digest, file_hash, durable_mkdir, sync_directory, require_hash, utc

WEEKS=('2022-01-03','2022-06-13','2022-07-25','2022-11-07','2023-06-05','2024-01-01','2024-03-11','2024-08-05','2024-12-23')
MODEL_SHA256='29af65736dddfbd22b5ce94c6ff3e507041b00dc81dfcc94c6919a615a68dcb7'
PREFIX='research_artifacts/onchain-paper-replication-2026-09-24/sources'
OUTPUTS={'cell-ledger.json','resource-summary.json','artifact-index.json'}


def _fatal(error):
    import torch
    return not isinstance(error,Exception) or isinstance(error,(MemoryError,torch.OutOfMemoryError))


def _close_checkpoint(stream,primary):
    try:stream.close()
    except BaseException as close_error:
        if primary is not None:
            primary.add_note('checkpoint close uncertainty: '+repr(close_error))
            if _fatal(primary):raise primary
        fatal=close_error if _fatal(close_error) else CleanupFailure('checkpoint close uncertainty; stop worker')
        fatal.add_note(repr(close_error))
        raise fatal from primary


def _bound_worker(run,plan_input):
    from . import job,environment,resources
    value=json.loads(run.read_input('execution_job'));job.job_schema(value)
    if value['kind']!='neural_resource' or value['payload']!={'plan_input':plan_input}:
        raise ValueError('neural producer differs from selected execution_job plan')
    root=run.admission.root;policy=job.resource_policy(value['resources'],root)
    if not job.required_sources()<=set(run.admission.experiment['source_files']):raise ValueError('neural dependency source closure missing')
    if Path(__file__).resolve()!=root/'tradingagents/research/onchain_replication/neural_resource.py':raise ValueError('neural producer imported outside admitted source root')
    args=SimpleNamespace(root=root,registration=run.admission.registration,experiment=run.admission.experiment_id,source=run.admission.source)
    scope=current_metadata_scope()
    if 'physical_policy' in policy:
        if scope is None or scope.root!=root or scope.anchor['experiment']!=args.experiment or scope.anchor['source']!=args.source or scope.policy!=policy['physical_policy']:
            raise ValueError('neural original physical authority required')
        scope.check();args.physical_anchor=scope.anchor_hash
    base=job._base(args);owner=json.loads((base/'owner.json').read_bytes())
    live=resources.assert_guarded_worker(base/'guard',job._command(args,'worker'),
        required_paths=[Path(x) for x in policy['disk_paths']],wall_seconds=policy['wall_seconds'],
        memory_max_bytes=policy['memory_max_bytes'],memory_high_bytes=policy['memory_high_bytes'],disk_floor_bytes=policy['disk_floor_bytes'])
    if live['owner_identity']!=owner or owner['experiment']!=args.experiment or owner['source_commit']!=args.source or any(live[k]!=v for k,v in policy.items()):
        raise ValueError('neural live guard/owner policy differs')
    if environment.inventory(root,include_torch=True)!=json.loads(run.read_input(value['environment_input'])):
        raise ValueError('neural registered Torch environment differs')
    return live


def _namespace(root,directory,expected=None):
    if directory.resolve()!=directory or not directory.is_relative_to(root.resolve()):raise ValueError('neural output namespace redirected')
    ancestor=directory
    while not ancestor.exists():ancestor=ancestor.parent
    if ancestor.stat().st_dev!=root.stat().st_dev:raise ValueError('neural output device differs from guarded root')
    if expected is not None and (directory.stat().st_dev,directory.stat().st_ino)!=expected:raise ValueError('neural owned output namespace changed')


def validate_model(config, checkpointing):
    if type(checkpointing) is not bool or not isinstance(config,dict):raise ValueError('explicit checkpoint policy required')
    value=dict(config)
    if 'graph_activation_checkpointing' in value:
        if type(value['graph_activation_checkpointing']) is not bool or value.pop('graph_activation_checkpointing')!=checkpointing:
            raise ValueError('model/plan checkpoint policy differs')
    if digest(canonical_bytes(value))!=MODEL_SHA256:raise ValueError('original neural model configuration differs')
    return {**value,'graph_activation_checkpointing':checkpointing}


def registered_plan(run,name):
    raw=run.read_input(name);p=json.loads(raw)
    if type(p) is not dict or set(p)!={'schema_version','model_input','graph_activation_checkpointing','cells','limits'} or type(p['schema_version']) is not int or p['schema_version']!=1:
        raise ValueError('neural plan schema differs')
    if type(p['model_input']) is not str or not p['model_input']:raise ValueError('registered model input required')
    config=validate_model(json.loads(run.read_input(p['model_input'])),p['graph_activation_checkpointing'])
    limits=p['limits'];keys={'max_graph_bytes','max_checkpoint_bytes','max_output_bytes','cooperative_cell_seconds'}
    if type(limits) is not dict or set(limits)!=keys or any(type(limits[k]) is not int or limits[k]<=0 for k in keys):raise ValueError('finite neural limits required')
    if limits['cooperative_cell_seconds']>28800 or limits['max_graph_bytes']>6*1024**3 or limits['max_checkpoint_bytes']>1024**3:
        raise ValueError('neural finite envelope differs')
    # Nine retained checkpoints plus metadata, filesystem rounding and lifecycle output allowance.
    if limits['max_output_bytes']<9*limits['max_checkpoint_bytes']+1024**2:raise ValueError('neural output allowance excludes retained checkpoints')
    cells=p['cells'];expected=['neural_checkpoint-'+w for w in WEEKS]
    if type(cells) is not list or len(cells)!=9 or run.admission.experiment['cells']!=expected or set(run.admission.experiment['outputs'])!=OUTPUTS:
        raise ValueError('neural registered denominator differs')
    fields={'cell_id','week','graph_input','graph_hash','graph_config_hash','node_order_sha256','expected_nodes','expected_edges'}
    for cell,week in zip(cells,WEEKS,strict=True):
        if type(cell) is not dict or set(cell)!=fields or cell['cell_id']!='neural_checkpoint-'+week or cell['week']!=week:
            raise ValueError('neural ordered population differs')
        if type(cell['graph_input']) is not str or not cell['graph_input']:raise ValueError('registered graph input required')
        for key in ('graph_hash','graph_config_hash','node_order_sha256'):require_hash(cell[key])
        for key in ('expected_nodes','expected_edges'):
            if type(cell[key]) is not int or cell[key]<(1 if key=='expected_nodes' else 0):raise ValueError('neural graph count differs')
        m=json.loads(run.read_input(cell['graph_input']));info=run.admission.inputs[cell['graph_input']]
        if m['graph_hash']!=cell['graph_hash'] or m['metadata']['graph_config_hash']!=cell['graph_config_hash'] or m['arrays']['node_ids']['sha256']!=cell['node_order_sha256']:
            raise ValueError('neural graph identity differs')
        meta=m['metadata']
        if meta['asset']!='ETH' or utc(meta['start_utc'])!=utc(week+'T00:00:00Z') or utc(meta['end_utc'])!=utc(week+'T00:00:00Z')+timedelta(days=7) or not any(w['dataset']==info['dataset'] and utc(w['start'])<=utc(meta['start_utc'])<utc(meta['end_utc'])<=utc(w['end']) for w in run.admission.experiment['windows']):
            raise ValueError('neural graph outside registered week/window')
        total=0
        for key,member in m['arrays'].items():
            if type(member['bytes']) is not int or member['bytes']<=0:raise ValueError('graph member extent differs')
            total+=member['bytes']
        if total>limits['max_graph_bytes'] or cell['expected_nodes']*128>limits['max_graph_bytes'] or cell['expected_edges']*16>limits['max_graph_bytes']:
            raise ValueError('neural graph declared extent exceeds allowance')
    return p,config,digest(raw)


class _BoundedWriter:
    def __init__(self,stream,maximum):self.stream=stream;self.maximum=maximum
    def write(self,data):
        if self.stream.tell()+len(data)>self.maximum:raise ValueError('checkpoint write allowance exceeded')
        return self.stream.write(data)
    def flush(self):return self.stream.flush()
    def tell(self):return self.stream.tell()


def _state_hash(value):
    """Exact nested scalar/tensor state comparison without copying all tensors."""
    import torch
    h=hashlib.sha256()
    def visit(v):
        if isinstance(v,torch.Tensor):
            a=v.detach().cpu().contiguous().numpy();h.update(str((a.dtype.str,a.shape)).encode());h.update(memoryview(a).cast('B'))
        elif isinstance(v,dict):
            h.update(b'dict')
            for key in sorted(v,key=lambda k:(type(k).__name__,str(k))):visit(key);visit(v[key])
        elif isinstance(v,(tuple,list)):
            h.update(type(v).__name__.encode())
            for child in v:visit(child)
        else:h.update(repr((type(v).__name__,v)).encode())
    visit(value);return h.hexdigest()


def _phase(phases,event):
    if phases is not None:phases.record(event)


def run_cell(graph,config,directory,identity,*,max_checkpoint_bytes,cooperative_seconds,phases=None):
    """One unchanged synthetic update; helper callers must supply outer admission."""
    import numpy as np
    import torch
    from .checkpoints import seed_all,capture_rng,restore_rng
    from .model import ReplicationModel
    begin=time.monotonic()
    def check():
        if time.monotonic()-begin>cooperative_seconds:raise TimeoutError('neural cooperative cell budget exceeded; not a hard per-call deadline')
    _phase(phases,'model_before')
    rng=seed_all(11);model=ReplicationModel(config,'classification')
    _phase(phases,'model_after')
    _phase(phases,'tensor_adapter_before')
    item={'mcm':torch.from_numpy(rng.random((len(graph.node_ids),32),dtype=np.float32)),
          'edge_index':torch.tensor(graph.edge_index.copy(),dtype=torch.long)}
    prices=torch.linspace(-1,1,16*28).reshape(16,28,1);labels=torch.arange(16)%2
    optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    _phase(phases,'tensor_adapter_after')
    check();_phase(phases,'forward_before');out=model([[item]*28 for _ in range(16)],prices)
    _phase(phases,'forward_after')
    _phase(phases,'loss_before')
    loss=torch.nn.functional.cross_entropy(out,labels)
    if not torch.isfinite(loss):raise ValueError('nonfinite resource loss')
    _phase(phases,'loss_after')
    check();_phase(phases,'backward_before');loss.backward();_phase(phases,'backward_after');check()
    _phase(phases,'optimizer_before');optimizer.step();_phase(phases,'optimizer_after');check()
    step_seconds=time.monotonic()-begin
    # Free autograd/large graph tensors before checkpoint serialization.
    loss_value=float(loss.detach());del out,loss,item,prices,labels
    _phase(phases,'checkpoint_before')
    state={'model':model.state_dict(),'optimizer':optimizer.state_dict(),'rng':capture_rng(rng),
           'epoch':1,'batch':0,'identity':identity,'loss':loss_value}
    expected=_state_hash(state);path=Path(directory)/'checkpoint.pt';io=time.monotonic()
    stream=path.open('xb');primary=None
    try:
        torch.save(state,_BoundedWriter(stream,max_checkpoint_bytes));stream.flush();os.fsync(stream.fileno())
    except BaseException as error:primary=error
    finally:_close_checkpoint(stream,primary)
    if primary is not None:
        if _fatal(primary):raise primary
        raise ValueError('checkpoint serialization failed; partial bytes retained') from primary
    sync_directory(path.parent);del state
    _phase(phases,'checkpoint_after')
    check();_phase(phases,'reload_before');loaded=torch.load(path,map_location='cpu',weights_only=True)
    if _state_hash(loaded)!=expected:raise ValueError('checkpoint exact state differs after load')
    model.load_state_dict(loaded['model'],strict=True);optimizer.load_state_dict(loaded['optimizer']);restore_rng(loaded['rng'],rng)
    if _state_hash({'model':model.state_dict(),'optimizer':optimizer.state_dict(),'rng':capture_rng(rng),
                   'epoch':1,'batch':0,'identity':identity,'loss':loss_value})!=expected:
        raise ValueError('checkpoint restored model/optimizer/RNG differs')
    check()
    _phase(phases,'reload_after')
    return {'synthetic':True,'unique_graphs':1,'batch':16,'lookback':28,'optimizer_steps':1,
        'forward_backward_step_seconds':step_seconds,'checkpoint_seconds':time.monotonic()-io,
        'checkpoint_bytes':path.stat().st_size,'checkpoint_sha256':file_hash(path),
        'state_sha256':expected,'checkpoint_roundtrip_exact':True,'loss':loss_value,
        'process_lifetime_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}


def _allocated(directory):return sum(p.stat().st_blocks*512 for p in [directory,*directory.rglob('*')])


def produce_registered_neural_resource(run,plan_input):
    if not isinstance(run,ResearchRun):raise ValueError('admitted neural resource run required')
    run._active();run._check_source();_bound_worker(run,plan_input)
    p,config,plan_hash=registered_plan(run,plan_input)
    root=run.admission.root;directory=root/PREFIX/run.admission.experiment_id
    _namespace(root,directory)
    scope=current_metadata_scope()
    if scope is None:
        durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    elif scope.birth('producer')!=directory:raise ValueError('neural original producer birth differs')
    owned=(directory.stat().st_dev,directory.stat().st_ino)
    _namespace(root,directory,owned)
    identity={'plan_sha256':plan_hash,'claim_sha256':run._claim_sha256,'source_commit':run.admission.source,
              'model_config_sha256':digest(canonical_bytes(config))}
    _immutable(directory/'intent.json',{'identity':identity,'plan':p,'qualification':'synthetic MCM and labels; one graph repeated16x28; no financial fit'})
    run._neural_resource_output=(str(directory),owned,file_hash(directory/'intent.json'))
    rows=[];failure=None;primary=None;publication_errors=[];begin=time.monotonic()
    from .graph_store import load_graph
    from .mapped_graph import open_mapped_graph
    import torch
    torch.set_num_threads(2)
    for index,cell in enumerate(p['cells']):
        row={'id':cell['cell_id'],'status':'unavailable','reason':'earlier cell failed; no retry'}
        if failure is None:
            sub=directory/f'cell-{index:02d}';sub.mkdir();sync_directory(directory)
            try:
                _namespace(root,directory,owned)
                run._active();run._check_source();live=_bound_worker(run,plan_input);run.read_input(cell['graph_input'])
                info=run.admission.inputs[cell['graph_input']]
                phases=None
                if scope is not None:
                    from .neural_phases import PhaseJournal
                    phases=PhaseJournal(scope,sub,{**identity,'cell_id':cell['cell_id'],'graph_manifest_sha256':info['sha256']},Path(live['cgroup']))
                cell_begin=time.monotonic()
                _phase(phases,'graph_validation_before')
                with open_mapped_graph(root/info['path'],info['sha256'],max_mapped_bytes=p['limits']['max_graph_bytes']) as mapped:
                    if len(mapped.node_ids)!=cell['expected_nodes'] or mapped.edge_index.shape[1]!=cell['expected_edges']:raise ValueError('neural mapped graph count differs before resident load')
                _phase(phases,'graph_validation_after')
                if time.monotonic()-cell_begin>p['limits']['cooperative_cell_seconds']:raise TimeoutError('neural cooperative graph validation budget exceeded')
                _phase(phases,'graph_load_before')
                graph=load_graph(root/info['path'],info['sha256'])
                try:
                    if len(graph.node_ids)!=cell['expected_nodes'] or graph.edge_index.shape[1]!=cell['expected_edges']:raise ValueError('neural loaded graph count differs')
                    _phase(phases,'graph_load_after')
                    result=run_cell(graph,config,sub,{**identity,'cell_id':cell['cell_id'],'graph_manifest_sha256':info['sha256']},
                        max_checkpoint_bytes=p['limits']['max_checkpoint_bytes'],cooperative_seconds=p['limits']['cooperative_cell_seconds'],phases=phases)
                finally:del graph
                gc.collect()
                if time.monotonic()-cell_begin>p['limits']['cooperative_cell_seconds']:raise TimeoutError('neural cooperative whole-cell budget exceeded')
                if _allocated(directory)+1024**2>p['limits']['max_output_bytes']:raise ValueError('neural output allowance exceeded')
                row={'id':cell['cell_id'],'status':'complete','result':result}
            except BaseException as error:
                # SIGTERM/SystemExit is terminal too; no next graph or automatic resume.
                primary=error;message=str(error);failure=type(error).__name__+': '+message[:2048]
                row={'id':cell['cell_id'],'status':'failed','reason':failure,'reason_sha256':digest(message.encode())}
            gc.collect()
        rows.append(row)
        try:
            _namespace(root,directory,owned);_immutable(directory/(cell['cell_id']+'.json'),row)
        except BaseException as error:
            publication_errors.append(error)
            if primary is None:primary=error;failure=type(error).__name__+': '+str(error)[:2048]
            else:primary.add_note('neural cell publication failure: '+repr(error))
    summary={'schema_version':1,'identity':identity,'financial_run_admitted':False,'resource_only':True,
        'cells':9,'complete':sum(r['status']=='complete' for r in rows),'failed':sum(r['status']=='failed' for r in rows),
        'unavailable':sum(r['status']=='unavailable' for r in rows),'elapsed_seconds':time.monotonic()-begin,
        'failure':failure,'allocator_release_proven':False,'peak_upper_bound_bytes':None,
        'qualification':'in-process sequential; process-lifetime RSS, not isolated cell peak; graph loader copies and allocator retention remain; outer guard supplies hard whole-job containment'}
    publications=([('failure-ledger.json',rows)] if primary is not None else [])+[('result.json',summary)]
    for name,value in publications:
        try:
            _namespace(root,directory,owned)
            _immutable(directory/name,value)
        except BaseException as error:
            publication_errors.append(error)
            if primary is None:primary=error
            else:primary.add_note('neural '+name+' publication failure: '+repr(error))
    if primary is not None and _fatal(primary):raise primary
    if publication_errors:
        fatal=next((e for e in publication_errors if _fatal(e)),None)
        if fatal is not None:raise fatal from primary
        raise RuntimeError('neural evidence publication failed; preserve failed claim') from primary
    return rows,summary,directory


def finalize_storage(run,directory,plan_input):
    run._active();run._check_source();_bound_worker(run,plan_input)
    expected=run.admission.root/PREFIX/run.admission.experiment_id
    if directory!=expected:raise ValueError('neural final output owner path differs')
    anchor=getattr(run,'_neural_resource_output',None)
    if anchor is None or anchor[0]!=str(directory):raise ValueError('neural owned output identity missing')
    _namespace(run.admission.root,directory,anchor[1])
    if file_hash(directory/'intent.json')!=anchor[2]:raise ValueError('neural owned output intent changed')
    intent=json.loads((directory/'intent.json').read_bytes())
    if intent['identity']['claim_sha256']!=run._claim_sha256:raise ValueError('neural final output claim differs')
    maximum=json.loads(run.read_input(plan_input))['limits']['max_output_bytes']
    measured=_allocated(directory)+_allocated(run.directory/'outputs')
    print(json.dumps({'kind':'neural_resource_final_storage','allocated_bytes':measured,'maximum_bytes':maximum,
        'scope':'producer and lifecycle outputs; guard/claim/terminal excluded'}),flush=True)
    if measured>maximum:raise RuntimeError('neural final output allowance exceeded; evidence retained')
