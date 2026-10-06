"""Prepare one fixed May30 registration; no admission, claim or numerical work."""
from pathlib import Path
import copy,datetime,hashlib,json,shutil
from tradingagents.research.onchain_replication.workflow_storage import StorageWatch
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
STUDY=ROOT/'research/onchain-paper-replication-2026-09-24'
F=STUDY/'full_sources'
NAME='eth-paper-real-pilot-graph-20220530-20261005-01'
OLD=F/'real-data-pilot-fourth-graph01-2026-10-06'
DRAFT=F/'real-data-pilot-fifth-graph-input-preparation01-2026-10-06/draft01'
BACKUP=STUDY/'storage/real-pilot-fourth-graph-preservation-20261006-01'
LEDGER=F/'real-data-pilot-fourth-graph-post-recovery-retirement01-2026-10-06'
GETS=F/'real-data-pilot-fourth-graph-get-duplicates-retirement01-2026-10-06'
OUTCOME=F/'real-data-pilot-fourth-graph-preservation-outcome-review01-2026-10-06/REVIEW01.json'
def load(p):return json.loads(p.read_bytes())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'dataset':'eth','path':str(p.relative_to(ROOT)),'sha256':digest(p)}
def write(p,v):
    with p.open('x') as stream:json.dump(v,stream,sort_keys=True,indent=2);stream.write('\n')
def main():
    assert digest(OUTCOME)=='4b5d5e4efa6b4f920e94f64b06530fb6ca2da569ed21e2a1c0f9b4a7a9e142fc'
    assert load(OUTCOME)['full_scope_byte_recovery'] is True
    for directory,total in ((LEDGER,6437658624),(GETS,501845112)):
        completed=load(directory/'complete01.json');terminal=load(directory/'ROOT_TERMINAL01.json')
        assert completed['payload_bytes_retired']==total and terminal['actual_root_exit_code']==0
        assert terminal['complete_sha256']==digest(directory/'complete01.json')
        assert all(not (ROOT/relative).exists() and not (ROOT/relative).is_symlink() for relative in completed['removed'])
    draft=load(DRAFT/'MAY30_DRAFT01.json');projection=load(HERE/'STORAGE_PROJECTION01.json')
    old_job=load(OLD/'execution-job01.json');baseline=StorageWatch(**old_job['resources']['storage_budget']).check()
    growth=projection['prospective_growth_estimate_bytes'];startup=projection['prospective_startup_free_bytes']
    policy=load(OLD/'STORAGE_POLICY01.json');policy.update(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline=baseline,free_disk_observed_bytes=shutil.disk_usage(ROOT).free,growth_estimate_bytes=growth,startup_free_requirement_bytes=startup)
    policy['storage_budget']=copy.deepcopy(old_job['resources']['storage_budget'])
    policy['storage_budget']['limits'].update(max_logical_bytes=baseline['logical_file_bytes']+growth,max_allocated_bytes=baseline['allocated_bytes']+growth)
    write(HERE/'STORAGE_POLICY01.json',policy)
    job=copy.deepcopy(old_job);job['resources']['storage_budget']=policy['storage_budget'];write(HERE/'execution-job01.json',job)
    gate=load(OLD/'gate01.json');old=next(iter(gate['experiments'].values()));e=copy.deepcopy(old)
    e.update(cells=draft['cells'],outputs=draft['outputs'],windows=draft['windows'],parent=None,question='Build the complete preserved ETH May30–June6,2022 graph for the representative real-data pilot; measure graph throughput, peak charged memory and storage.',charter={k:v for k,v in ref(HERE/'CHARTER01.md').items() if k!='dataset'})
    keep={k:v for k,v in old['inputs'].items() if not k.startswith('storage_') and k not in ('raw_extent','execution_job') and k not in draft['raw_input_refs']}
    e['inputs']={**keep,**draft['raw_input_refs'],'raw_extent':ref(HERE/'RAW_EXTENT01.json'),'execution_job':ref(HERE/'execution-job01.json'),'storage_policy':ref(HERE/'STORAGE_POLICY01.json'),'storage_projection':ref(HERE/'STORAGE_PROJECTION01.json'),'storage_closure_review':ref(OUTCOME),'storage_retirement_complete':ref(LEDGER/'complete01.json'),'storage_retirement_root_exit':ref(LEDGER/'ROOT_TERMINAL01.json')}
    roles={'storage_complete':'complete.json','storage_recovered_complete':'recovered-complete.json','storage_selection':'selection01.json','storage_native_final':'guard01/final.json','storage_outer_exit':'outer-exit01.json','storage_root_terminal':'ROOT_TERMINAL01.json','storage_restore':'11-restore.json','storage_recovered_restore':'11-recovered-restore.json','storage_kept':'11-kept.json','storage_body_get_receipt':'11-recovered.bin.transport.json'}
    e['inputs'].update({role:ref(BACKUP/name) for role,name in roles.items()})
    e['source_files']={p:h for p,h in old['source_files'].items() if not p.startswith(str(OLD.relative_to(ROOT))+'/')}
    for p in (HERE/'CHARTER01.md',HERE/'launch01.py',HERE/'preflight01.py',Path(__file__)):
        e['source_files'][str(p.relative_to(ROOT))]=digest(p)
    assert len(e['source_files'])==178
    assert e['cumulative_budget_extension']==old['cumulative_budget_extension'] and gate['families']==load(OLD/'gate01.json')['families']
    gate['experiments']={NAME:e};write(HERE/'gate01.json',gate)
    write(HERE/'ROOT_PREPARATION01.json',{'status':'FROZEN_REQUIRES_INDEPENDENT_ENTRY_REVIEW_COMMIT_AND_FRESH_ADMISSION','identity':NAME,'source_pins':len(e['source_files']),'compact_inputs':len(e['inputs']),'raw_stat_extents':sum(len(v['segments']) for v in load(HERE/'RAW_EXTENT01.json')['daily_members']),'effective_budget_unchanged':71,'scientific_source_unchanged':True,'growth_estimate_bytes':growth,'startup_free_requirement_bytes':startup,'free_disk_observed_bytes':policy['free_disk_observed_bytes'],'preparation_source_sha256':digest(Path(__file__)),'qualification':'Exact fixed input/gate preparation only; no claim/Owner/Binding/admission/capacity. Same native caps and original density formula; shared-tree baseline measured anew.'})
    print(json.dumps({'gate_sha256':digest(HERE/'gate01.json'),'inputs':len(e['inputs']),'source_pins':len(e['source_files']),'free_disk_bytes':policy['free_disk_observed_bytes'],'startup_requirement':startup},sort_keys=True))
if __name__=='__main__':main()
