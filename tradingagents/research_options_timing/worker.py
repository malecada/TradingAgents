"""Single externally anchored raw episode worker. No financial authority.

The public CLI always supervises a child. Public HTTPS is called only after
frozen assignment checks and durable intents. Tests replace acquisition locally.
"""
import argparse
import base64
import contextlib
from datetime import datetime
import re
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

from .journal import Journal, encode, digest, safe
from .schedule import ASSETS, DAY, JOURNALS, calendar, groups, post_exit, validate_entry, nominal_ms, ACQUISITION_DELAY_MS
from .transport import collect

MIB = 1024**2
PHYSICAL_RESERVATION = 8*1024**3
ALLOCATION_UNIT_CEILING = 4096
MINIMUM_FREE_INODES = 1200258
CAPS = dict(zip(JOURNALS, (32*MIB,224*MIB,224*MIB,1472*MIB,16*MIB)))
RESERVES = dict(zip(JOURNALS,(MIB,16*MIB,16*MIB,4*MIB,MIB)))
PACKAGE_FILES = {f'tradingagents/research_options_timing/{n}.py' for n in
                 ('journal','transport','schedule','worker','adapter')}
PACKAGE_FILES.add('release_bootstrap.py')
PACKAGE_FILES.update('research/strategy-search-2026-09-11/options_policy_'+n+'.py' for n in ('selection','batch'))


def read(path, cap):
    path = safe(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_size > cap:
            raise ValueError('bounded regular file required')
        with os.fdopen(fd, 'rb', closefd=False) as stream: return stream.read(cap+1)
    finally: os.close(fd)


def publish(path, value):
    raw = encode(value)
    if len(raw)>MIB: raise ValueError('auxiliary record bound')
    # A single exclusive file is fsynced before it can authorize any next action.
    # Interrupted writes remain and are refused; they are never replaced.
    fd=os.open(safe(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb',closefd=False) as stream:stream.write(raw);stream.flush();os.fsync(fd)
    finally:os.close(fd)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def assignment(package, expected):
    package=safe(package)
    raw=read(package/'assignment.json',MIB)
    if digest(raw)!=expected:raise ValueError('external assignment hash mismatch')
    value=json.loads(raw)
    keys={'schema_version','entry_ms','lease_not_before_ms','lease_expires_ms','claim_path','claim_sha256','package_files','journal_caps','terminal_reserves','authority','target','source_commit','data_root','host_identity'}
    if set(value)!=keys or value['schema_version']!=1:raise ValueError('assignment schema')
    if value['authority']!='raw-worker-only' or value['target']!='options-timing-20260915':raise ValueError('raw worker authority')
    t=validate_entry(value['entry_ms'])
    if value['lease_not_before_ms']!=t-120000 or value['lease_expires_ms']!=t+45*DAY+60000:raise ValueError('fixed worker lease')
    if value['claim_path']!='claim.json' or digest(read(package/'claim.json',512*1024))!=value['claim_sha256']:raise ValueError('claim anchor')
    claim=json.loads(read(package/'claim.json',512*1024))
    if not isinstance(value['source_commit'],str) or not re.fullmatch('[0-9a-f]{40}',value['source_commit']) or claim.get('source')!=value['source_commit']:raise ValueError('claim source commit mismatch')
    protocol=claim['episode_protocol']
    if protocol.get('schema_version')!=3 or protocol.get('hourly_acquisition_delay_ms')!=ACQUISITION_DELAY_MS:raise ValueError('fixed timing protocol required')
    def milliseconds(text):
        dt=datetime.fromisoformat(text.replace('Z','+00:00'))
        if dt.utcoffset() is None or dt.utcoffset().total_seconds()!=0:raise ValueError('UTC lease clock')
        return int(dt.timestamp()*1000)
    if milliseconds(protocol['worker_lease']['not_before'])!=value['lease_not_before_ms'] or milliseconds(protocol['worker_lease']['expires_at'])!=value['lease_expires_ms']:raise ValueError('claim worker lease mismatch')
    if milliseconds(protocol['observation_window']['start'])!=t or milliseconds(protocol['observation_window']['end'])!=t+44*DAY+5000:raise ValueError('claim future observation mismatch')
    if value['journal_caps']!=CAPS or value['terminal_reserves']!=RESERVES:raise ValueError('reviewed journal resource bounds')
    if set(value['package_files'])!=PACKAGE_FILES:raise ValueError('exact frozen source allowlist')
    allowed=set(value['package_files'])|{'assignment.json','claim.json'}
    allowed_dirs={str(parent) for name in allowed for parent in Path(name).parents if str(parent)!='.'}
    for current,dirs,names in os.walk(package,followlinks=False):
        for name in dirs:
            directory=Path(current)/name
            if directory.is_symlink() or directory.relative_to(package).as_posix() not in allowed_dirs:raise ValueError('unregistered source directory/symlink')
        for name in names:
            member=Path(current)/name
            if member.is_symlink() or member.relative_to(package).as_posix() not in allowed:raise ValueError('unregistered package member')
    if not isinstance(value['data_root'],str) or not Path(value['data_root']).is_absolute() or str(safe(value['data_root']))!=value['data_root']:raise ValueError('canonical absolute data root required')
    if value['host_identity']!=os.uname().nodename:raise ValueError('assigned host identity mismatch')
    for name, sha in value['package_files'].items():
        if digest(read(package/name,2*MIB))!=sha:raise ValueError('frozen source changed: '+name)
    if Path(__file__).resolve()!=package/'tradingagents/research_options_timing/worker.py':raise ValueError('worker must execute anchored package')
    return value


def selected_projection(value):
    if set(value)!=set(ASSETS):raise ValueError('both asset selections required')
    result={}
    for asset in ASSETS:
        if value[asset].get('status')!='complete':raise ValueError('initial selection unavailable; no replacement entry')
        result[asset]=value[asset]['selected']
    return result


def resource_reason(*, aggregate_rss, progress_age, clock_drift, wall_ms, lease_end, monotonic_now=0, monotonic_lease_end=float('inf')):
    if aggregate_rss>512*MIB:return 'sampled aggregate RSS limit'
    if progress_age>120:return 'operation/progress watchdog'
    if abs(clock_drift)>.1:return 'wall/monotonic discontinuity'
    if wall_ms>=lease_end or monotonic_now>=monotonic_lease_end:return 'absolute/monotonic lease expired'
    return None


def disk_preflight(data):
    disk=os.statvfs(data)
    if not 0<disk.f_frsize<=ALLOCATION_UNIT_CEILING or not 0<disk.f_bsize<=ALLOCATION_UNIT_CEILING:raise ValueError('filesystem allocation unit exceeds reviewed4KiB bound')
    if disk.f_bavail*disk.f_frsize<PHYSICAL_RESERVATION:raise ValueError('at least8GiB available filesystem reservation required')
    if disk.f_favail<MINIMUM_FREE_INODES:raise ValueError('insufficient free inodes for reviewed journal member envelope')
    return disk


def initial_roles(known):
    expected={'h0000-options-time','h0000-futures-time'}|{f'h0000-{a.lower()}-{role}' for a in ASSETS for role in ('index','perp-depth','perp-mark')}
    if set(known)!=expected:raise ValueError('exact initial prefixed role denominator')
    return {n.removeprefix('h0000-'):value for n,value in known.items()}


def run(package, data, expected, *, acquisition=collect, choose=None,
        now=lambda:time.time_ns()//1000000, sleep=time.sleep, beat=lambda:None):
    """Production child core. Injectable callables are synthetic-test-only API."""
    spec=assignment(package,expected);package=safe(package);data=safe(data)
    if str(data)!=spec['data_root']:raise ValueError('assignment data root mismatch')
    if not spec['lease_not_before_ms']<=now()<spec['lease_expires_ms']:raise ValueError('outside lease')
    data.mkdir(exist_ok=True)
    disk_preflight(data)
    allowed=set(JOURNALS)|{'selection.json','source-seal.json','STOP','worker.lock','supervisor.lock'}
    if any((p.name not in allowed and not re.fullmatch(r'supervisor-exit-[0-9]{6}\.json',p.name)) or p.is_symlink() for p in data.iterdir()):raise ValueError('unregistered data member')
    if (data/'source-seal.json').exists():raise ValueError('sealed source cannot resume')
    import fcntl
    lock=os.open(data/'worker.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if choose is None:
            from .adapter import select_initial
            choose=select_initial
        def check():
            # Source and claim bytes are bounded; no history or market parsing.
            assignment(package,expected)
            if (package/'complete.json').exists() or (package/'failed.json').exists():raise ValueError('outer terminal prohibits capture')
        full=calendar(spec['entry_ms']);selection=None
        if (data/'selection.json').exists():
            saved=json.loads(read(data/'selection.json',MIB))
            if saved['assignment_sha256']!=expected:raise ValueError('selection assignment changed')
            initial=json.loads(read(data/'bootstrap'/'receipt-initial-options-rules.json',16*MIB))
            known={n:json.loads(read(data/'known'/('receipt-'+n+'.json'),MIB)) for n in groups(full['known'])[0][1]}
            bindings={'initial':digest(encode(initial)),**{n:digest(encode(r)) for n,r in known.items()}}
            if saved['input_sha256']!=bindings or saved['result']!=choose(initial,initial_roles(known),entry_ms=spec['entry_ms']):raise ValueError('selection differs from frozen initial source')
            selection=selected_projection(saved['result']);full=calendar(spec['entry_ms'],selection)
        with contextlib.ExitStack() as stack:
            journals={}
            def open_journal(name):
                journal=Journal(data/name,claim_path=package/'claim.json',claim_sha256=spec['claim_sha256'],
                    slots=full[name],total_cap=CAPS[name],terminal_reserve=RESERVES[name],check_source=check)
                journals[name]=stack.enter_context(journal)
                journal.recover(now_ms=now())
            for name in JOURNALS:
                if name!='selected' or selection is not None:open_journal(name)
            events=sorted((at,name,names) for name,slots in full.items() for at,names in groups(slots))
            # First known group precedes selected group, independent of sorting.
            rank={name:i for i,name in enumerate(('bootstrap','known','selected','daily','final'))}
            events.sort(key=lambda x:(x[0],rank[x[1]]))
            failed=None
            try:
                pos=0
                if selection is None and now()>spec['entry_ms']+5000:raise ValueError('initial selection absent after entry; no replacement')
                while pos<len(events):
                    beat()
                    clock=now()
                    if (data/'STOP').exists():raise ValueError('explicit stop requested')
                    if clock>=spec['lease_expires_ms']:raise ValueError('lease expired')
                    at,name,names=events[pos]
                    if clock<at:sleep(min(.1,(at-clock)/1000));continue
                    journal=journals[name]
                    event_slot=journal.slots[names[0]]
                    nominal=nominal_ms(spec['entry_ms'],event_slot)
                    deadline=event_slot['deadline_ms']
                    if any(journal.slots[n]['deadline_ms']!=deadline or nominal_ms(spec['entry_ms'],journal.slots[n])!=nominal for n in names):raise ValueError('inconsistent group clocks')
                    states=journal._states
                    unresolved=[n for n in names if states[n]['status']=='future_or_unattempted']
                    if not unresolved:
                        if nominal==spec['entry_ms'] and name=='known' and selection is None:
                            raise ValueError('initial source consumed without immutable selection; no retry')
                        pos+=1;continue
                    if len(unresolved)!=len(names):raise ValueError('partial group cannot be retried')
                    if clock>deadline:
                        journal.recover(now_ms=clock);pos+=1
                        if nominal==spec['entry_ms'] and name=='known' and selection is None:raise ValueError('missed initial entry')
                        continue
                    journal.begin_group(names,now_ms=clock)
                    active=[]
                    for n in names:
                        if selection is not None and name in ('known','selected') and post_exit(n,nominal,selection):
                            journal.record(n,b'',metadata={'attempted':False,'reason':'frozen post-exit unused slot'})
                        else:active.append(n)
                    if active:
                        result=acquisition(journal,active,deadline_ms=deadline)
                        if result.get('halt_on_access_restriction'):raise ValueError('public access restriction; no further groups')
                    pos+=1
                    if nominal==spec['entry_ms'] and name=='known' and selection is None:
                        initial=json.loads(read(data/'bootstrap'/'receipt-initial-options-rules.json',16*MIB))
                        known={n:json.loads(read(data/'known'/('receipt-'+n+'.json'),MIB)) for n in names}
                        chosen=choose(initial,initial_roles(known),entry_ms=nominal)
                        saved={'assignment_sha256':expected,'result':chosen,
                               'input_sha256':{'initial':digest(encode(initial)),**{n:digest(encode(r)) for n,r in known.items()}}}
                        publish(data/'selection.json',saved)
                        selection=selected_projection(chosen);full=calendar(spec['entry_ms'],selection)
                        open_journal('selected')
                        extra=[(a,'selected',ns) for a,ns in groups(full['selected'])]
                        events=events[:pos]+sorted(events[pos:]+extra,key=lambda x:(x[0],rank[x[1]]))
                        if now()>deadline:raise ValueError('selection missed entry deadline')
                for journal in journals.values():journal.recover(now_ms=now())
            except Exception as exc:failed=type(exc).__name__+': '+str(exc)[:300]
            seals={}
            for name,journal in journals.items():
                journal.recover(now_ms=now())
                seals[name]=journal.seal('failed' if failed else 'complete')
            # A failed initial selection still preserves all8456 conditional
            # selected roles by fixed calendar count, without inventing symbols.
            value={'assignment_sha256':expected,'status':'failed' if failed else 'complete',
                   'reason':failed,'journal_seals':seals,'intended_slot_count':17144,
                   'unresolved_selected_slots':8456 if selection is None else 0,
                   'unresolved_selected_ids_sha256':digest(encode([f'h{h:04d}-{a.lower()}-{side}-{role}' for h in range(1057) for a in ASSETS for side in ('call','put') for role in ('depth','mark')])) if selection is None else None,
                   'failure_scope':'Source operability only; no economic rejection of either asset or strategy family.',
                   'selection_sha256':digest(read(data/'selection.json',MIB)) if (data/'selection.json').exists() else None,
                   'quiescent_ms':now(),'scope':'raw source seal only; no financial or outer terminal authority'}
            publish(data/'source-seal.json',value)
            return value
    finally:os.close(lock)


def tree_rss(pid):
    """Linux sampled live descendant RSS. Shared pages deliberately count twice."""
    pending=[pid];seen=set();rss=0
    while pending:
        child=pending.pop()
        if child in seen:continue
        seen.add(child)
        try:
            status=Path(f'/proc/{child}/status').read_text()
            rss+=next(int(line.split()[1])*1024 for line in status.splitlines() if line.startswith('VmRSS:'))
            pending.extend(map(int,Path(f'/proc/{child}/task/{child}/children').read_text().split()))
        except (FileNotFoundError,ProcessLookupError,StopIteration):pass
    return rss,seen


def supervise(package,data,expected):
    spec=assignment(package,expected);data=safe(data)
    if str(data)!=spec['data_root']:raise ValueError('assignment data root mismatch')
    data.mkdir(exist_ok=True)
    import fcntl
    fd=os.open(data/'supervisor.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _supervise_locked(package,data,expected)
    finally:os.close(fd)


def _supervise_locked(package,data,expected):
    spec=assignment(package,expected);data=safe(data)
    if str(data)!=spec['data_root']:raise ValueError('assignment data root mismatch')
    if sys.version_info[:3]!=(3,13,13):raise ValueError('pinned Python3.13.13 required')
    if not spec['lease_not_before_ms']<=time.time()*1000<spec['lease_expires_ms']:raise ValueError('outside lease')
    data.mkdir(exist_ok=True)
    prior=sorted(data.glob('supervisor-exit-*.json'))
    if len(prior)>=64 or any(p.is_symlink() or p.stat().st_size>128*1024 for p in prior):raise ValueError('supervisor record bound')
    if [p.name for p in prior]!=[f'supervisor-exit-{i:06d}.json' for i in range(len(prior))]:raise ValueError('supervisor record sequence')
    if any(json.loads(read(p,128*1024)).get('assignment_sha256')!=expected for p in prior):raise ValueError('supervisor record assignment changed')
    cpus=sorted(os.sched_getaffinity(0))[:2];os.sched_setaffinity(0,cpus)
    r,w=os.pipe();os.set_blocking(r,False)
    command=[sys.executable,'-I','-B',str(package/'release_bootstrap.py'),str(package),str(data),expected,'--child-fd',str(w)]
    process=subprocess.Popen(command,cwd=package,pass_fds=(w,),start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    os.close(w);os.set_blocking(process.stderr.fileno(),False)
    last=time.monotonic();previous_wall=time.time();previous_mono=last
    monotonic_lease_end=last+max(0,spec['lease_expires_ms']/1000-previous_wall)
    reason=None;stderr=bytearray();stderr_bytes=0;peak=0
    def drain():
        nonlocal stderr_bytes
        try:
            chunk=os.read(process.stderr.fileno(),65536)
            stderr_bytes+=len(chunk);stderr.extend(chunk[:max(0,65536-len(stderr))])
        except BlockingIOError:pass
    try:
        while process.poll() is None:
            try:
                if os.read(r,65536):last=time.monotonic()
            except BlockingIOError:pass
            drain();mono=time.monotonic();wall=time.time();rss=tree_rss(os.getpid())[0];peak=max(peak,rss)
            reason=resource_reason(aggregate_rss=rss,progress_age=mono-last,
                                   clock_drift=(wall-previous_wall)-(mono-previous_mono),wall_ms=wall*1000,
                                   lease_end=spec['lease_expires_ms'],monotonic_now=mono,monotonic_lease_end=monotonic_lease_end)
            previous_wall=wall;previous_mono=mono
            if reason:break
            time.sleep(.1)
    except BaseException as exc:
        reason=type(exc).__name__+': supervisor interrupted'
        raise
    finally:
        if process.poll() is None:
            _,descendants=tree_rss(process.pid)
            for pid in descendants:
                try:os.kill(pid,signal.SIGKILL)
                except ProcessLookupError:pass
        process.wait(timeout=5);drain();process.stderr.close();os.close(r)
        publish(data/f'supervisor-exit-{len(prior):06d}.json',
                {'assignment_sha256':expected,'ended_ms':time.time_ns()//1000000,'child_pid':process.pid,
                 'child_exit_code':process.returncode,'reason':reason or 'child exited with code '+str(process.returncode),'sampled_peak_aggregate_rss':peak,
                 'stderr_base64':base64.b64encode(stderr).decode(),'stderr_bytes_observed':stderr_bytes,
                 'stderr_truncated':stderr_bytes>len(stderr),'scope':'Supervisor exit evidence; raw journal admission remains separate.'})
    if reason:raise RuntimeError(reason+'; preserve interrupted intents, no automatic restart')
    return process.returncode


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path);parser.add_argument('data',type=Path);parser.add_argument('assignment_sha256')
    parser.add_argument('--child-fd',type=int)
    args=parser.parse_args()
    if args.child_fd is None:return supervise(args.package,args.data,args.assignment_sha256)
    # Inherited pipe is essential; direct child invocation without it fails.
    if not stat.S_ISFIFO(os.fstat(args.child_fd).st_mode):raise ValueError('supervisor pipe required')
    import ctypes
    parent=os.getppid()
    if ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGKILL,0,0,0)!=0 or os.getppid()!=parent:raise ValueError('parent death guard unavailable')
    result=run(args.package,args.data,args.assignment_sha256,beat=lambda:os.write(args.child_fd,b'.'))
    return 0 if result['status']=='complete' else 2


if __name__=='__main__':raise SystemExit(main())
