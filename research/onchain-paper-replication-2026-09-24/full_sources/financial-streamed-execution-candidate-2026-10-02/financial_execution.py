"""Explicit financial execution identity; no admission or numerical import at load."""
import hashlib
import json
from pathlib import Path
SOURCE='tradingagents/research/onchain_replication/streamed_gat.py'
SHA='e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f'
ARMS={'proposed','training_label_permutation'}
PLAN_KEYS={'schema_version','cells','populations','representations','model','training','ledger_output','controls_output'}

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')

def identity(value):
    if value is None:return None
    keys={'policy','policy_sha256','source_path','source_sha256','candidate_sha256'}
    if type(value) is not dict or set(value)!=keys:raise ValueError('financial execution identity fields')
    p=value['policy']
    if type(p) is not dict or set(p)!={'schema_version','backend','block_edges'}:raise ValueError('financial execution policy fields')
    if type(p['schema_version']) is not int or p['schema_version']!=1 or type(p['block_edges']) is not int or p['block_edges']!=65536 or type(p['backend']) is not str or p['backend']!='streamed-gat-mulsum-v1':raise ValueError('financial execution policy differs')
    if any(type(value[k]) is not str for k in keys-{'policy'}) or value['policy_sha256']!=hashlib.sha256(canonical(p)).hexdigest() or value['source_path']!=SOURCE or value['source_sha256']!=SHA or value['candidate_sha256']!=SHA:raise ValueError('financial execution source/hash differs')
    return {**value,'policy':dict(p)}

def authenticate(value):
    selected=identity(value)
    if selected is None:return None
    path=Path(__file__).resolve().parent/'streamed_gat.py'
    if path.resolve()!=path or path.is_symlink() or not 0<path.stat().st_size<=65536:raise ValueError('financial backend source path/extent differs')
    with path.open('rb') as stream:raw=stream.read(65537)
    if len(raw)>65536 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('financial backend source bytes differ')
    return selected

def for_run(run,value):
    selected=authenticate(value)
    if selected is not None:
        expected=run.admission.root/SOURCE
        if Path(__file__).resolve().parent/'streamed_gat.py'!=expected or run.admission.experiment['source_files'].get(SOURCE)!=SHA:raise ValueError('financial backend not selected in admitted source')
    return selected

def plan_selection(plan):
    if set(plan)==PLAN_KEYS and plan['schema_version']==1:return {}
    if set(plan)!=PLAN_KEYS|{'model_execution'} or type(plan['schema_version']) is not int or plan['schema_version']!=2:raise ValueError('batch plan schema differs')
    mapping=plan['model_execution'];present={item['cell']['arm'] for item in plan['cells']}
    if type(mapping) is not dict or not mapping or not set(mapping)<=ARMS & present:raise ValueError('financial selected arm mapping differs')
    if plan['model'].get('graph_activation_checkpointing',False) is not False:raise ValueError('financial streamed checkpoint policy differs')
    result={}
    for arm,value in mapping.items():
        selected=identity(value)
        if selected is None:raise ValueError('selected financial execution binding absent')
        result[arm]=selected
    return result

def attach(model,value):
    selected=authenticate(value)
    if selected is None:raise ValueError('selected model execution missing')
    model._financial_execution=canonical(selected)
    check_model(model,selected)
    return model

def check_model(model,value):
    selected=authenticate(value)
    if selected is None:
        if getattr(model,'execution',None) is not None or hasattr(model,'_financial_execution'):raise ValueError('selected model lacks checkpoint execution binding')
        return
    from .model import ReplicationModel
    from .streamed_gat import GraphAttention
    if type(model) is not ReplicationModel or model.graph_activation_checkpointing is not False or dict(model.execution or {})!=selected['policy'] or getattr(model,'_financial_execution',None)!=canonical(selected):raise ValueError('financial model execution changed or absent')
    if len(model.graph.gat)!=len(model.config['gat_heads']) or any(type(layer) is not GraphAttention or layer.block_edges!=65536 for layer in model.graph.gat):raise ValueError('financial actual GAT backend differs')
    if any(p.device.type!='cpu' or str(p.dtype)!='torch.float32' for p in model.parameters()):raise ValueError('financial selected backend requires CPU float32')

def validate_state(state,provenance):
    selected=identity(provenance.get('model_execution'))
    if 'model_execution' in provenance and selected is None:raise ValueError('explicit checkpoint execution missing')
    if ('model_execution' in state)!=('model_execution' in provenance):raise ValueError('checkpoint execution presence differs')
    if selected is not None and identity(state['model_execution'])!=selected:raise ValueError('checkpoint execution identity differs')
