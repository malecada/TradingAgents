"""Preserve the entire closed failed adapter tree without following symbolic links."""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
IDENTITY = 'neural-streamed-production-adapter-20261002-02'
OWNED = HERE/'owned'/IDENTITY


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def publish(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    assert len(raw) < 1024**2
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def inventory():
    assert OWNED.resolve() == OWNED
    rows = []; signatures = {}; paths = [OWNED]
    while paths:
        path = paths.pop(); info = path.lstat()
        relative = str(path.relative_to(OWNED))
        assert len(Path(relative).parts) <= 32
        signatures[relative] = (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
                               info.st_size, info.st_blocks, info.st_mtime_ns, info.st_ctime_ns)
        row = {'role':'owned', 'path':relative, 'mode':stat.S_IMODE(info.st_mode),
               'allocated_bytes':info.st_blocks*512}
        if stat.S_ISDIR(info.st_mode):
            row['type'] = 'directory'; paths.extend(sorted(path.iterdir(), reverse=True))
        elif stat.S_ISLNK(info.st_mode):
            target = os.readlink(path); raw = os.fsencode(target)
            assert len(raw) <= 4096
            row.update(type='symlink', link_target=target, link_bytes=len(raw), link_sha256=digest(raw))
        else:
            assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 4*1024**2
            raw = path.read_bytes(); assert len(raw) == info.st_size
            row.update(type='file', bytes=len(raw), sha256=digest(raw))
        rows.append(row); assert len(rows)+len(paths) <= 12000
    rows.sort(key=lambda row:row['path'])
    assert sum(row['allocated_bytes'] for row in rows) <= 64*1024**2
    assert sum(row.get('bytes',0)+row.get('link_bytes',0) for row in rows) <= 64*1024**2
    return rows, signatures


def main():
    guard=json.loads((OWNED/'guard/final.json').read_bytes());ready=json.loads((OWNED/'guard/cpu_ready.json').read_bytes())
    child=json.loads((OWNED/'guard/child_exit.json').read_bytes());oracle=json.loads((OWNED/'oracle-report.json').read_bytes());terminal=json.loads((OWNED/'launcher-terminal.json').read_bytes())
    assert guard['phase']=='complete' and guard['cleanup_verified'] is True and guard['cleanup_stop_returncode'] in (0,5)
    assert child['exit_code']==0 and child['snapshot_error'] is None and child['reason']=='workload exited'
    assert terminal['status']=='passed' and terminal['error'] is None and terminal['retry'] is False
    assert oracle['status']=='passed' and oracle['error'] is None and oracle['pytest_exit_code']==0
    assert oracle['passed_checks']==['production_adapter_four_tests'] and len(oracle['collected'])==4
    expected=[{'nodeid':name,'when':phase,'outcome':'passed'} for name in oracle['collected'] for phase in ('setup','call','teardown')]
    assert oracle['outcomes']==expected
    progress=[json.loads(line) for line in (OWNED/'test-progress.jsonl').read_bytes().splitlines()]
    assert progress==[{'event':'collected','nodes':oracle['collected']},*expected]
    assert all(n==0 for n in guard['memory_events'].values())
    assert not Path(guard['cgroup']).exists()
    pids={guard['monitor_pid'],ready['pid'],child['workload_pid'],*(int(pid) for pid in guard['cpu_thread_readback'])}
    assert all(not Path('/proc',str(pid)).exists() for pid in pids)
    source=json.loads((OWNED/'reservation.json').read_bytes())['head'];release=json.loads((HERE/'adapter-release05.json').read_bytes())
    for path,expected_sha in release['source_files'].items():
        committed=subprocess.check_output(['git','show',source+':'+path],cwd=ROOT,timeout=10)
        assert digest(committed)==expected_sha==digest((ROOT/path).read_bytes())
    rows,before=inventory();assert all(row['type']!='symlink' for row in rows)
    manifest={'schema_version':1,'identity':IDENTITY,'members':rows,'files':sum(row['type']=='file' for row in rows),'directories_including_each_root':sum(row['type']=='directory' for row in rows),'symlinks':0,'entries_including_each_root':len(rows),'logical_bytes':sum(row.get('bytes',0) for row in rows),'allocated_bytes_including_directories':sum(row['allocated_bytes'] for row in rows)}
    with (HERE/'retained-tree02.tar.gz').open('xb') as output:
        with tarfile.open(fileobj=output,mode='w:gz') as archive:
            for row in rows:
                entry=tarfile.TarInfo('retained/owned'+('' if row['path']=='.' else '/'+row['path']));entry.mode=row['mode']
                if row['type']=='directory':entry.type=tarfile.DIRTYPE;archive.addfile(entry)
                else:
                    raw=(OWNED/row['path']).read_bytes();assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
                    entry.size=len(raw);archive.addfile(entry,io.BytesIO(raw))
        output.flush();os.fsync(output.fileno())
    after_rows,after=inventory();assert before==after and rows==after_rows
    publish(HERE/'retained-tree02.json',manifest)
    names=('launch-intent02.json','coordinator02.log','coordinator-result02.json','adapter-release05.json','REVIEW_ADAPTER_RELEASE05.md','adapter_tests04.py','adapter_launcher04.py','retained-tree02.json','retained-tree02.tar.gz')
    refs={name:{'path':str((HERE/name).relative_to(ROOT)),'bytes':(HERE/name).stat().st_size,'sha256':digest((HERE/name).read_bytes())} for name in names}
    publish(HERE/'execution-result02.json',{'schema_version':1,'identity':IDENTITY,'status':'closed_passed_adapter_retained_review_pending','source':source,'session':65517,'closed_at_utc':datetime.now(timezone.utc).isoformat(),'coordinator_exit_code':0,'child_exit_code':child['exit_code'],'guard_phase':guard['phase'],'cleanup_verified':True,'cleanup_stop_returncode':guard['cleanup_stop_returncode'],'cgroup_absent':True,'pids_absent':{str(pid):True for pid in sorted(pids)},'passed_checks':oracle['passed_checks'],'collected_tests':oracle['collected'],'passed_test_phase_count':len(expected),'progress_record_count':len(progress),'memory_events':guard['memory_events'],'peak_sampled_memory_bytes':guard['peak_sampled_memory_current_bytes'],'source_pins_verified':len(release['source_files']),'complete_retained_tree':{k:v for k,v in manifest.items() if k!='members'},'refs':refs,'budget':{'spent_empirical':35,'highest_adopted_ceiling':63,'new_empirical_claims':0,'new_financial_fits':0},'qualification':'Actual complete four new production-adapter tests/12PASSphases/13appendprogress records, real default-selectedconstructorRNG/state equality and actualtiny selected update/checkpoint/reload/identity refusal. Qualified synthetic admission mocks source/guard and does not prove genuine empirical admission or full-sizecapacity. Parent/guard/childPASS and actualnative1GiBhigh=max/zeroSwap/120s/twoCPU/4MiBfile/events0/completeownedregular-only storage/cleanup verified with naturalstop5; precise stop5reason unknown. All originalPIDs/cgroup absent; complete final tree/file bodies/dirmodes preserved with no links. Historicaladapter01FAILED remainsclosed; no financial fit/empiricalclaim/refund. Sourcefreeze ended after verifiedclosure. First fullgraph pending3.75GiB resource question remains separatelygated.'})
    print(json.dumps({k:v for k,v in manifest.items() if k!='members'}))

if __name__=='__main__':main()
