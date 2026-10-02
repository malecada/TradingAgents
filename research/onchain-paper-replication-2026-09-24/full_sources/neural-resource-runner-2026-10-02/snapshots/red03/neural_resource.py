"""Finite registered one-graph neural resource checks; never a financial fit.

Full graph allocation/allocator retention are not bounded by checkpointing.
Only the existing owned whole-job guard supplies hard resource containment.
"""
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import time

from ..lifecycle import ResearchRun, _immutable
from .provenance import canonical_bytes, digest, file_hash, durable_mkdir, sync_directory, require_hash, utc

WEEKS=('2022-01-03','2022-06-13','2022-07-25','2022-11-07','2023-06-05','2024-01-01','2024-03-11','2024-08-05','2024-12-23')
MODEL_SHA256='29af65736dddfbd22b5ce94c6ff3e507041b00dc81dfcc94c6919a615a68dcb7'
PREFIX='research_artifacts/onchain-paper-replication-2026-09-24/sources'
OUTPUTS={'cell-ledger.json','resource-summary.json','artifact-index.json'}


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
        if meta['asset']!='ETH' or meta['start_utc'][:10]!=week or not any(w['dataset']==info['dataset'] and utc(w['start'])<=utc(meta['start_utc'])<utc(meta['end_utc'])<=utc(w['end']) for w in run.admission.experiment['windows']):
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


def run_cell(graph,config,directory,identity,*,max_checkpoint_bytes,cooperative_seconds):
    """One unchanged synthetic update; helper callers must supply outer admission."""
    import numpy as np
    import torch
    from .checkpoints import seed_all,capture_rng,restore_rng
    from .model import ReplicationModel
    begin=time.monotonic()
    def check():
        if time.monotonic()-begin>cooperative_seconds:raise TimeoutError('neural cooperative cell budget exceeded; not a hard per-call deadline')
    rng=seed_all(11);model=ReplicationModel(config,'classification')
    item={'mcm':torch.from_numpy(rng.random((len(graph.node_ids),32),dtype=np.float32)),
          'edge_index':torch.tensor(graph.edge_index.copy(),dtype=torch.long)}
    prices=torch.linspace(-1,1,16*28).reshape(16,28,1);labels=torch.arange(16)%2
    optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    check();out=model([[item]*28 for _ in range(16)],prices)
    loss=torch.nn.functional.cross_entropy(out,labels)
    if not torch.isfinite(loss):raise ValueError('nonfinite resource loss')
    check();loss.backward();check();optimizer.step();check()
    step_seconds=time.monotonic()-begin
    # Free autograd/large graph tensors before checkpoint serialization.
    loss_value=float(loss.detach());del out,loss,item,prices,labels
    state={'model':model.state_dict(),'optimizer':optimizer.state_dict(),'rng':capture_rng(rng),
           'epoch':1,'batch':0,'identity':identity,'loss':loss_value}
    expected=_state_hash(state);path=Path(directory)/'checkpoint.pt';io=time.monotonic()
    with path.open('xb') as stream:
        torch.save(state,_BoundedWriter(stream,max_checkpoint_bytes));stream.flush();os.fsync(stream.fileno())
    sync_directory(path.parent);del state
    check();loaded=torch.load(path,map_location='cpu',weights_only=True)
    if _state_hash(loaded)!=expected:raise ValueError('checkpoint exact state differs after load')
    model.load_state_dict(loaded['model'],strict=True);optimizer.load_state_dict(loaded['optimizer']);restore_rng(loaded['rng'],rng)
    if _state_hash({'model':model.state_dict(),'optimizer':optimizer.state_dict(),'rng':capture_rng(rng),
                   'epoch':1,'batch':0,'identity':identity,'loss':loss_value})!=expected:
        raise ValueError('checkpoint restored model/optimizer/RNG differs')
    check()
    return {'synthetic':True,'unique_graphs':1,'batch':16,'lookback':28,'optimizer_steps':1,
        'forward_backward_step_seconds':step_seconds,'checkpoint_seconds':time.monotonic()-io,
        'checkpoint_bytes':path.stat().st_size,'checkpoint_sha256':file_hash(path),
        'state_sha256':expected,'checkpoint_roundtrip_exact':True,'loss':loss_value,
        'process_lifetime_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}


def _allocated(directory):return sum(p.stat().st_blocks*512 for p in [directory,*directory.rglob('*')])


def produce_registered_neural_resource(run,plan_input):
    if not isinstance(run,ResearchRun):raise ValueError('admitted neural resource run required')
    run._active();run._check_source();p,config,plan_hash=registered_plan(run,plan_input)
    root=run.admission.root;directory=root/PREFIX/run.admission.experiment_id
    if not directory.resolve().is_relative_to(root.resolve()):raise ValueError('neural output outside root')
    durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    identity={'plan_sha256':plan_hash,'claim_sha256':run._claim_sha256,'source_commit':run.admission.source,
              'model_config_sha256':digest(canonical_bytes(config))}
    _immutable(directory/'intent.json',{'identity':identity,'plan':p,'qualification':'synthetic MCM and labels; one graph repeated16x28; no financial fit'})
    rows=[];failure=None;begin=time.monotonic()
    from .graph_store import load_graph
    import torch
    torch.set_num_threads(2)
    for index,cell in enumerate(p['cells']):
        row={'id':cell['cell_id'],'status':'unavailable','reason':'earlier cell failed; no retry'}
        if failure is None:
            sub=directory/f'cell-{index:02d}';sub.mkdir();sync_directory(directory)
            try:
                run._active();run._check_source();run.read_input(cell['graph_input'])
                info=run.admission.inputs[cell['graph_input']]
                graph=load_graph(root/info['path'],info['sha256'])
                try:
                    if len(graph.node_ids)!=cell['expected_nodes'] or graph.edge_index.shape[1]!=cell['expected_edges']:raise ValueError('neural loaded graph count differs')
                    result=run_cell(graph,config,sub,{**identity,'cell_id':cell['cell_id'],'graph_manifest_sha256':info['sha256']},
                        max_checkpoint_bytes=p['limits']['max_checkpoint_bytes'],cooperative_seconds=p['limits']['cooperative_cell_seconds'])
                finally:del graph
                gc.collect()
                if _allocated(directory)+1024**2>p['limits']['max_output_bytes']:raise ValueError('neural output allowance exceeded')
                row={'id':cell['cell_id'],'status':'complete','result':result}
            except BaseException as error:
                # SIGTERM/SystemExit is terminal too; no next graph or automatic resume.
                message=str(error);failure=type(error).__name__+': '+message[:2048]
                row={'id':cell['cell_id'],'status':'failed','reason':failure,'reason_sha256':digest(message.encode())}
            gc.collect()
        rows.append(row);_immutable(directory/(cell['cell_id']+'.json'),row)
    summary={'schema_version':1,'identity':identity,'financial_run_admitted':False,'resource_only':True,
        'cells':9,'complete':sum(r['status']=='complete' for r in rows),'failed':sum(r['status']=='failed' for r in rows),
        'unavailable':sum(r['status']=='unavailable' for r in rows),'elapsed_seconds':time.monotonic()-begin,
        'failure':failure,'allocator_release_proven':False,'peak_upper_bound_bytes':None,
        'qualification':'in-process sequential; process-lifetime RSS, not isolated cell peak; graph loader copies and allocator retention remain; outer guard supplies hard whole-job containment'}
    _immutable(directory/'result.json',summary)
    return rows,summary,directory


def finalize_storage(run,directory,plan_input):
    maximum=json.loads(run.read_input(plan_input))['limits']['max_output_bytes']
    measured=_allocated(directory)+_allocated(run.directory/'outputs')
    print(json.dumps({'kind':'neural_resource_final_storage','allocated_bytes':measured,'maximum_bytes':maximum,
        'scope':'producer and lifecycle outputs; guard/claim/terminal excluded'}),flush=True)
    if measured>maximum:raise RuntimeError('neural final output allowance exceeded; evidence retained')
