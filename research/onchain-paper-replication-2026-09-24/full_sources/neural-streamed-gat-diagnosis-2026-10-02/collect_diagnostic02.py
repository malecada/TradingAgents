"""Preserve the closed four-arm diagnostic once; no numerical imports or execution."""
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
IDENTITY = 'neural-streamed-gat-diagnostic-20261002-01'
OWNED = HERE / 'owned' / IDENTITY


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def publish(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    assert len(raw) < 1024**2
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def inventory():
    assert OWNED.resolve() == OWNED
    rows = []
    signatures = {}
    paths = [OWNED]
    while paths:
        path = paths.pop()
        info = path.lstat()
        relative = str(path.relative_to(OWNED))
        assert len(Path(relative).parts) <= 32
        signatures[relative] = (info.st_dev, info.st_ino, info.st_mode,
                               info.st_nlink, info.st_size, info.st_blocks,
                               info.st_mtime_ns, info.st_ctime_ns)
        row = {'role': 'owned', 'path': relative,
               'mode': stat.S_IMODE(info.st_mode),
               'allocated_bytes': info.st_blocks*512}
        if stat.S_ISDIR(info.st_mode):
            row['type'] = 'directory'
            paths.extend(sorted(path.iterdir(), reverse=True))
        else:
            assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            assert info.st_size <= 4*1024**2
            raw = path.read_bytes()
            assert len(raw) == info.st_size
            row.update(type='file', bytes=len(raw), sha256=digest(raw))
        rows.append(row)
        assert len(rows)+len(paths) <= 12000
    rows.sort(key=lambda row: row['path'])
    assert sum(row['allocated_bytes'] for row in rows) <= 64*1024**2
    assert sum(row.get('bytes', 0) for row in rows) <= 64*1024**2
    return rows, signatures


def main():
    guard = json.loads((OWNED/'guard/final.json').read_bytes())
    ready = json.loads((OWNED/'guard/cpu_ready.json').read_bytes())
    child = json.loads((OWNED/'guard/child_exit.json').read_bytes())
    oracle = json.loads((OWNED/'oracle-report.json').read_bytes())
    terminal = json.loads((OWNED/'launcher-terminal.json').read_bytes())
    assert guard['cleanup_verified'] is True
    assert guard['cleanup_stop_returncode'] == 5
    assert guard['phase'] == 'complete' and child['exit_code'] == 0
    assert terminal['status'] == 'failed' and terminal['retry'] is False
    assert not Path(guard['cgroup']).exists()
    pids = {guard['monitor_pid'], ready['pid'], child['workload_pid']}
    pids.update(int(pid) for pid in guard['cpu_thread_readback'])
    assert all(not Path('/proc', str(pid)).exists() for pid in pids)
    assert oracle['status'] == 'observed_disagreement'
    assert oracle['arm_order'] == ['eager_eager','einsum_eager','eager_streamed','einsum_streamed']
    assert all(row['status']=='observed' for row in oracle['arms'].values())
    assert all(value == 0 for value in guard['memory_events'].values())
    release = json.loads((HERE/'diagnostic-release02.json').read_bytes())
    for path, expected in release['source_files'].items():
        assert digest((ROOT/path).read_bytes()) == expected
    source = json.loads((OWNED/'reservation.json').read_bytes())['head']
    assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT,
                                   text=True, timeout=10).strip() == source
    rows, before = inventory()
    manifest = {'schema_version': 1, 'identity': IDENTITY, 'members': rows,
                'files': sum(row['type']=='file' for row in rows),
                'directories_including_each_root': sum(row['type']=='directory' for row in rows),
                'entries_including_each_root': len(rows),
                'logical_bytes': sum(row.get('bytes', 0) for row in rows),
                'allocated_bytes_including_directories': sum(row['allocated_bytes'] for row in rows)}
    with (HERE/'retained-tree01.tar.gz').open('xb') as output:
        with tarfile.open(fileobj=output, mode='w:gz') as archive:
            for row in rows:
                name='retained/owned'+('' if row['path']=='.' else '/'+row['path'])
                entry=tarfile.TarInfo(name);entry.mode=row['mode']
                if row['type']=='directory':
                    entry.type=tarfile.DIRTYPE;archive.addfile(entry)
                else:
                    raw=(OWNED/row['path']).read_bytes()
                    assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
                    entry.size=len(raw)
                    archive.addfile(entry, io.BytesIO(raw))
        output.flush();os.fsync(output.fileno())
    after_rows, after = inventory()
    assert before == after and rows == after_rows
    publish(HERE/'retained-tree01.json', manifest)
    names=('launch-intent01.json','coordinator01.log',
           'coordinator-result01.json','diagnostic-release02.json',
           'REVIEW_DIAGNOSTIC_RELEASE02.md','candidate01.py','source-manifest01.json',
           'diagnostic01.py','PROTOCOL01.md','diagnostic_launcher02.py',
           'retained-tree01.json','retained-tree01.tar.gz')
    refs={}
    for name in names:
        path=HERE/name;raw=path.read_bytes()
        refs[name]={'path':str(path.relative_to(ROOT)), 'bytes':len(raw), 'sha256':digest(raw)}
    publish(HERE/'execution-result01.json', {
        'schema_version':1, 'status':'closed_diagnostic_observed_parent_failed_independent_review_pending',
        'identity':IDENTITY, 'source':source, 'session':33910,
        'closed_at_utc':datetime.now(timezone.utc).isoformat(),
        'coordinator_exit_code':1, 'guard_worker_exit_code':child['exit_code'],
        'guard_elapsed_seconds':guard['elapsed_seconds'], 'guard_unit':guard['unit'],
        'observed_arm_order':oracle['arm_order'], 'diagnostic_status':oracle['status'],
        'cleanup_stop_returncode':guard['cleanup_stop_returncode'],
        'launcher_failure':terminal['error'],
        'memory_events':guard['memory_events'],
        'peak_sampled_memory_bytes':guard['peak_sampled_memory_current_bytes'],
        'cleanup_verified':True, 'cgroup_absent':True,
        'pids_absent':{str(pid):True for pid in sorted(pids)},
        'complete_retained_tree':{key:value for key,value in manifest.items() if key!='members'},
        'refs':refs,
        'budget':{'spent_empirical':35,'highest_adopted_ceiling':63,
                  'new_empirical_claims':0,'new_financial_fits':0},
        'qualification':'All four prescribed tiny arms observed disagreement. Eagerattention with streamedmessages matches all recorded tensors; einsum attention causes three updated-parameter mismatches regardless of aggregation. Named first-step Adam reconstruction and tiny-gradient values are retained in raw report. Overall parent remains failed because its validator required cleanup-stop return0 while actual return5 occurred with verified cleanup, native success/inactive/dead/empty cgroup and original process absence. No rerun, retroactive passing terminal, candidate GREEN acceptance, empirical capacity or financial claim. Complete original final owned tree preserved; overwritten live states are not separately recovered. Sampled peak is not lifetime peak; allocated counts describe original host, not tar media.'})
    print(json.dumps({'status':'closed_diagnostic_observed_parent_failed_preserved','files':manifest['files'],
                      'directories':manifest['directories_including_each_root'],
                      'entries':len(rows),'logical_bytes':manifest['logical_bytes'],
                      'allocated_bytes':manifest['allocated_bytes_including_directories'],
                      'source_freeze':'ended_after_verified_closure'}))


if __name__ == '__main__':
    main()
