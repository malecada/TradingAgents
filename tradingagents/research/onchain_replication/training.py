"""Finite fit engine behind an existing admitted ResearchRun claim."""
from dataclasses import dataclass
from pathlib import Path
import json
import time
import torch
from ..lifecycle import ResearchRun,_lock,_immutable
from .provenance import canonical_bytes,digest,durable_mkdir,sync_directory,file_hash
from .checkpoints import seed_all,save_checkpoint,load_checkpoint


@dataclass
class FitResult:
    model:object
    checkpoint:Path
    checkpoint_hash:str
    logs:list


def _reserve(run,cell_id,provenance,continuation):
    if not isinstance(run,ResearchRun):raise ValueError('admitted ResearchRun required')
    with _lock(run.admission.root):
        run._active();run._check_source()
        if cell_id not in run.admission.experiment['cells']:raise ValueError('unregistered fit cell')
        if provenance['cell_id']!=cell_id or provenance['source_commit']!=run.admission.source:raise ValueError('fit source/cell mismatch')
        root=run.admission.root/'research_artifacts'/'onchain_fit_cells'/digest(cell_id.encode())
        durable_mkdir(root)
        previous=sorted(root.iterdir())
        if previous:
            if continuation is None:raise FileExistsError('fit cell already claimed; explicit new continuation required')
            parent=run.admission.experiment['parent']
            if parent is None or parent==run.admission.experiment_id:raise ValueError('continuation requires new registered parent claim')
            parent_dir=run.admission.root/'research_runs'/parent
            if not (parent_dir/'failed.json').is_file() or (parent_dir/'complete.json').exists():raise ValueError('parent is active or completed; continuation forbidden')
            if len(previous)!=1 or previous[0].name!=parent:raise ValueError('unreviewed continuation chain')
            if not (previous[0]/'failed.json').is_file() or (previous[0]/'complete.json').exists():raise ValueError('parent fit is active or completed; continuation forbidden')
            checkpoint=Path(continuation['checkpoint']).resolve()
            if not checkpoint.is_relative_to(previous[0].resolve()):raise ValueError('checkpoint is not from parent fit')
            if not any(info['sha256']==file_hash(checkpoint) and (run.admission.root/info['path']).resolve()==checkpoint for info in run.admission.inputs.values()):raise ValueError('continuation checkpoint not registered input')
            old=continuation['provenance']
            if {k:v for k,v in old.items() if k!='source_commit'}!={k:v for k,v in provenance.items() if k!='source_commit'}:raise ValueError('continuation scientific provenance mismatch')
        elif continuation is not None:raise ValueError('continuation has no prior fit claim')
        destination=root/run.admission.experiment_id
        destination.mkdir();sync_directory(root)
        _immutable(destination/'claim.json',{'experiment_id':run.admission.experiment_id,'provenance':provenance,'parent_checkpoint':None if continuation is None else str(continuation['checkpoint'])})
        return destination


def fit_cell(run,cell_id,provenance,model_factory,batch_factory,n_examples,task,seed,training_config,*,continuation=None,checkpoint_seconds=600.,after_batch=None):
    """batch_factory supplies registered chronological inputs; no test loss enters fit."""
    if n_examples<=0 or task not in {'regression','classification'}:raise ValueError('invalid fit population/task')
    if training_config['shuffle'] or training_config['scheduler']!='none':raise ValueError('unregistered training schedule')
    if not 0<checkpoint_seconds<=600:raise ValueError('checkpoint interval must be within ten minutes')
    directory=_reserve(run,cell_id,provenance,continuation)
    checkpoint=None
    try:
        rng=seed_all(seed);model=model_factory();model.train()
        optimizer=torch.optim.Adam(model.parameters(),lr=training_config['learning_rate'],betas=tuple(training_config['betas']),eps=training_config['epsilon'],weight_decay=training_config['weight_decay'])
        epoch=0;batch=0;logs=[];loss_sum=0.;count=0;checkpoint=None
        schedule={'training':training_config,'seed':seed,'task':task,'n_examples':n_examples}
        if continuation is not None:
            prior_schedule=Path(continuation['checkpoint']).parents[2]/'schedule.json'
            if canonical_bytes(json.loads(prior_schedule.read_bytes()))!=canonical_bytes(schedule):raise ValueError('continuation training schedule mismatch')
            state=load_checkpoint(continuation['checkpoint'],model,optimizer,rng,continuation['provenance'])
            epoch=state['epoch'];batch=state['batch'];logs=state['logs'];loss_sum=state['epoch_loss'];count=state['epoch_count']
            checkpoint=Path(continuation['checkpoint'])
        size=training_config['batch_size'];epochs=training_config['epochs'];batches=(n_examples+size-1)//size
        if epoch>epochs or batch>=batches or (epoch==epochs and batch):raise ValueError('checkpoint cursor outside registered fit')
        last=time.monotonic()
        _immutable(directory/'schedule.json',schedule)
        while epoch<epochs:
            run._active()
            indices=list(range(batch*size,min((batch+1)*size,n_examples)))
            inputs,targets=batch_factory(indices);optimizer.zero_grad(set_to_none=True)
            output=model(**inputs)
            if output.shape[0]!=len(indices) or len(targets)!=len(indices):raise ValueError('batch population changed')
            if task=='regression' and (output.shape!=(len(indices),1) or targets.shape!=output.shape):raise ValueError('regression target shape must equal [batch,1] output')
            if task=='classification' and (output.shape!=(len(indices),2) or targets.shape!=(len(indices),) or targets.dtype!=torch.long):raise ValueError('classification target shape/dtype')
            loss=torch.nn.functional.cross_entropy(output,targets) if task=='classification' else torch.nn.functional.mse_loss(output,targets)
            if not torch.isfinite(loss):raise ValueError('nonfinite training loss')
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),training_config['gradient_clip_norm'],error_if_nonfinite=True);optimizer.step()
            loss_sum+=float(loss.detach())*len(indices);count+=len(indices);batch+=1
            epoch_end=batch==batches
            if epoch_end:
                logs.append({'epoch':epoch,'loss':loss_sum/count,'examples':count,'seed':seed})
                _immutable(directory/f'epoch-{epoch:04d}.json',logs[-1])
                epoch+=1;batch=0;loss_sum=0.;count=0
            if epoch_end or time.monotonic()-last>=checkpoint_seconds:
                checkpoint=save_checkpoint(directory/'checkpoints',model,optimizer,rng,provenance,epoch=epoch,batch=batch,logs=logs,epoch_loss=loss_sum,epoch_count=count);last=time.monotonic()
            if after_batch is not None:after_batch(epoch,batch,checkpoint)
        _immutable(directory/'complete.json',{'checkpoint':str(checkpoint),'sha256':file_hash(checkpoint),'epochs':epoch})
        return FitResult(model,checkpoint,file_hash(checkpoint),logs)
    except BaseException as error:
        _immutable(directory/'failed.json',{'type':type(error).__name__,'reason':str(error),'last_checkpoint':str(checkpoint) if checkpoint else None})
        raise


def predict_cell(model,batch_factory,n_examples,batch_size):
    model.eval();outputs=[]
    with torch.no_grad():
        for start in range(0,n_examples,batch_size):
            inputs,_=batch_factory(list(range(start,min(start+batch_size,n_examples))))
            output=model(**inputs)
            if output.shape[0]!=min(batch_size,n_examples-start):raise ValueError('prediction population changed')
            if not torch.isfinite(output).all():raise ValueError('nonfinite prediction')
            outputs.append(output.detach().cpu())
    return torch.cat(outputs)
