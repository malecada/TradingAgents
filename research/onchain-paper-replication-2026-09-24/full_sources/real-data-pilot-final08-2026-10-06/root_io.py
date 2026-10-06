"""Concrete Root IO seam for the one fixed real-data pilot.

The existing job supervisor, admission, native limits and scientific method
remain responsible for execution. This file only captures outer logs and
observes storage after actual process return and log closure.
"""
from pathlib import Path
import datetime
import json
import os
import subprocess

EXPERIMENT = 'eth-paper-real-data-end-to-end-resource-20261006-08'
PREFIX = 'research_artifacts/onchain-paper-replication-2026-09-24'


def capture(command, root, logs, observer):
    logs.mkdir(exist_ok=False)
    streams = []
    process = None
    primary = None
    value = {'actual_parent_exit_code': None, 'supervisor_pid': None,
             'supervisor_reaped': False, 'outer_log_handles_closed': False}
    try:
        streams.append((logs/'stdout.log').open('xb'))
        streams.append((logs/'stderr.log').open('xb'))
        process = subprocess.Popen(command, cwd=root, stdout=streams[0], stderr=streams[1])
        value['supervisor_pid'] = process.pid
        value['actual_parent_exit_code'] = process.wait()
        value['supervisor_reaped'] = True
    except BaseException as error:
        primary = error
        raise
    finally:
        if process is not None and not value['supervisor_reaped']:
            try:
                if process.poll() is None:
                    process.kill()
                value['actual_parent_exit_code'] = process.wait()
                value['supervisor_reaped'] = True
            except BaseException as error:
                if primary is None:
                    primary = error
                else:
                    primary.add_note('Root supervisor cleanup: '+repr(error))
        later = []
        for stream in streams:
            try:
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException as error:
                later.append(error)
            finally:
                try:
                    stream.close()
                except BaseException as error:
                    later.append(error)
        value['outer_log_handles_closed'] = all(stream.closed for stream in streams)
        value['at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            observer(value)
        except BaseException as error:
            later.append(error)
        if primary is not None:
            for error in later:
                primary.add_note('Root post-process observation/IO: '+repr(error))
        elif later:
            raise later[0]
    return value


def final_storage(args, job, io):
    """Actual terminal closure is required; missing evidence stays unavailable."""
    from tradingagents.research.onchain_replication import job as original_job, resources
    from tradingagents.research.onchain_replication.real_pilot_storage import WritableUnion
    from tradingagents.research.onchain_replication.provenance import file_hash
    root = Path(args.root)
    if args.experiment != EXPERIMENT or not io['outer_log_handles_closed'] or not io['supervisor_reaped']:
        raise ValueError('Fixed pilot actual process/log closure is missing')
    base = root/PREFIX/'runs'/EXPERIMENT
    paths = {key:base/name for key,name in (
        ('launch','launch.json'),('owner','owner.json'),('guard','guard/final.json'))}
    bodies = {}
    for key,path in paths.items():
        if path.is_symlink() or path.stat().st_size > 4*1024**2:
            raise ValueError('Final bounded native metadata differs')
        bodies[key] = json.loads(path.read_bytes())
    launch, owner, guard = (bodies[key] for key in ('launch','owner','guard'))
    if launch['supervisor_pid'] != io['supervisor_pid'] or launch['source_commit'] != args.source or launch['experiment'] != EXPERIMENT:
        raise ValueError('Actual reaped supervisor does not match original launch')
    if owner['supervisor_pid'] != launch['supervisor_pid'] or owner['nonce'] != launch['nonce']:
        raise ValueError('Original monitor owner differs')
    if original_job.same_process_alive(owner['monitor_pid'], owner['monitor_start_ticks']):
        raise ValueError('Original monitor still owns outer log descriptors')
    if guard.get('cleanup_verified') is not True or guard.get('monitor_pid') != owner['monitor_pid']:
        raise ValueError('Actual final native cleanup remains unavailable')
    cgroup = Path(guard['cgroup'])
    if not cgroup.is_relative_to('/sys/fs/cgroup/user.slice') or cgroup.exists():
        raise ValueError('Original native cgroup remains present or differs')
    current = resources._systemctl('show',guard['unit'],
        '--property=ControlGroup,ActiveState,SubState,ExecMainStatus,Result,MainPID')
    current_unit = dict(line.split('=',1) for line in current.stdout.splitlines() if '=' in line)
    if current_unit.get('ActiveState') not in ('inactive','failed') or current_unit.get('MainPID') != '0' or current_unit.get('ControlGroup') != '':
        raise ValueError('Native unit is still active or closure is unavailable')
    observation = WritableUnion(job['resources']['storage_budget'],root).check()
    return {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'experiment':EXPERIMENT,'source':args.source,
        'original_metadata_sha256':{key:file_hash(path) for key,path in paths.items()},
        'actual_current_unit_properties':current_unit,'actual_current_cgroup_absent':True,
        'outer_log_handles_closed':True,'supervisor_reaped':True,
        'original_monitor_process_absent':True,'storage_observation':observation,
        'qualification':'Actual sampled post-process WritableUnion observation after the reaped supervisor, original monitor and native cgroup closed. No global writer exclusion, atomic snapshot, hard quota, whole-job peak or scientific completion is inferred.'}


def launch_checked(args, preflight, here):
    from tradingagents.research.onchain_replication.job import _admitted, _command
    from tradingagents.research.lifecycle import _immutable
    if args.experiment != EXPERIMENT:
        raise ValueError('This Root IO seam admits only the fixed unused pilot')
    _, job = _admitted(args)
    root = Path(args.root)
    logs = root/PREFIX/'pilot-parent'/EXPERIMENT
    if logs.parent.resolve(strict=True) != logs.parent:
        raise ValueError('Existing pilot-parent domain must be canonical')
    _immutable(here/'launch-attempt01.json',preflight)
    def observe(io):
        _immutable(here/'ROOT_IO_CLOSED01.json',io)
        try:
            final = final_storage(args,job,io)
        except BaseException as error:
            _immutable(here/'FINAL_STORAGE_UNAVAILABLE01.json',
                       {'reason':repr(error),'actual_parent_exit_code':io['actual_parent_exit_code'],
                        'qualification':'Missing or failed final observation is retained without a capacity or successful pilot claim.'})
            raise
        _immutable(here/'FINAL_STORAGE01.json',final)
    return capture(_command(args,'launch'),root,logs,observe)


if __name__ == '__main__':
    # Final exact preflight is separately bound/reviewed in the execution dir.
    from preflight01 import check
    args, preflight = check()
    result = launch_checked(args,preflight,Path(__file__).resolve().parent)
    raise SystemExit(result['actual_parent_exit_code'])
