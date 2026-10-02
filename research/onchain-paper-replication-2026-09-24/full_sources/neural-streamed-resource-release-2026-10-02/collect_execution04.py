"""Retain the terminal neural04 failure; no numerical execution or retry."""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
IDENTITY = 'eth-paper-neural-resource-20261002-04'
SOURCE = '8631cbcce34cf827f0551dad04f6822ca8e1e1ec'
ROLES = {
    'control': ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/IDENTITY,
    'lifecycle': ROOT/'research_runs'/IDENTITY,
    'producer': ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/IDENTITY,
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    assert len(raw) <= 4*1024**2
    with path.open('xb') as output:
        output.write(raw); output.flush(); os.fsync(output.fileno())


def publish(path, value):
    write(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())


def load(path):
    assert path.stat().st_size <= 8*1024**2
    return json.loads(path.read_bytes())


def inventory():
    rows = []; signatures = {}
    for role, root in ROLES.items():
        assert root.resolve() == root
        pending = [root]
        while pending:
            path = pending.pop(); info = path.lstat(); relative = str(path.relative_to(root))
            assert len(Path(relative).parts) <= 32
            signatures[(role, relative)] = (info.st_dev, info.st_ino, info.st_mode,
                info.st_nlink, info.st_size, info.st_blocks, info.st_mtime_ns, info.st_ctime_ns)
            row = {'role': role, 'path': relative, 'mode': stat.S_IMODE(info.st_mode),
                   'allocated_bytes': info.st_blocks*512}
            if stat.S_ISDIR(info.st_mode):
                row['type'] = 'directory'; pending.extend(sorted(path.iterdir(), reverse=True))
            elif stat.S_ISLNK(info.st_mode):
                raw = os.fsencode(os.readlink(path)); assert len(raw) <= 4096
                row.update(type='symlink', link_target=os.fsdecode(raw), link_bytes=len(raw), link_sha256=digest(raw))
            else:
                assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 8*1024**2
                raw = path.read_bytes(); assert len(raw) == info.st_size
                row.update(type='file', bytes=len(raw), sha256=digest(raw))
            rows.append(row); assert len(rows)+len(pending) <= 128
    rows.sort(key=lambda row: (row['role'], row['path']))
    assert sum(row.get('bytes', 0)+row.get('link_bytes', 0) for row in rows) <= 128*1024**2
    assert sum(row['allocated_bytes'] for row in rows) <= 160*1024**2
    return rows, signatures


def command_receipt(name, command):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
    assert len(result.stdout)+len(result.stderr) <= 4*1024**2
    write(HERE/(name+'.txt'), result.stdout+result.stderr)
    return {'command': command, 'returncode': result.returncode,
            'stdout_bytes': len(result.stdout), 'stderr_bytes': len(result.stderr),
            'stdout_sha256': digest(result.stdout), 'stderr_sha256': digest(result.stderr)}, result.stdout


def main():
    control = ROLES['control']; lifecycle = ROLES['lifecycle']
    claim = load(lifecycle/'claim.json'); terminal = load(lifecycle/'failed.json')
    guard = load(control/'guard/final.json'); ready = load(control/'guard/cpu_ready.json')
    observer = load(control/'observer.json'); cells = load(control/'postmortem-cells.json')
    phase = load(ROLES['producer']/'cell-00/phase-journal.json')
    assert claim['source'] == SOURCE and claim['experiment_id'] == IDENTITY
    assert digest((lifecycle/'claim.json').read_bytes()) == terminal['claim_sha256']
    assert terminal['status'] == guard['phase'] == observer['status'] == 'failed'
    assert guard['cleanup_verified'] is True and guard['cleanup_stop_returncode'] == 0
    assert guard['cleanup_unit_properties']['Result'] == 'oom-kill'
    assert guard['cleanup_unit_properties']['ExecMainStatus'] == '9'
    assert guard['child_exit_code'] is None
    assert guard['memory_max_bytes'] == guard['memory_high_bytes'] == 4026531840
    assert guard['memory_swap_max_bytes'] == 0 and guard['reserve_bytes'] == 3221225472
    assert guard['disk_floor_bytes'] == 10737418240 and guard['wall_seconds'] == 7200
    assert guard['memory_events'] == {'high':0, 'low':0, 'max':2181, 'oom':2, 'oom_group_kill':1, 'oom_kill':3}
    assert guard['peak_sampled_memory_current_bytes'] == 4026531840
    assert phase['schema_version'] == 2 and len(phase['events']) == 9
    assert phase['events'][-1]['event'] == 'forward_before'
    assert len(cells) == 9 and all(cell['status'] == 'unavailable' for cell in cells)
    assert [cell['id'] for cell in cells] == [cell['id'] for cell in claim['experiment']['cells']]
    for name, expected in observer['evidence_sha256'].items():
        assert digest((control/name).read_bytes()) == expected
    assert digest((lifecycle/'failed.json').read_bytes()) == observer['terminal_sha256']
    assert digest((control/'owner.json').read_bytes()) == observer['owner_sha256']
    assert load(control/'guard/release.json')['kernel_controls_verified'] is True
    receipts = {}
    receipts['unit'], unit_body = command_receipt('unit-journal04',
        ['journalctl','--user','--utc','--no-pager','--output=short-iso-precise',
         '--since','2026-10-02 20:35:00 UTC','--until','2026-10-02 20:45:00 UTC','--unit',guard['unit']])
    receipts['kernel'], kernel_body = command_receipt('kernel-journal04',
        ['journalctl','-k','--utc','--no-pager','--output=short-iso-precise',
         '--since','2026-10-02 20:35:00 UTC','--until','2026-10-02 20:45:00 UTC','--grep',guard['unit']])
    receipts['unit_current'], current = command_receipt('unit-properties04',
        ['systemctl','--user','show',guard['unit'],'--property=ActiveState,SubState,Result,ExecMainStatus,ControlGroup,MainPID'])
    properties = dict(line.split('=',1) for line in current.decode().splitlines() if '=' in line)
    assert properties['ControlGroup'] == '' and properties['MainPID'] == '0'
    assert properties['ActiveState'] in ('failed','inactive') and properties['Result'] == 'oom-kill'
    pids = {guard['monitor_pid'], guard['owner_identity']['supervisor_pid'], ready['pid']}
    for body in (unit_body, kernel_body):
        pids.update(int(match) for match in re.findall(rb'(?:Killed process|Killing process|Main process exited[^\n]*?pid=)\s*(\d+)',body))
    pids_absent = {str(pid): not Path('/proc',str(pid)).exists() for pid in sorted(pids)}
    assert all(pids_absent.values()) and not Path(guard['cgroup']).exists()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == SOURCE
    for path, expected in claim['experiment']['source_files'].items():
        assert digest((ROOT/path).read_bytes()) == expected
        assert digest(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT,timeout=10)) == expected
    for path, expected in claim['experiment']['runtime_hashes'].items():
        assert digest((ROOT/'tradingagents/research'/path).read_bytes()) == expected
    inputs_verified = 0
    for value in claim['inputs'].values():
        h = hashlib.sha256()
        with (ROOT/value['path']).open('rb') as stream:
            for block in iter(lambda: stream.read(65536), b''): h.update(block)
        assert h.hexdigest() == value['sha256']; inputs_verified += 1
    prior = load(HERE.parent/'neural-streamed-budget-preparation-2026-10-02/population03.json')
    statuses = []
    for row in prior['current_claims']:
        root = ROOT/'research_runs'/row['experiment']
        assert digest((root/'claim.json').read_bytes()) == row['claim_sha256']
        assert digest((root/(row['terminal_status']+'.json')).read_bytes()) == row['terminal_sha256']
        statuses.append(row['terminal_status'])
    for row in prior['prior_claims']:
        for role in ('claim','terminal'):
            assert digest((ROOT/row[role]['path']).read_bytes()) == row[role]['sha256']
        statuses.append(row['terminal_status'])
    statuses.append('failed'); assert len(statuses) == 36
    assert statuses.count('complete') == 27 and statuses.count('failed') == 9
    assert claim['effective_attempt_budget'] == 64
    rows, before = inventory()
    manifest = {'schema_version':1, 'identity':IDENTITY, 'members':rows,
        'files':sum(row['type']=='file' for row in rows),
        'directories_including_each_root':sum(row['type']=='directory' for row in rows),
        'symlinks':sum(row['type']=='symlink' for row in rows), 'entries_including_each_root':len(rows),
        'logical_bytes':sum(row.get('bytes',0)+row.get('link_bytes',0) for row in rows),
        'allocated_bytes_including_directories':sum(row['allocated_bytes'] for row in rows)}
    with (HERE/'retained-tree04.tar.gz').open('xb') as output:
        with tarfile.open(fileobj=output,mode='w:gz') as archive:
            for row in rows:
                entry = tarfile.TarInfo('retained/'+row['role']+('' if row['path']=='.' else '/'+row['path']))
                entry.mode = row['mode']
                if row['type']=='directory': entry.type=tarfile.DIRTYPE; archive.addfile(entry)
                elif row['type']=='symlink': entry.type=tarfile.SYMTYPE; entry.linkname=row['link_target']; archive.addfile(entry)
                else:
                    raw=(ROLES[row['role']]/row['path']).read_bytes()
                    assert digest(raw)==row['sha256'] and len(raw)==row['bytes']
                    entry.size=len(raw); archive.addfile(entry,io.BytesIO(raw))
        output.flush(); os.fsync(output.fileno())
    after_rows, after = inventory(); assert rows == after_rows and before == after
    publish(HERE/'retained-tree04.json',manifest)
    names = ('admission02.json','readiness02.json','launch-intent02.json','launch02.log',
        'gate.json','source-manifest01.json','neural-plan.json','resource-amendment.json',
        'unit-journal04.txt','kernel-journal04.txt','unit-properties04.txt',
        'retained-tree04.json','retained-tree04.tar.gz','collect_execution04.py')
    refs = {name:{'path':str((HERE/name).relative_to(ROOT)), 'bytes':(HERE/name).stat().st_size,
                  'sha256':digest((HERE/name).read_bytes())} for name in names}
    publish(HERE/'execution-result04.json',{'schema_version':1, 'identity':IDENTITY,
        'status':'closed_failed_kernel_oom_retained_review_pending', 'source':SOURCE,
        'session':82271, 'coordinator_exit_code':1, 'terminal':terminal,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(), 'child_exit_code':None,
        'guard_phase':guard['phase'], 'cleanup_verified':True, 'cleanup_stop_returncode':0,
        'unit_properties_observed':properties, 'journal_commands':receipts,
        'cgroup_absent':True, 'pids_absent':pids_absent,
        'pid_qualification':'All explicitly recorded owner/supervisor/cpu-ready and identified journal PIDs absent; vanished unit cgroup proves no remaining owned descendants. Final cpu_thread_readback is empty after death, not reconstructed.',
        'memory_events':guard['memory_events'], 'peak_sampled_memory_bytes':guard['peak_sampled_memory_current_bytes'],
        'last_sampled_memory_bytes':guard['memory_current_bytes'], 'phase_schema':2,
        'phase_count':9, 'last_phase':phase['events'][-1], 'cells':cells,
        'source_pins_verified':len(claim['experiment']['source_files']),
        'runtime_pins_verified':len(claim['experiment']['runtime_hashes']), 'input_pins_verified':inputs_verified,
        'complete_retained_tree':{k:v for k,v in manifest.items() if k!='members'}, 'refs':refs,
        'budget':{'spent_empirical':36, 'closed_complete':27, 'closed_failed':9,
                  'highest_adopted_ceiling':64, 'new_financial_fits':0, 'refunds':0},
        'qualification':'Actual streamed full-size trial failed at native 3.75GiB hard high=max with kernel OOM. Startup 16-row window passed; host reserve remained satisfied at final sample. Forward_before marks intent only; exact allocating suboperation and larger capacity required are unknown. No returned forward, backward, optimizer or checkpoint proof. Nine cells unavailable; financial1420 fits remain pending. No retry/checkpoint-policy/cap-ladder authority. Complete raw three-root bodies/directory modes plus separate outer receipts retained; sourcefreeze ends after this verified closure. Native CPU quota unavailable; twoCPU ready receipt retained.'})
    print(json.dumps({'status':'retained_failed04', 'pids_absent':pids_absent,
        'tree':{k:v for k,v in manifest.items() if k!='members'}, 'budget_spent':36}))


if __name__=='__main__': main()
