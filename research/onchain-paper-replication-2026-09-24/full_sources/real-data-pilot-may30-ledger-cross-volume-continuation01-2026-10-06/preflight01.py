"""Read-only entry checks for the fixed fresh retained-ledger graph continuation."""
from pathlib import Path
from types import SimpleNamespace
import datetime
import json
import shutil
import subprocess

from tradingagents.research.onchain_replication.job import _admitted, PREFIX
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.resources import mem_available
from tradingagents.research.onchain_replication.workflow_storage import StorageWatch

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
NAME='eth-paper-real-pilot-may30-ledger-continuation-20261006-01'
GATE=str((HERE/'gate01.json').relative_to(ROOT))


from prepare01 import validate_binding,baseline


def check():
    binding=json.loads((HERE/'BINDINGS01.json').read_bytes())
    plan,policy,control=validate_binding(binding)
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    release_path=HERE/'RELEASE_REVIEW01.json'
    release=json.loads(release_path.read_bytes())
    if release.get('decision')!='accepted':raise ValueError('exact source/entry review missing')
    for relative,expected in release['evidence'].items():
        path=ROOT/relative
        if file_hash(path)!=expected:raise ValueError('reviewed entry changed: '+relative)
        committed=subprocess.check_output(['git','show',source+':'+relative],cwd=ROOT)
        if committed!=path.read_bytes():raise ValueError('reviewed entry not committed: '+relative)
    if subprocess.check_output(['git','show',source+':'+str(release_path.relative_to(ROOT))],cwd=ROOT)!=release_path.read_bytes():
        raise ValueError('source/entry review itself not committed')
    args=SimpleNamespace(root=ROOT,registration=GATE,experiment=NAME,source=source)
    admission,job=_admitted(args)
    if not admission.ready or admission.effective_attempt_budget!=72:raise ValueError('exact pilot admission/budget differs')
    expected_resources=baseline('execution-job01.json')['resources'];expected_resources['disk_paths']=[str(ROOT),str(control.DATA_ROOT)]
    if job['resources']!=expected_resources:raise ValueError('unchanged native/storage controls or exact two-volume floors differ')
    for relative,expected in admission.experiment['source_files'].items():
        if file_hash(ROOT/relative)!=expected:raise ValueError('source pin changed: '+relative)
    for info in admission.inputs.values():
        path=ROOT/info['path']
        if path.stat().st_size>4*1024**2 or file_hash(path)!=info['sha256']:
            raise ValueError('compact input pin changed: '+info['path'])
    if inventory(ROOT)!=json.loads((ROOT/admission.inputs['environment']['path']).read_bytes()):raise ValueError('installed runtime inventory differs')
    for path in (ROOT/'research_runs'/NAME,ROOT/PREFIX/'runs'/NAME,ROOT/PREFIX/'sources'/NAME,HERE/'launch-attempt01.json',HERE/'outer-exit01.json'):
        if path.exists() or path.is_symlink():raise ValueError('fixed namespace already reserved: '+str(path))
    units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True)
    if units.strip():raise ValueError('another native resource process is active')
    for claim_path in (ROOT/'research_runs').glob('*/claim.json'):
        claim=json.loads(claim_path.read_bytes())
        if claim.get('program_id')==admission.spec['program_id'] and not any((claim_path.parent/name).exists() for name in ('complete.json','failed.json')):
            raise ValueError('another program claim is active: '+str(claim_path.parent))
    if admission.experiment['cells']!=['graph-2022-05-30'] or job['kind']!='graphs' or job['payload']!={'plan_input':'continuation_plan'}:
        raise ValueError('fresh graph-only continuation differs')
    for role,key in [('continuation_plan','plan'),(plan['recovery_review_input'],'recovery'),('storage_policy','storage_policy'),(plan['relocation_receipt_input'],'relocation_receipt'),(plan['relocation_review_input'],'relocation_review')]:
        if any(admission.inputs[role][k]!=v for k,v in binding[key].items()):raise ValueError('registered continuation proof differs')
    if admission.inputs['continuation_entry_bindings']['sha256']!=file_hash(HERE/'BINDINGS01.json'):
        raise ValueError('registered exact entry binding differs')
    for candidate in policy['scratch_scope']['sqlite_temp_candidates']:
        path=Path(candidate)
        if path.exists() and path.stat().st_dev!=ROOT.stat().st_dev:raise ValueError('SQLite temp candidate outside guarded volume')
    storage=StorageWatch(**job['resources']['storage_budget']).check()
    growth=policy['growth_estimate_bytes'];limits=job['resources']['storage_budget']['limits']
    if storage['logical_file_bytes']+growth>limits['max_logical_bytes'] or storage['allocated_bytes']+growth>limits['max_allocated_bytes']:
        raise ValueError('current baseline plus declared continuation exceeds unchanged storage ceiling')
    data_storage=StorageWatch(**control.data_budget(plan)).check()
    data_free=shutil.disk_usage(control.DATA_ROOT).free
    if data_free<10*1024**3+control.DATA_RESERVE:raise ValueError('Data floor plus retained-store reserve unavailable')
    free=shutil.disk_usage(ROOT).free; available=mem_available()
    if free<policy['startup_free_requirement_bytes']:raise ValueError('full projected source/scratch plus disk floor unavailable')
    if available<job['resources']['start_reserve_bytes']:raise ValueError('frozen startup RAM reserve unavailable')
    return args,{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'experiment':NAME,
        'registration_sha256':file_hash(HERE/'gate01.json'),'release_sha256':file_hash(release_path),'effective_attempt_budget':72,
        'source_pins':len(admission.experiment['source_files']),'compact_input_pins':len(admission.inputs),
        'source_reingestion':False,'retained_ledger_bytes':plan['ledger']['bytes'],'host_mem_available_bytes':available,'free_disk_bytes':free,
        'startup_free_requirement_bytes':policy['startup_free_requirement_bytes'],'storage_observation':storage,
        'Data_storage_observation':data_storage,'Data_free_disk_bytes':data_free,'retained_ledger_path':str(control.EXTERNAL),
        'qualification':'Read-only continuation proof/source/namespace check; actual retained ledger hash and database consistency are checked only inside the genuine guarded worker. Growth is a reservation estimate, not certified graph extent or capacity. No payload was opened here.'}


if __name__=='__main__':print(json.dumps(check()[1],sort_keys=True))
