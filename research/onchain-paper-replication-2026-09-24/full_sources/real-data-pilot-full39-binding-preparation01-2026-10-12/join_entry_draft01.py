"""Root-only finite39 draft joins; no Gate write, admission, claim or release.

Call after real public construction and binding, supplying the actual73 role refs
and inherited core dictionary. Returned fragments belong to a draft only.
"""
import copy
import hashlib
import json
from pathlib import Path

NAME='eth-paper-real-data-end-to-end-resource-20261012-39'
CELL='real-eth-whole-seven-graph-joint-pilot-resource39'

def joined_draft(root, inputs, inherited_core, builder_path):
    root=Path(root).resolve()
    assert len(inputs)==73
    def body(role):
        pin=inputs[role];path=root/pin['path']
        assert path.resolve(strict=True)==path and path.is_relative_to(root) and path.is_file() and not path.is_symlink()
        before=path.stat();assert before.st_size<=4*1024**2 and before.st_nlink==1
        raw=path.read_bytes();after=path.stat()
        assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns'))
        assert hashlib.sha256(raw).hexdigest()==pin['sha256']
        if 'bytes' in pin:assert len(raw)==pin['bytes']
        return json.loads(raw),{'path':str(path.relative_to(root)),'sha256':pin['sha256'],'bytes':len(raw)}
    job,_=body('execution_job')
    assert len(job['payload']['representation_jobs'])==1
    selected=next(iter(job['payload']['representation_jobs'].values()))
    pilot,_=body(selected['real_pilot_input'])
    assert pilot['cell_id']==CELL and len(pilot['graph_inputs'])==7
    assert job['resources']['storage_budget']['experiment']==NAME
    mcm,_=body('mcm_policy');assert 'entry_qualification' not in mcm
    assert mcm['batched']['continuation']['manifest_input'] is None
    assert mcm['batched']['continuation']['graph_manifest_inputs']=={}
    typed,_=body('typed_payload');assert len(typed['graphs'])==7
    assert sum(v['rows']*32 for v in typed['graphs'].values())==415968128
    core=copy.deepcopy(inherited_core)
    assert 'mcm_policy' in core['inputs']
    # Rebuild every original core role from actual39 bodies, including MCM.
    core['inputs']={role:body(role)[1] for role in core['inputs']}
    path=Path(builder_path);assert path.resolve(strict=True)==path and path.is_relative_to(root) and not path.is_symlink()
    core['builder_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    core['scope']='Fixed39 whole-pilot draft; actual bound core roles including full-route MCM.'
    return {'status':'DRAFT_NOT_RELEASED','identity':NAME,'core_manifest':core,
            'experiment_cells':[pilot['cell_id']],
            'prior38_outcome':None,'prior38_recovery':None,
            'prior38_component_qualification':None,'current_whole39_capacity':None,
            'final_release':None,'claim':False,'execution':False}
