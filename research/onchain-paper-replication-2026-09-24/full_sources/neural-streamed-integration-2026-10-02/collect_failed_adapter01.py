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
IDENTITY = 'neural-streamed-production-adapter-20261002-01'
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
    guard = json.loads((OWNED/'guard/final.json').read_bytes())
    ready = json.loads((OWNED/'guard/cpu_ready.json').read_bytes())
    terminal = json.loads((OWNED/'launcher-terminal.json').read_bytes())
    assert guard['phase']=='failed' and guard['cleanup_verified'] is True
    assert guard['cleanup_stop_returncode']==0
    assert guard['limit_reason']=='ValueError: storage special file or symbolic link refused'
    assert terminal['status']=='failed' and terminal['retry'] is False
    assert not (OWNED/'oracle-report.json').exists()
    assert not Path(guard['cgroup']).exists()
    pids = {guard['monitor_pid'], ready['pid'], *(int(pid) for pid in guard['cpu_thread_readback'])}
    assert all(not Path('/proc',str(pid)).exists() for pid in pids)
    source = json.loads((OWNED/'reservation.json').read_bytes())['head']
    release = json.loads((HERE/'adapter-release03.json').read_bytes())
    for path, expected in release['source_files'].items():
        committed = subprocess.check_output(['git','show',source+':'+path], cwd=ROOT, timeout=10)
        assert digest(committed)==expected==digest((ROOT/path).read_bytes())
    rows, before = inventory()
    manifest = {'schema_version':1, 'identity':IDENTITY, 'members':rows,
        'files':sum(row['type']=='file' for row in rows),
        'directories_including_each_root':sum(row['type']=='directory' for row in rows),
        'symlinks':sum(row['type']=='symlink' for row in rows),
        'entries_including_each_root':len(rows),
        'logical_bytes':sum(row.get('bytes',0) for row in rows),
        'logical_link_target_bytes':sum(row.get('link_bytes',0) for row in rows),
        'allocated_bytes_including_directories':sum(row['allocated_bytes'] for row in rows)}
    with (HERE/'retained-tree01.tar.gz').open('xb') as output:
        with tarfile.open(fileobj=output, mode='w:gz') as archive:
            for row in rows:
                name='retained/owned'+('' if row['path']=='.' else '/'+row['path'])
                entry=tarfile.TarInfo(name); entry.mode=row['mode']
                if row['type']=='directory':
                    entry.type=tarfile.DIRTYPE; archive.addfile(entry)
                elif row['type']=='symlink':
                    entry.type=tarfile.SYMTYPE; entry.linkname=row['link_target']; archive.addfile(entry)
                else:
                    raw=(OWNED/row['path']).read_bytes()
                    assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
                    entry.size=len(raw); archive.addfile(entry, io.BytesIO(raw))
        output.flush(); os.fsync(output.fileno())
    after_rows, after=inventory(); assert before==after and rows==after_rows
    publish(HERE/'retained-tree01.json',manifest)
    names=('launch-intent01.json','coordinator01.log','coordinator-result01.json',
           'adapter-release03.json','REVIEW_ADAPTER_RELEASE03.md','adapter_tests03.py',
           'adapter_launcher03.py','retained-tree01.json','retained-tree01.tar.gz')
    refs={name:{'path':str((HERE/name).relative_to(ROOT)), 'bytes':(HERE/name).stat().st_size,
                'sha256':digest((HERE/name).read_bytes())} for name in names}
    publish(HERE/'execution-result01.json',{'schema_version':1, 'identity':IDENTITY,
        'status':'closed_failed_storage_symlink_retained_review_pending', 'source':source,
        'session':90521, 'coordinator_exit_code':1, 'closed_at_utc':datetime.now(timezone.utc).isoformat(),
        'guard_limit_reason':guard['limit_reason'], 'launcher_error':terminal['error'],
        'child_exit_code':guard['child_exit_code'], 'oracle_report_present':False,
        'memory_events':guard['memory_events'], 'peak_sampled_memory_bytes':guard['peak_sampled_memory_current_bytes'],
        'cleanup_verified':True, 'cgroup_absent':True, 'pids_absent':{str(pid):True for pid in sorted(pids)},
        'source_pins_verified':len(release['source_files']),
        'complete_retained_tree':{k:v for k,v in manifest.items() if k!='members'}, 'refs':refs,
        'budget':{'spent_empirical':35,'highest_adopted_ceiling':63,'new_empirical_claims':0,'new_financial_fits':0},
        'qualification':'Failed native adapter preserved permanently. Pytest builtin tmp_path created three current symlinks; guard correctly rejected special/link objects. Child log has three dots but no complete four-test/phase report or child_exit snapshot, so no full adapter pass claimed. Native memory events all0; no memory failure. Original workload/readback threads/monitor/cgroup absent. All regular bodies, directory modes and symlink target strings retained without following links or modifying failed tree; allocation includes directories, link target bytes reported separately. No model/criterion change or historical rerun. New successor may change only explicit regular-directory fixture, after exact independent release. Sourcefreeze ended after verified closure.'})
    print(json.dumps({k:v for k,v in manifest.items() if k!='members'}))


if __name__=='__main__':main()
