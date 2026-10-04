"""Registered complete induced-edge sizing for closed-census oversized centers."""
import hashlib
import json
import os
import time
from pathlib import Path
import numpy as np
from ..lifecycle import ResearchRun,_immutable
from .census_production import PREFIX,_footprint
from .hub_edges import measure
from .mapped_graph import open_mapped_graph
from .provenance import digest,file_hash,require_hash,durable_mkdir,sync_directory,utc


def _json_input(run,name):
    info=run.admission.inputs[name]
    if (run.admission.root/info['path']).stat().st_size>1024**2:raise ValueError('hub compact input bound exceeded')
    return json.loads(run.read_input(name))


def _plan(run,name):
    p=_json_input(run,name)
    fields={'schema_version','graph_input','prior_claim_input','prior_terminal_input','prior_result_input','cardinalities_input','census_experiment','graph_hash','graph_config_hash','node_order_sha256','expected_nodes','expected_edges','expected_centers','threshold','edge_chunk','max_output_bytes','max_buffer_bytes','max_mapped_bytes','cell_ids'}
    if not isinstance(p,dict) or set(p)!=fields or type(p['schema_version']) is not int or p['schema_version']!=1:raise ValueError('hub plan schema differs')
    for k in ('graph_input','prior_claim_input','prior_terminal_input','prior_result_input','cardinalities_input','census_experiment'):
        if not isinstance(p[k],str) or not p[k]:raise ValueError('hub named identity required')
    for k in ('graph_hash','graph_config_hash','node_order_sha256'):require_hash(p[k])
    for k in ('expected_nodes','expected_edges','expected_centers','threshold','edge_chunk','max_output_bytes','max_buffer_bytes','max_mapped_bytes'):
        if type(p[k]) is not int or p[k]<(0 if k=='expected_edges' else 1):raise ValueError('hub positive integer policy required')
    if p['expected_centers']>64 or p['edge_chunk']>65536 or p['expected_nodes']>3037000499 or p['max_output_bytes']>1024**2 or p['max_buffer_bytes']>8*1024**2 or p['max_mapped_bytes']>1024**3:raise ValueError('hub finite envelope differs')
    cells=p['cell_ids']
    if not isinstance(cells,list) or len(cells)!=p['expected_centers'] or cells!=run.admission.experiment['cells'] or len(set(cells))!=len(cells):raise ValueError('hub cell denominator differs')
    if set(run.admission.experiment['outputs'])!={'cell-ledger.json','source-summary.json','artifact-index.json'}:raise ValueError('hub output denominator differs')
    numeric=max(p['expected_nodes']+32*min(p['edge_chunk'],p['expected_edges'])+16*p['expected_centers']+65536,
                32*min(p['edge_chunk'],p['expected_nodes'])+32*p['expected_centers']+65536)
    if numeric>p['max_buffer_bytes']:raise ValueError('hub numeric allowance exceeded before mapping')
    if p['census_experiment']!=run.admission.experiment['parent']:raise ValueError('census must be actual admitted parent')
    parent=run.admission.root/'research_runs'/p['census_experiment']
    for key,relative in (('prior_claim_input','claim.json'),('prior_terminal_input','complete.json'),('prior_result_input','outputs/source-summary.json')):
        value=run.admission.inputs[p[key]];path=run.admission.root/value['path']
        if path.resolve()!=(parent/relative).resolve() or file_hash(parent/relative)!=value['sha256']:
            raise ValueError('census input differs from original parent evidence')
    # Lifecycle already validates cell ID syntax. The finite physical envelope
    # includes bounded failure reasons in producer and duplicated lifecycle JSON.
    block=os.statvfs(run.admission.root).f_frsize
    reserved=(4*len(cells)+20)*block+(3*len(cells)+4)*2304
    if block<=0 or reserved>p['max_output_bytes']:raise ValueError('hub output physical allowance exceeded')
    m=_json_input(run,p['graph_input']);prior=_json_input(run,p['prior_result_input'])
    claim=_json_input(run,p['prior_claim_input']);terminal=_json_input(run,p['prior_terminal_input'])
    info=run.admission.inputs[p['graph_input']];identity=prior['identity']
    if (prior['status']!='complete' or terminal['status']!='complete' or terminal['unavailable_count']!=0
        or claim['experiment_id']!=p['census_experiment'] or terminal['experiment_id']!=p['census_experiment']
        or identity['claim_sha256']!=run.admission.inputs[p['prior_claim_input']]['sha256']
        or terminal['claim_sha256']!=identity['claim_sha256']
        or terminal['output_sha256']['source-summary.json']!=run.admission.inputs[p['prior_result_input']]['sha256']):raise ValueError('closed census identity differs')
    if prior['result']['identity']!=identity or identity['graph_manifest_sha256']!=info['sha256']:raise ValueError('census graph binding differs')
    for k in ('graph_hash','graph_config_hash','node_order_sha256'):
        if identity[k]!=p[k]:raise ValueError('census configuration identity differs')
    if m['graph_hash']!=p['graph_hash'] or m['metadata']['graph_config_hash']!=p['graph_config_hash'] or m['arrays']['node_ids']['sha256']!=p['node_order_sha256']:raise ValueError('hub graph identity differs')
    if (prior['result']['nodes'],prior['result']['directed_edges'])!=(p['expected_nodes'],p['expected_edges']):raise ValueError('hub source shape differs')
    meta=m['metadata']
    if not any(w['dataset']==info['dataset'] and utc(w['start'])<=utc(meta['start_utc'])<utc(meta['end_utc'])<=utc(w['end']) for w in run.admission.experiment['windows']):raise ValueError('hub graph outside registered window')
    ci=run.admission.inputs[p['cardinalities_input']];descriptor=prior['result']['files']['cardinalities.npy']
    if ci['sha256']!=descriptor['sha256'] or ci['dataset']!=info['dataset']:raise ValueError('census cardinalities binding differs')
    return p,info,ci,descriptor,identity,reserved


def _open_counts(root,info,descriptor,n):
    path=root/info['path']
    if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():raise ValueError('cardinalities path differs')
    if path.stat().st_size!=descriptor['bytes'] or path.stat().st_size>8*n+10000:raise ValueError('cardinalities file bound differs')
    if file_hash(path)!=info['sha256']:raise ValueError('cardinalities content differs')
    with path.open('rb') as stream:
        if np.lib.format.read_magic(stream)!=(1,0):raise ValueError('cardinalities NPY version differs')
        shape,fortran,dtype=np.lib.format.read_array_header_1_0(stream,max_header_size=10000)
        if shape!=(n,) or fortran or dtype!=np.dtype(np.int64) or stream.tell()+8*n!=path.stat().st_size:raise ValueError('cardinalities header/extent differs')
    return np.load(path,mmap_mode='r',allow_pickle=False,max_header_size=10000)


def produce_registered_hub_census(run,plan_input):
    if not isinstance(run,ResearchRun):raise ValueError('admitted hub census required')
    run._active();run._check_source();p,info,ci,descriptor,identity,reserved=_plan(run,plan_input)
    root=run.admission.root;directory=root/PREFIX/run.admission.experiment_id;ancestor=directory
    while not ancestor.exists():ancestor=ancestor.parent
    if not directory.resolve().is_relative_to(root) or ancestor.stat().st_dev!=root.stat().st_dev:raise ValueError('hub output must remain on guarded root filesystem')
    durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    _immutable(directory/'intent.json',{'plan_sha256':run.admission.inputs[plan_input]['sha256'],'prior_identity':identity,'cell_ids':p['cell_ids'],'reserved_output_bytes':reserved})
    start=time.monotonic();rows=[];counts=None;primary=None;propagating=False
    summary={'schema_version':1,'status':'running','financial_run_admitted':False,'prior_identity':identity,'graph_hash':p['graph_hash'],'qualification':'induced-edge sizing only; no capacity override, extraction/matching/fit feasibility or original pilot-cell completion'}
    try:
        counts=_open_counts(root,ci,descriptor,p['expected_nodes'])
        selected=[]
        for first in range(0,len(counts),p['edge_chunk']):
            part=counts[first:first+p['edge_chunk']]
            if part.min()<1 or part.max()>len(counts):raise ValueError('cardinalities range differs')
            indices=np.flatnonzero(part>p['threshold'])
            if len(selected)+len(indices)>p['expected_centers']:raise ValueError('selected center denominator differs')
            selected.extend((int(first+i),int(part[i])) for i in indices)
        if len(selected)!=p['expected_centers']:raise ValueError('selected center denominator differs')
        del part,indices
        with open_mapped_graph(root/info['path'],info['sha256'],max_mapped_bytes=p['max_mapped_bytes']) as graph:
            if (len(graph.node_ids),graph.edge_index.shape[1])!=(p['expected_nodes'],p['expected_edges']):raise ValueError('hub graph shape differs')
            def checkpoint(value):
                rank=len(rows)
                if rank>=len(selected) or (value['center'],value['nodes'])!=selected[rank]:raise ValueError('hub checkpoint selection differs')
                row={'id':p['cell_ids'][rank],'status':'complete',**value,'elapsed_seconds':time.monotonic()-start}
                _immutable(directory/(row['id']+'.json'),row);rows.append(row)
            measure(graph.edge_index,len(graph.node_ids),dict(selected),max_buffer_bytes=p['max_buffer_bytes'],edge_chunk=p['edge_chunk'],checkpoint=checkpoint)
        if len(rows)!=len(p['cell_ids']):raise ValueError('hub measurement denominator incomplete')
        summary['status']='complete'
    except BaseException as error:
        primary=error
        # Interruptions are left to the existing post-death observer; completed
        # cell files already provide a durable prefix and missing rows stay unknown.
        if not isinstance(error,Exception):
            propagating=True;raise
        message=str(error)
        # Printable ASCII and JSON escaping are bounded separately. The full
        # original message hash preserves identity when text is shortened/sanitized.
        raw_reason=type(error).__name__[:128]+': '+message[:2048]
        safe=''.join(c if 32<=ord(c)<=126 else '?' for c in raw_reason)
        while len(json.dumps(safe).encode('ascii'))>2048:safe=safe[:-1]
        summary.update(status='failed',reason=safe,reason_truncated=len(message)>2048 or safe!=raw_reason,
                       reason_sha256=hashlib.sha256(message.encode()).hexdigest())
        if len(rows)==len(p['cell_ids']):
            _immutable(directory/'infrastructure-failure.json',summary);propagating=True;raise
        while len(rows)<len(p['cell_ids']):
            row={'id':p['cell_ids'][len(rows)],'status':'failed' if not any(r['status']=='failed' for r in rows) else 'unavailable','reason':summary['reason']}
            _immutable(directory/(row['id']+'.json'),row);rows.append(row)
    finally:
        if counts is not None:
            try:counts._mmap.close()
            except BaseException as error:
                if propagating and primary is not None:primary.add_note('cardinality map cleanup failed: '+repr(error))
                else:raise RuntimeError('cardinality map close failure; no successful publication') from error
    summary.update(cells=rows,elapsed_seconds=time.monotonic()-start,prepublication_storage=_footprint(directory),prepublication_storage_scope='producer before result and three lifecycle outputs; final accounting in guard log')
    _immutable(directory/'result.json',summary)
    return rows,summary,directory
