"""Retain actual failed first invocation without replay or receipt alteration."""
import hashlib,importlib.util,json,shutil,stat,subprocess,tarfile,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;CAP=HERE/'capsule01'
IDENTITY='original-import-native-success-20261003-01'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())

def main():
    started=time.monotonic();assert shutil.disk_usage(HERE).free>=10*1024**3
    release=read(HERE/'release01.json');base=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/IDENTITY
    run=CAP/'research_runs'/IDENTITY;outer=CAP/'fixture_outer'/IDENTITY
    launch=read(base/'launch.json');owner=read(base/'owner.json');ready=read(base/'guard/cpu_ready.json');child=read(base/'guard/child_exit.json');guard=read(base/'guard/final.json')
    claim=read(run/'claim.json');terminal=read(run/'failed.json');exit_record=read(HERE/'OUTER_EXIT_PRIMARY01.json')
    assert exit_record['caller_exit_code']==1 and guard['phase']=='failed' and child['exit_code']==guard['child_exit_code']==1
    assert claim['source']==release['capsule_commit'] and claim['registration_sha256']==release['registration_sha256']
    assert terminal['claim_sha256']==sha((run/'claim.json').read_bytes()) and terminal['reason']=='ValueError: compact metadata bound'
    assert not (run/'complete.json').exists()
    outputs={p.name:sha(p.read_bytes()) for p in (run/'outputs').iterdir()};assert outputs==terminal['output_sha256']
    cells=read(run/'outputs/cell-ledger.json');assert [r['status'] for r in cells]==['failed','unavailable']
    pids=sorted({launch['supervisor_pid'],owner['monitor_pid'],ready['pid'],child['workload_pid'],read(outer/'intent.json')['caller_pid'],read(HERE/'LAUNCH_INTENT_PRIMARY01.json')['launcher_shell_pid']})
    assert all(type(pid) is int and pid>1 and not Path('/proc',str(pid)).exists() for pid in pids)
    cg=Path(guard['cgroup']);assert cg.is_relative_to('/sys/fs/cgroup') and cg.name==guard['unit'] and not cg.exists()
    result=subprocess.run(['systemctl','--user','show',guard['unit'],'--property=ActiveState,SubState,Result,ExecMainStatus,ControlGroup'],capture_output=True,text=True,timeout=10)
    assert result.returncode==0 and len(result.stdout)<16384
    properties=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    assert properties['ActiveState']=='failed' and properties['SubState']=='failed' and properties['ControlGroup']==''
    spec=importlib.util.spec_from_file_location('retained_raw_observations',CAP/'fixture_tools/raw_receipts01.py');raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
    observations=raw.positive_native_observations(CAP,guard,child,release['cases']['success']['job_resources'])
    for name,pin in release['source_files'].items():assert sha((CAP/name).read_bytes())==pin
    assert sha((CAP/release['registration']).read_bytes())==release['registration_sha256']
    journal_roots=list((CAP/'research_artifacts/onchain_representations').glob('*/'+IDENTITY));assert len(journal_roots)==1
    journal=journal_roots[0];assert (journal/'failed.json').exists() and not (journal/'complete.json').exists()
    imported=journal/'compact/dictionary-import/import-complete.json';assert imported.exists()
    assert not list(journal.glob('compact/mcm-*')) and not (CAP/'research_artifacts/onchain_compact_outputs').exists()
    members=[]
    for path in [CAP,*sorted(CAP.rglob('*'))]:
        assert time.monotonic()-started<60
        info=path.lstat();assert path.resolve()==path and info.st_dev==CAP.stat().st_dev
        row={'path':str(path.relative_to(CAP)),'mode':stat.S_IMODE(info.st_mode),'allocated_bytes':info.st_blocks*512}
        if stat.S_ISREG(info.st_mode):
            assert info.st_nlink==1 and info.st_size<=4*1024**2
            body=path.read_bytes();row.update(kind='file',bytes=len(body),sha256=sha(body))
        else:assert stat.S_ISDIR(info.st_mode);row.update(kind='directory',bytes=0)
        members.append(row)
    archive=HERE/'retained-primary01.tar.gz'
    with tarfile.open(archive,'x:gz') as stream:
        for row in members:stream.add(CAP/row['path'],arcname='capsule01'+('' if row['path']=='.' else '/'+row['path']),recursive=False)
    for row in members:
        if row['kind']=='file':assert sha((CAP/row['path']).read_bytes())==row['sha256']
    inventory={'schema_version':1,'identity':IDENTITY,'members':members,'files':sum(x['kind']=='file' for x in members),'directories':sum(x['kind']=='directory' for x in members),'logical_bytes':sum(x['bytes'] for x in members),'allocated_bytes':sum(x['allocated_bytes'] for x in members),'archive_sha256':sha(archive.read_bytes()),'archive_bytes':archive.stat().st_size}
    with (HERE/'RETAINED_PRIMARY01.json').open('x') as stream:json.dump(inventory,stream,indent=2,sort_keys=True);stream.write('\n')
    report={'schema_version':1,'identity':IDENTITY,'status':'failed','repeat_allowed':False,'source_commit':release['capsule_commit'],'release_sha256':sha((HERE/'release01.json').read_bytes()),'claim_sha256':terminal['claim_sha256'],'parent_failure_reason':terminal['reason'],'outer_exit_code':1,'native_child_exit_code':1,'native_elapsed_seconds':guard['elapsed_seconds'],'native_sampled_peak_bytes':guard['peak_sampled_memory_current_bytes'],'native_observations':observations,'kernel_controls':guard['kernel_controls'],'recorded_pids_absent':pids,'original_cgroup_absent':str(cg),'unit_properties':properties,'original_outer_unresolved_pid_absence_preserved':True,'original_dictionary_import_complete_sha256':sha(imported.read_bytes()),'completed_mcm_targets':0,'scalar_reference_comparisons':0,'cells':cells,'retention_sha256':sha((HERE/'RETAINED_PRIMARY01.json').read_bytes()),'source_freeze_ended':True,'closed_engineering_attempts':1,'engineering_attempt_budget':2,'paper_closed_attempts':36,'paper_highest_adopted_budget':64,'verified_utc':datetime.now(timezone.utc).isoformat(),'qualification':'Actual genuine imported dictionary stage completed but metadata preflight failed before any MCM stage. Both resource cells retained failed/unavailable. Native control/cleanup readback is separate root metadata evidence; original outer cleanup.json unresolved flag is unchanged. No full-sized capacity, MCM correctness, financial fit or paper agreement inferred. Full raw archive not yet externally recovered.'}
    with (HERE/'EXECUTION_PRIMARY01.json').open('x') as stream:json.dump(report,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:report[k] for k in ['status','identity','parent_failure_reason','native_elapsed_seconds','native_sampled_peak_bytes','recorded_pids_absent','completed_mcm_targets','scalar_reference_comparisons']}))

if __name__=='__main__':main()
