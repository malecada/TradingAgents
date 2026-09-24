"""Post-death observer only. No raw transform, fit, retry or terminal overwrite."""
from pathlib import Path
from types import SimpleNamespace
import json
import subprocess
import time
from tradingagents.research import ResearchRun
from tradingagents.research.lifecycle import _immutable,_encode
from tradingagents.research.onchain_replication.provenance import file_hash,durable_mkdir
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXPERIMENT='paper-full-source-metadata-20260924'


def publish_once(path,value):
    if path.exists():
        if path.read_bytes()!=_encode(value):raise ValueError('existing observer bytes differ; preserve and review')
    else:_immutable(path,value)


def reconcile(receipt,artifacts,source,owner_identity):
    receipt=Path(receipt);artifacts=Path(artifacts)
    live_path=receipt/'live.json'
    if not live_path.exists():return {'status':'no_guard_receipt_no_release'}
    live=json.loads(live_path.read_bytes());cgroup=Path(live['cgroup']) if live.get('cgroup') else None
    if live.get('owner_identity')!=owner_identity or live.get('monitor_pid')!=owner_identity.get('monitor_pid'):raise ValueError('observer ownership differs; no process action authorized')
    if (receipt/'observer.json').exists():return json.loads((receipt/'observer.json').read_bytes())
    # Wait for lease-loss self-termination, then stop exactly the recorded local unit.
    if cgroup is not None:
        deadline=time.monotonic()+20
        while cgroup.exists() and 'populated 1' in (cgroup/'cgroup.events').read_text() and time.monotonic()<deadline:time.sleep(.25)
        if cgroup.exists() and 'populated 1' in (cgroup/'cgroup.events').read_text():
            subprocess.run(['systemctl','--user','stop',live['unit']],check=True,timeout=10,capture_output=True)
        if cgroup.exists() and 'populated 1' in (cgroup/'cgroup.events').read_text():raise RuntimeError('observer cannot prove cgroup death; do not release or reuse claim')
    guard_hashes={str(p):file_hash(p) for p in receipt.iterdir() if p.is_file() and p.name!='observer.json'}
    directory=ROOT/'research_runs'/EXPERIMENT
    if not (directory/'claim.json').exists():
        record={'status':'not_admitted','cgroup_empty':True,'source':source,'guard_receipt_hashes':guard_hashes}
        _immutable(receipt/'observer.json',record);return record
    if cgroup is None:raise RuntimeError('admitted claim has no cgroup-death proof; observer closure refused')
    claim=json.loads((directory/'claim.json').read_bytes())
    if claim['source']!=source or claim['registration_sha256']!=file_hash(HERE/'gate-v2.json'):raise ValueError('observer claim source/registration differs')
    if (directory/'complete.json').exists():
        guard=json.loads((receipt/'final.json').read_bytes()) if (receipt/'final.json').exists() else {}
        verified=guard.get('phase')=='complete' and guard.get('cleanup_verified') is True and guard.get('child_exit_code')==0 and guard.get('limit_reason') is None and all(guard.get('memory_events',{}).get(k)==0 for k in ('oom','oom_kill'))
        record={'status':'complete' if verified else 'resource_verification_failed','lifecycle_status':'complete','guard_status':guard.get('phase','unavailable'),'cgroup_empty':True,'source':source,'guard_receipt_hashes':guard_hashes,'terminal_sha256':file_hash(directory/'complete.json')}
        _immutable(receipt/'observer.json',record);return record
    observer=artifacts/'postmortem';durable_mkdir(observer)
    cells=[]
    for name in claim['experiment']['cells']:
        path=artifacts/(name+'.json')
        cells.append(json.loads(path.read_bytes()) if path.exists() else {'id':name,'status':'unavailable','reason':'workload terminated before durable disposition; no retry'})
    publish_once(observer/'cell-ledger.json',cells)
    index={str(p):{'sha256':file_hash(p),'bytes':p.stat().st_size} for p in artifacts.rglob('*') if p.is_file() and observer not in p.parents}
    publish_once(observer/'artifact-index.json',index)
    run=ResearchRun(SimpleNamespace(root=ROOT,experiment_id=EXPERIMENT));run._claim_sha256=file_hash(directory/'claim.json')
    if not (directory/'failed.json').exists():run.fail('outer observer verified cgroup death; resource attempt interrupted; complete denominator retained at '+str(observer))
    record={'status':'failed','cgroup_empty':True,'source':source,'guard_receipt_hashes':guard_hashes,'terminal_sha256':file_hash(directory/'failed.json'),'observer_ledger':str(observer/'cell-ledger.json'),'observer_ledger_sha256':file_hash(observer/'cell-ledger.json'),'artifact_index_sha256':file_hash(observer/'artifact-index.json')}
    _immutable(receipt/'observer.json',record);return record
