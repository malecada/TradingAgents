"""Exact registered one-graph neighborhood census, with no fit or graph rebuild."""
import json
import hashlib
import os
import time
from ..lifecycle import ResearchRun,_immutable
from .mapped_graph import open_mapped_graph
from .neighborhood_census import census
from .provenance import digest,durable_mkdir,sync_directory,require_hash,utc

PREFIX='research_artifacts/onchain-paper-replication-2026-09-24/sources'


def _plan(run,name):
    raw=run.read_input(name);plan=json.loads(raw)
    fields={'schema_version','graph_input','graph_hash','graph_config_hash','node_order_sha256','expected_nodes','expected_edges','edge_chunk','max_output_bytes','max_mapped_bytes','cell_id'}
    if not isinstance(plan,dict) or set(plan)!=fields or type(plan['schema_version']) is not int or plan['schema_version']!=1:raise ValueError('census plan schema differs')
    if any(not isinstance(plan[k],str) or not plan[k] for k in ('graph_input','cell_id')):raise ValueError('census named input/cell required')
    for k in ('graph_hash','graph_config_hash','node_order_sha256'):require_hash(plan[k])
    for k in ('expected_nodes','expected_edges','edge_chunk','max_output_bytes','max_mapped_bytes'):
        if type(plan[k]) is not int or plan[k]<(0 if k=='expected_edges' else 1):raise ValueError('census integer bounds differ')
    if plan['expected_nodes']>3037000499 or plan['edge_chunk']>65536 or plan['max_output_bytes']>512*1024**2 or plan['max_mapped_bytes']>1024**3:raise ValueError('census finite envelope differs')
    if run.admission.experiment['cells']!=[plan['cell_id']]:raise ValueError('census cell denominator differs')
    if set(run.admission.experiment['outputs'])!={'cell-ledger.json','source-summary.json','artifact-index.json'}:raise ValueError('census output denominator differs')
    raw_graph=run.read_input(plan['graph_input']);manifest=json.loads(raw_graph)
    if (manifest['graph_hash']!=plan['graph_hash'] or manifest['metadata']['graph_config_hash']!=plan['graph_config_hash']
            or manifest['arrays']['node_ids']['sha256']!=plan['node_order_sha256']):raise ValueError('census bound graph identity differs')
    info=run.admission.inputs[plan['graph_input']];meta=manifest['metadata']
    if not any(w['dataset']==info['dataset'] and utc(w['start'])<=utc(meta['start_utc'])<utc(meta['end_utc'])<=utc(w['end']) for w in run.admission.experiment['windows']):raise ValueError('census graph outside registered window')
    # Reserve rounded storage for arrays, phase/summary/intent/cell metadata and
    # directory blocks before creating the exclusive output owner.
    logical=8*plan['expected_edges']+32*plan['expected_nodes']+131072
    allocation_unit=os.statvfs(run.admission.root).f_frsize
    if allocation_unit<=0 or logical+32*allocation_unit>plan['max_output_bytes']:raise ValueError('census physical output allowance exceeded')
    return plan,digest(raw),info,logical+32*allocation_unit


def _footprint(directory):
    paths=[directory,*directory.rglob('*')]
    return {'logical_output_bytes':sum(p.stat().st_size for p in paths if p.is_file()),
            'allocated_output_bytes':sum(p.stat().st_blocks*512 for p in paths)}


def produce_registered_census(run,plan_input):
    if not isinstance(run,ResearchRun):raise ValueError('admitted census run required')
    run._active();run._check_source()
    plan,plan_hash,info,reserved=_plan(run,plan_input)
    root=run.admission.root;directory=root/PREFIX/run.admission.experiment_id
    ancestor=directory
    while not ancestor.exists():ancestor=ancestor.parent
    if not directory.resolve().is_relative_to(root.resolve()) or ancestor.stat().st_dev!=root.stat().st_dev:
        raise ValueError('census output must remain on the guarded root filesystem')
    durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    identity={'graph_hash':plan['graph_hash'],'graph_config_hash':plan['graph_config_hash'],
              'node_order_sha256':plan['node_order_sha256'],'graph_manifest_sha256':info['sha256'],
              'plan_sha256':plan_hash,'claim_sha256':run._claim_sha256}
    _immutable(directory/'intent.json',{'identity':identity,'source_commit':run.admission.source,'reserved_allocated_bytes':reserved})
    begin=time.monotonic()
    summary={'schema_version':1,'identity':identity,'graph_hash':plan['graph_hash'],'financial_run_admitted':False,
             'qualification':'exact weak one-hop cardinality only; no induced-edge, matching, MCM or fit feasibility claim'}
    try:
        with open_mapped_graph(root/info['path'],info['sha256'],max_mapped_bytes=plan['max_mapped_bytes']) as graph:
            if len(graph.node_ids)!=plan['expected_nodes'] or graph.edge_index.shape[1]!=plan['expected_edges']:raise ValueError('census graph shape differs')
            result=census(graph.edge_index,len(graph.node_ids),directory/'census',identity=identity,
                edge_chunk=plan['edge_chunk'],max_output_bytes=plan['max_output_bytes'])
        summary.update(status='complete',result=result,cardinalities_path=str((directory/'census/cardinalities.npy').relative_to(root)))
        row={'id':plan['cell_id'],'status':'complete','nodes':result['nodes'],'graph_hash':plan['graph_hash']}
    except Exception as error:
        message=str(error)
        summary.update(status='failed',reason=type(error).__name__[:128]+': '+message[:2048],
            reason_truncated=len(message)>2048,reason_sha256=hashlib.sha256(message.encode()).hexdigest())
        row={'id':plan['cell_id'],'status':'failed','reason':summary['reason']}
    summary.update(elapsed_seconds=time.monotonic()-begin,prepublication_storage=_footprint(directory),
        prepublication_storage_scope='producer directory before result and cell publication; lifecycle outputs excluded; final complete accounting is emitted to guarded child log')
    if summary['prepublication_storage']['allocated_output_bytes']>plan['max_output_bytes']:
        summary.update(status='failed',reason='census allocated output allowance exceeded')
        row={'id':plan['cell_id'],'status':'failed','reason':summary['reason']}
    _immutable(directory/'result.json',summary);_immutable(directory/(plan['cell_id']+'.json'),row)
    # Lifecycle outputs and their finite metadata allowance are reserved above.
    return [row],summary,directory


def finalize_registered_storage(run,directory,plan_input):
    """Measure after all producer files and three lifecycle outputs are durable.

    Emit to the retained guard log, outside the counted artifact roots, avoiding
    a self-referential accounting file. A quota failure prevents run completion.
    Guard telemetry/claim/terminal metadata are explicitly outside this scope.
    """
    maximum=json.loads(run.read_input(plan_input))['max_output_bytes']
    roots=[directory,run.directory/'outputs'];paths=[p for root in roots for p in [root,*root.rglob('*')]]
    value={'kind':'census_final_storage_accounting','experiment':run.admission.experiment_id,
           'roots':[str(p.relative_to(run.admission.root)) for p in roots],
           'files':sorted(str(p.relative_to(run.admission.root)) for p in paths if p.is_file()),
           'logical_bytes':sum(p.stat().st_size for p in paths if p.is_file()),
           'allocated_bytes':sum(p.stat().st_blocks*512 for p in paths),
           'maximum_bytes':maximum,
           'scope':'complete producer directory and three lifecycle outputs, including directory blocks; guard telemetry and lifecycle claim/terminal excluded'}
    value['within_allowance']=value['allocated_bytes']<=maximum and value['logical_bytes']<=maximum
    print(json.dumps(value,sort_keys=True),flush=True)
    if not value['within_allowance']:raise RuntimeError('final census storage allowance exceeded; published evidence retained')
    return value
