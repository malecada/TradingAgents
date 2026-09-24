"""Matched cell execution and immutable per-date prediction evidence."""
from dataclasses import asdict
from pathlib import Path
import json
import os
import io
import hashlib
import numpy as np
import torch
from scipy.special import expit
from ..lifecycle import _immutable,_lock,ResearchRun
from .provenance import canonical_bytes,digest,file_hash,durable_mkdir,sync_directory
from .dataset import example_binding
from .contracts import Prediction
from .model_registry import build_model,PRICE_ARMS,VECTOR_WIDTHS
from .training import fit_cell,predict_cell,_reserve
from .cells import lifecycle_cell_id
from .cache import read_artifact
from .baselines import permute_training_labels
from .metrics import classification_metrics,regression_metrics


def batch_factory(arm,task,examples,scaler,features,*,permuted=False):
    values=torch.tensor(scaler.transform([x.input_prices for x in examples]),dtype=torch.float32).unsqueeze(-1)
    labels=np.array([x.up for x in examples])
    if permuted:labels=permute_training_labels(labels)
    targets=torch.tensor(labels,dtype=torch.long) if task=='direction' else torch.tensor(scaler.transform([x.target_price for x in examples]),dtype=torch.float32).reshape(-1,1)
    def batch(indices):
        prices=values[indices]
        if arm in PRICE_ARMS:inputs={'x':prices}
        elif arm=='constant_graph':inputs={'prices':prices}
        elif arm in VECTOR_WIDTHS:
            vectors=np.asarray([[features[h] for h in examples[i].graph_hashes] for i in indices])
            inputs={'prices':prices,'graph_vectors':torch.tensor(vectors,dtype=torch.float32)}
        else:inputs={'prices':prices,'graph_sequences':[[features[h] for h in examples[i].graph_hashes] for i in indices]}
        return inputs,targets[indices]
    return batch


def evaluate_cell(run,cell,examples,scaler,features,model_config,training_config,provenance,*,expected_test_mask,feature_binding,output_directory=None,feature_binding_input=None,feature_binding_output=None,example_binding_input=None,example_binding_output=None,continuation=None,completed_fit=None):
    """The caller admits graph/dictionary artifacts; this function enforces their binding."""
    examples.require_test_mask(expected_test_mask)
    validate_scientific_cell(cell)
    registered_id=lifecycle_cell_id(cell['id'])
    validate_cell_admission(run,registered_id,provenance)
    decisions=[x.decision_at for x in examples.test]
    if len(set(decisions))!=len(decisions) or decisions!=sorted(decisions) or digest(canonical_bytes(decisions))!=examples.test_mask_hash:raise ValueError('actual test decision membership differs')
    validate_manifest(run,example_binding_input,example_binding_output,example_binding(examples,scaler))
    if provenance['cell_id']!=registered_id or provenance['fold_id']!=cell['fold'] or tuple(sorted(provenance['source_hashes']))!=tuple(sorted(examples.source_hashes)):raise ValueError('cell/fold/source binding differs')
    if digest(canonical_bytes([asdict(x) for x in examples.train]))!=examples.train_hash:raise ValueError('training example bytes differ from membership')
    if not examples.train or not examples.test:raise ValueError('empty fixed train/test population')
    if scaler.train_hash!=examples.train_hash or provenance['input_hash']!=examples.train_hash:raise ValueError('training membership/scaler mismatch')
    if cell['arm'] not in PRICE_ARMS|{'constant_graph'}:
        expected_representation='motif_mcm' if cell['arm'] in {'proposed','mcm_without_gat','training_label_permutation'} else cell['arm']
        if feature_binding.get('representation')!=expected_representation or feature_binding.get('asset')!=cell['asset']:raise ValueError('feature representation/asset differs from requested cell')
        if feature_binding.get('fold_id')!=cell['fold'] or feature_binding.get('train_hash')!=examples.train_hash or feature_binding.get('dictionary_hash')!=provenance['dictionary_hash']:raise ValueError('feature fitted provenance mismatch')
        if feature_binding.get('seed')!=cell['seed'] or feature_binding.get('fold_hash')!=examples.fold_hash:raise ValueError('feature seed/fold binding differs')
        if (feature_binding_input is None)==(feature_binding_output is None):raise ValueError('exactly one admitted feature binding required')
        if feature_binding_input is not None:bound=json.loads(run.read_input(feature_binding_input))
        else:
            path=run.directory/'outputs'/feature_binding_output
            raw=path.read_bytes()
            if run._published_outputs.get(feature_binding_output)!=digest(raw):raise ValueError('feature output not published by this run')
            bound=json.loads(raw)
        if canonical_bytes(bound)!=canonical_bytes(feature_binding):raise ValueError('feature binding differs from admitted artifact')
        if feature_binding.get('feature_hashes')!={h:feature_hash(v) for h,v in features.items()}:raise ValueError('feature tensor bytes differ')
        required={h for x in (*examples.train,*examples.test) for h in x.graph_hashes}
        if set(features)!=required:raise ValueError('graph feature membership differs from common population')
    config_identity=digest(canonical_bytes({'model':model_config,'training':training_config,'cell':{k:cell[k] for k in ('id','lane','asset','arm','task','seed','fold','variant')},'feature_binding':feature_binding,'scaler':asdict(scaler)}))
    if provenance['config_hash']!=config_identity:raise ValueError('cell configuration identity differs')
    directory=prediction_directory(run,registered_id)
    if output_directory is not None and Path(output_directory).resolve()!=directory.resolve():raise ValueError('prediction output must use the admitted run artifact root')
    durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    _immutable(directory/'claim.json',{'scientific_id':cell['id'],'lifecycle_id':registered_id,'provenance':provenance,'test_mask_hash':expected_test_mask})
    try:
        arm=cell['arm'];task=cell['task'];factory=lambda:build_model(arm,task,model_config)
        train=batch_factory(arm,task,examples.train,scaler,features,permuted=arm=='training_label_permutation')
        test=batch_factory(arm,task,examples.test,scaler,features)
        if completed_fit is not None:
            if continuation is not None:raise ValueError('fit continuation and prediction recovery are exclusive')
            model,checkpoint_hash=recover_completed_model(run,registered_id,provenance,completed_fit,factory,arm)
            if arm=='svm':
                x,_=test(list(range(len(examples.test))));x=x['x'].numpy().reshape(len(examples.test),-1)
                prediction=expit(model.decision_function(x)) if task=='direction' else scaler.inverse(model.predict(x))
            else:
                output=predict_cell(model,test,len(examples.test),training_config['batch_size'])
                prediction=torch.softmax(output,1)[:,1].numpy() if task=='direction' else scaler.inverse(output[:,0].numpy())
        elif arm=='svm':
            if continuation is not None:raise ValueError('SVM has no mid-fit continuation; recover a completed model only')
            import joblib
            fit_directory=_reserve(run,registered_id,provenance,None)
            try:
                model=factory();x,y=train(list(range(len(examples.train))));model.fit(x['x'].numpy().reshape(len(y),-1),y.numpy().reshape(-1))
                model_path=fit_directory/'model.joblib'
                with model_path.open('xb') as stream:
                    joblib.dump(model,stream);stream.flush();os.fsync(stream.fileno())
                sync_directory(fit_directory)
                checkpoint_hash=file_hash(model_path)
                _immutable(fit_directory/'complete.json',{'checkpoint':str(model_path),'sha256':checkpoint_hash,'provenance':provenance})
                x,_=test(list(range(len(examples.test))));x=x['x'].numpy().reshape(len(examples.test),-1)
                prediction=expit(model.decision_function(x)) if task=='direction' else scaler.inverse(model.predict(x))
            except BaseException as error:
                _immutable(directory/'failed.json',{'reason':type(error).__name__+': '+str(error)})
                if not (fit_directory/'complete.json').exists():_immutable(fit_directory/'failed.json',{'reason':type(error).__name__+': '+str(error)})
                raise
        else:
            fitted=fit_cell(run,registered_id,provenance,factory,train,len(examples.train),'classification' if task=='direction' else 'regression',cell['seed'],training_config,continuation=continuation)
            output=predict_cell(fitted.model,test,len(examples.test),training_config['batch_size']);checkpoint_hash=fitted.checkpoint_hash
            prediction=torch.softmax(output,1)[:,1].numpy() if task=='direction' else scaler.inverse(output[:,0].numpy())
        rows=[]
        for example,value in zip(examples.test,prediction,strict=True):
            row=Prediction(cell['lane'],cell['asset'],arm,cell['fold'],cell['seed'],example.decision_at,example.label_start,example.label_end,example.max_input_available_at,float(example.up if task=='direction' else example.target_price),float(value) if task=='direction' else None,float(value) if task=='regression' else None,checkpoint_hash)
            rows.append(asdict(row))
        summary=classification_metrics([r['y_true'] for r in rows],prediction) if task=='direction' else regression_metrics([r['y_true'] for r in rows],prediction)
        _immutable(directory/'predictions.json',rows)
        _immutable(directory/'cell.json',{'id':cell['id'],'lifecycle_id':registered_id,'status':'complete','provenance':provenance,'test_mask_hash':examples.test_mask_hash,'train_hash':examples.train_hash,'scaler':asdict(scaler),'prediction_hash':file_hash(directory/'predictions.json'),'checkpoint_hash':checkpoint_hash,'metrics':summary,'probability_qualification':'uncalibrated sigmoid SVC margin' if arm=='svm' and task=='direction' else 'softmax' if task=='direction' else None})
        return rows,summary
    except BaseException as error:
        if not (directory/'failed.json').exists():_immutable(directory/'failed.json',{'reason':type(error).__name__+': '+str(error),'scientific_id':cell['id'],'lifecycle_id':registered_id,'fit_may_already_be_complete':True,'next_action':'Inspect immutable fit completion; only a new registered continuation or prediction-only recovery may proceed.'})
        raise


def reuse_cell(path,*,cell_id,expected_provenance,expected_test_mask):
    """Exact first-stage identity reuse, never refitting the initial25 paper cells."""
    path=Path(path);record=json.loads((path/'cell.json').read_bytes())
    if record['id']!=cell_id or record['status']!='complete' or record['provenance']!=expected_provenance or record['test_mask_hash']!=expected_test_mask:raise ValueError('completed cell reuse identity differs')
    if file_hash(path/'predictions.json')!=record['prediction_hash']:raise ValueError('completed prediction bytes differ')
    return json.loads((path/'predictions.json').read_bytes()),record


def prediction_directory(run,registered_id):
    return run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/predictions'/run.admission.experiment_id/registered_id


def feature_hash(value):
    h=hashlib.sha256()
    def feed(item):
        if isinstance(item,torch.Tensor):item=item.detach().cpu().numpy()
        if isinstance(item,np.ndarray):
            array=np.ascontiguousarray(item)
            if array.dtype.hasobject:raise ValueError('object feature arrays forbidden')
            h.update(canonical_bytes({'shape':array.shape,'dtype':str(array.dtype)}));h.update(memoryview(array).cast('B'))
        elif isinstance(item,dict):
            for key in sorted(item):h.update(canonical_bytes(key));feed(item[key])
        else:h.update(canonical_bytes(item))
    feed(value);return h.hexdigest()


def recover_completed_model(run,cell_id,provenance,recovery,factory,arm):
    """Registered prediction-only recovery; completed fitting is never repeated."""
    validate_cell_admission(run,cell_id,provenance)
    old=recovery['provenance'];parent=run.admission.experiment['parent']
    if parent is None or parent==run.admission.experiment_id:raise ValueError('prediction recovery requires registered prior parent')
    if {k:v for k,v in old.items() if k!='source_commit'}!={k:v for k,v in provenance.items() if k!='source_commit'}:raise ValueError('recovery science differs')
    completion=json.loads(run.read_input(recovery['completion_input']))
    checkpoint_info=run.admission.inputs[recovery['checkpoint_input']]
    run.read_input(recovery['checkpoint_input'])
    checkpoint=run.admission.root/checkpoint_info['path']
    previous=run.admission.root/'research_artifacts/onchain_fit_cells'/digest(cell_id.encode())/parent
    completion_path=run.admission.root/run.admission.inputs[recovery['completion_input']]['path']
    if completion_path.resolve()!=(previous/'complete.json').resolve() or not checkpoint.resolve().is_relative_to(previous.resolve()):raise ValueError('recovery not from completed parent fit')
    if Path(completion['checkpoint']).resolve()!=checkpoint.resolve() or completion['sha256']!=file_hash(checkpoint):raise ValueError('recovery checkpoint differs')
    if arm=='svm':
        import joblib
        if completion.get('provenance')!=old:raise ValueError('SVM recovered provenance differs')
        model=joblib.load(checkpoint)
    else:
        data=read_artifact(checkpoint,old);state=torch.load(io.BytesIO(data['state.pt']),map_location='cpu',weights_only=True)
        model=factory();model.load_state_dict(state['model'],strict=True)
    return model,file_hash(checkpoint)


def validate_cell_admission(run,cell_id,provenance):
    if not isinstance(run,ResearchRun):raise ValueError('admitted run required')
    with _lock(run.admission.root):
        run._active();run._check_source()
        if cell_id not in run.admission.experiment['cells']:raise ValueError('unregistered evaluation cell')
        if provenance['cell_id']!=cell_id or provenance['source_commit']!=run.admission.source:raise ValueError('evaluation source/cell mismatch')


def validate_manifest(run,input_name,output_name,expected):
    if (input_name is None)==(output_name is None):raise ValueError('exactly one admitted example binding required')
    if input_name is not None:body=run.read_input(input_name)
    else:
        path=run.directory/'outputs'/output_name;body=path.read_bytes()
        if run._published_outputs.get(output_name)!=digest(body):raise ValueError('example output not published by this run')
    if canonical_bytes(json.loads(body))!=canonical_bytes(expected):raise ValueError('example bytes differ from admitted manifest')


def validate_scientific_cell(cell):
    if '/' in cell['id']:
        actual=cell['id'].split('/')
        expected=[str(cell[k]) for k in ('lane','asset','fold','seed','task','arm','variant')]
        if actual!=expected:raise ValueError('scientific cell identity contradicts its fields')
    lifecycle_cell_id(cell['id'])
