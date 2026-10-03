"""Root one-use invocation wrapper; actual controller retains all native evidence."""
import hashlib,json,os,resource,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
IDENTITY='original-import-native-success-20261003-04'
def pin(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode();assert len(raw)<=65536
    with (HERE/name).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
def main():
    release=json.loads((HERE/'release01.json').read_bytes());CAP=Path(release['capsule_root']);entry=release['cases']['success']
    assert entry['identity']==IDENTITY and release['status']=='released-native-engineering' and release['remaining']==[]
    assert not (HERE/'LAUNCH_INTENT_PRIMARY01.json').exists() and not (CAP/'fixture_outer'/IDENTITY).exists() and not (CAP/'research_runs'/IDENTITY).exists()
    assert pin(HERE/'REVIEW_PRIMARY_RELEASE04.md')==release['release_review_sha256']
    assert pin(HERE/'REVIEW_REMOTE_PREPARATION_RECOVERY04.md')==release['external_recovery_review_sha256']
    assert pin(HERE/'REMOTE_PREPARATION_RECOVERY01.json')==release['external_capsule_recovery_sha256']
    command=[sys.executable,'-B','fixture_tools/outer_controller01.py','--release',str(HERE/'release01.json'),'--case','success']
    assert pin(CAP/'fixture_tools/outer_controller01.py')==release['source_files']['fixture_tools/outer_controller01.py']
    assert shutil.disk_usage(CAP).free>=10*1024**3
    available=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
    assert available>=6*1024**3
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CAP,text=True,timeout=10).strip()==release['capsule_commit']
    resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304))
    started=time.monotonic();pid=os.getpid();ticks=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
    save('LAUNCH_INTENT_PRIMARY01.json',{'identity':IDENTITY,'source_commit':release['capsule_commit'],'registration_sha256':release['registration_sha256'],'release_sha256':pin(HERE/'release01.json'),'launcher_pid':pid,'launcher_start_ticks':ticks,'actual_controller_command':command,'cwd':str(CAP),'available_before_bytes':available,'disk_free_before_bytes':shutil.disk_usage(CAP).free,'started_utc':datetime.now(timezone.utc).isoformat(),'identity_reuse_forbidden_after_intent':True})
    result=subprocess.run(command,cwd=CAP,env=os.environ.copy())
    save('OUTER_EXIT_PRIMARY01.json',{'identity':IDENTITY,'source_commit':release['capsule_commit'],'caller_exit_code':result.returncode,'elapsed_seconds':time.monotonic()-started,'launcher_pid':pid,'launcher_start_ticks':ticks,'finished_utc':datetime.now(timezone.utc).isoformat(),'qualification':'Actual subprocess controller return; root wrapper does not infer native/MCM completion or external recovery. Intent identity is permanently reserved even on preclaim failure.'})
    raise SystemExit(result.returncode)
if __name__=='__main__':main()
