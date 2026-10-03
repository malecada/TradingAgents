"""Preserve a claimed terminal native successor; partial closure needs a separate record."""
import hashlib,importlib.util,json,os,shutil,stat,subprocess,tarfile,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;CAP=HERE/'capsule02';IDENTITY='original-import-native-success-20261003-02'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())
def save(name,value):
    with (HERE/name).open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
def main():
    started=time.monotonic();assert shutil.disk_usage(HERE).free>=10*1024**3
    release=read(HERE/'release01.json');base=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/IDENTITY
    run=CAP/'research_runs'/IDENTITY;outer=CAP/'fixture_outer'/IDENTITY
    exit_record=read(HERE/'OUTER_EXIT_PRIMARY01.json');assert exit_record['identity']==IDENTITY
    launch=read(base/'launch.json');owner=read(base/'owner.json');ready=read(base/'guard/cpu_ready.json');child=read(base/'guard/child_exit.json');guard=read(base/'guard/final.json')
    claim=read(run/'claim.json');terminals=[name for name in ['complete','failed'] if (run/(name+'.json')).exists()];assert len(terminals)==1
    status=terminals[0];terminal=read(run/(status+'.json'));assert terminal['status']==status and terminal['claim_sha256']==sha((run/'claim.json').read_bytes())
    assert claim['source']==release['capsule_commit'] and claim['registration_sha256']==release['registration_sha256']
    outputs={p.name:sha(p.read_bytes()) for p in (run/'outputs').iterdir()};assert outputs==terminal['output_sha256']
    spec=importlib.util.spec_from_file_location('actual_retained_verify',CAP/'tradingagents/research/verify.py');verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
    verified=verify.verify_claim(run);assert verified==claim
    pids=sorted({launch['supervisor_pid'],owner['monitor_pid'],ready['pid'],child['workload_pid'],read(outer/'intent.json')['caller_pid'],exit_record['launcher_pid']})
    assert all(type(pid) is int and pid>1 and not Path('/proc',str(pid)).exists() for pid in pids)
    cg=Path(guard['cgroup']);assert cg.is_relative_to('/sys/fs/cgroup') and cg.name==guard['unit'] and not cg.exists()
    result=subprocess.run(['systemctl','--user','show',guard['unit'],'--property=ActiveState,SubState,Result,ExecMainStatus,ControlGroup'],capture_output=True,text=True,timeout=10)
    assert result.returncode==0 and len(result.stdout)<16384
    properties=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line);assert properties['ActiveState'] in ('failed','inactive') and properties['SubState'] in ('failed','dead') and properties['ControlGroup']==''
    for name,pin in release['source_files'].items():assert sha((CAP/name).read_bytes())==pin
    assert sha((CAP/release['registration']).read_bytes())==release['registration_sha256']
    spec=importlib.util.spec_from_file_location('actual_selected_raw',CAP/'fixture_tools/raw_receipts01.py');raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
    authentication=None;authentication_error=None;post_tail=None;post_tail_error=None
    try:authentication=raw.authenticate(CAP,'success',release)
    except Exception as error:authentication_error={'type':type(error).__name__,'message':str(error)[:2048]}
    try:post_tail=raw.authenticate_post_tail(CAP,IDENTITY,release['cases']['success']['job_resources'])
    except Exception as error:post_tail_error={'type':type(error).__name__,'message':str(error)[:2048]}
    outer_terminal=read(outer/'terminal.json');cells=read(run/'outputs/cell-ledger.json')
    stages=[p for p in (CAP/'research_artifacts/onchain_representations').glob('*/'+IDENTITY+'/compact/mcm-*')]
    completed_stages=[p for p in stages if (p/'stage-complete.json').exists()]
    roots=list((CAP/'research_artifacts/onchain_representations').glob('*/'+IDENTITY));assert len(roots)==1
    imported=roots[0]/'compact/dictionary-import/import-complete.json'
    members=[]
    for path in [CAP,*sorted(CAP.rglob('*'))]:
        assert time.monotonic()-started<60;info=path.lstat();assert path.resolve()==path and info.st_dev==CAP.stat().st_dev
        row={'path':str(path.relative_to(CAP)),'mode':stat.S_IMODE(info.st_mode),'allocated_bytes':info.st_blocks*512}
        if stat.S_ISREG(info.st_mode):assert info.st_nlink==1 and info.st_size<=4*1024**2;body=path.read_bytes();row.update(kind='file',bytes=len(body),sha256=sha(body))
        else:assert stat.S_ISDIR(info.st_mode);row.update(kind='directory',bytes=0)
        members.append(row)
    archive=HERE/'retained-primary01.tar.gz'
    with tarfile.open(archive,'x:gz') as stream:
        for row in members:stream.add(CAP/row['path'],arcname='capsule02'+('' if row['path']=='.' else '/'+row['path']),recursive=False)
    assert archive.stat().st_size<=4*1024**2
    for row in members:
        if row['kind']=='file':assert sha((CAP/row['path']).read_bytes())==row['sha256']
    retention={'schema_version':1,'identity':IDENTITY,'members':members,'files':sum(x['kind']=='file' for x in members),'directories':sum(x['kind']=='directory' for x in members),'logical_bytes':sum(x['bytes'] for x in members),'allocated_bytes':sum(x['allocated_bytes'] for x in members),'archive_sha256':sha(archive.read_bytes()),'archive_bytes':archive.stat().st_size}
    save('RETAINED_PRIMARY01.json',retention)
    observed={'schema_version':1,'identity':IDENTITY,'lifecycle_status':status,'repeat_allowed':False,'source_commit':release['capsule_commit'],'release_sha256':sha((HERE/'release01.json').read_bytes()),'claim_sha256':sha((run/'claim.json').read_bytes()),'terminal_sha256':sha((run/(status+'.json')).read_bytes()),'parent_failure_reason':terminal.get('reason'),'outer_exit_code':exit_record['caller_exit_code'],'outer_terminal_status':outer_terminal['status'],'native_child_exit_code':child['exit_code'],'native_elapsed_seconds':guard['elapsed_seconds'],'native_sampled_peak_bytes':guard['peak_sampled_memory_current_bytes'],'memory_events':guard['memory_events'],'kernel_controls':guard['kernel_controls'],'recorded_pids_absent':pids,'original_cgroup_absent':str(cg),'unit_properties':properties,'original_outer_cleanup':read(outer/'cleanup.json'),'original_dictionary_import_complete_sha256':sha(imported.read_bytes()) if imported.exists() else None,'retained_mcm_stage_directories':len(stages),'complete_mcm_stage_markers':len(completed_stages),'cells':cells,'actual_selected_raw_authentication':authentication,'actual_selected_raw_authentication_error':authentication_error,'actual_selected_post_tail_authentication_error':post_tail_error,'retention_sha256':sha((HERE/'RETAINED_PRIMARY01.json').read_bytes()),'source_freeze_ended':True,'paper_closed_attempts':36,'paper_highest_adopted_budget':64,'verified_utc':datetime.now(timezone.utc).isoformat(),'qualification':'Actual registered synthetic imported dictionary/MCM resource outcome only. All actual dispositions retained; authentication refusal is reported and never relabeled success. Source freeze ended only after recorded original PIDs/cgroup absent and source/input pins unchanged. Full owned raw has not yet been independently reviewed or externally recovered. No scientific representation completion/full-sized capacity/financial fit or paper agreement inferred.'}
    if post_tail is not None:observed['actual_selected_post_tail']=post_tail
    save('EXECUTION_PRIMARY01.json',observed);print(json.dumps({k:observed[k] for k in ['identity','lifecycle_status','outer_exit_code','native_child_exit_code','native_elapsed_seconds','native_sampled_peak_bytes','complete_mcm_stage_markers','actual_selected_raw_authentication_error']}))
if __name__=='__main__':main()
