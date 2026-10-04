"""Read-only failed-owner evidence check; caller must separately admit ancestry.

No process action, ledger mutation, array read, recovery or continuation occurs.
This is a checked observation, not a lock or a substitute for ResearchRun.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

MAX_BYTES=2*1024**2
PREFIX='research_artifacts/onchain-paper-replication-2026-09-24/runs'
MODULE='tradingagents.research.onchain_replication.job'


def require(value,message):
    if not value:raise ValueError(message)


def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def equal(a,b):return encode(a)==encode(b)
def boot_id():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def pid_exists(pid):return (Path('/proc')/str(pid)).exists()


def same_process_alive(pid,ticks):
    require(type(pid) is int and pid>0 and isinstance(ticks,str) and ticks.isdecimal(),'invalid process identity')
    try:return (Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19]==ticks
    except FileNotFoundError:return False


def group_populated(path):
    if not path.exists():return False
    require(path.resolve()==path,'cgroup symlink forbidden')
    values=dict(row.split() for row in (path/'cgroup.events').read_text().splitlines())
    require(values.get('populated') in ('0','1'),'cgroup population unknown')
    return values['populated']=='1'


def signature(value):
    return tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks'))


def read(root,path,reference):
    require(isinstance(reference,dict) and set(reference)=={'path','sha256'},'evidence reference schema differs')
    require(reference['path']==str(path.relative_to(root)) and path.resolve()==path,'fixed evidence path differs')
    require(isinstance(reference['sha256'],str) and re.fullmatch('[0-9a-f]{64}',reference['sha256']),'invalid evidence hash')
    before=path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_dev==root.stat().st_dev and before.st_size<=MAX_BYTES,'evidence metadata extent/type differs')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        require(signature(os.fstat(fd))==signature(before),'evidence changed before read')
        with os.fdopen(fd,'rb',closefd=False) as stream:raw=stream.read(MAX_BYTES+1)
        require(signature(os.fstat(fd))==signature(before) and signature(path.stat())==signature(before),'evidence changed during read')
    finally:os.close(fd)
    require(len(raw)<=MAX_BYTES and hashlib.sha256(raw).hexdigest()==reference['sha256'],'evidence bytes differ')
    return json.loads(raw),signature(before)


def verify(root,expected,proof):
    root=Path(root).absolute()
    require(root.is_dir() and root.resolve()==root,'existing nonsymlink root required')
    require(isinstance(expected,dict) and set(expected)=={'experiment','source_commit'},'exact predecessor identity required')
    name=expected['experiment'];source=expected['source_commit']
    require(isinstance(name,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,127}',name),'invalid experiment identity')
    require(isinstance(source,str) and re.fullmatch('[0-9a-f]{40}',source),'invalid predecessor source')
    run=root/'research_runs'/name;base=root/PREFIX/name
    paths={'claim':run/'claim.json','failed':run/'failed.json','owner':base/'owner.json',
           'launch':base/'launch.json','live':base/'guard/live.json','death':base/'guard/observer-death.json',
           'cells':base/'postmortem-cells.json','journals':base/'unsealed-journals.json','observer':base/'observer.json'}
    required=set(paths)
    require(isinstance(proof,dict) and required<=set(proof)<=required|{'final'},'exact required death evidence set differs')
    if 'final' in proof:paths['final']=base/'guard/final.json'
    def inventory():
        final=base/'guard/final.json';complete=run/'complete.json'
        require(not final.is_symlink() and final.exists()==('final' in proof),'terminal guard evidence omitted or invented')
        require(not complete.exists() and not complete.is_symlink(),'completed predecessor cannot authorize failed continuation')
    inventory()
    documents={};snapshots={}
    for key,path in paths.items():documents[key],snapshots[path]=read(root,path,proof[key])
    claim=documents['claim'];failed=documents['failed'];owner=documents['owner'];live=documents['live'];death=documents['death'];observer=documents['observer']
    require(claim.get('experiment_id')==name and claim.get('source')==source,'claim predecessor differs')
    require(failed.get('status')=='failed' and failed.get('experiment_id')==name and failed.get('claim_sha256')==proof['claim']['sha256'],'failed terminal claim join differs')
    require(set(owner)=={'experiment','source_commit','supervisor_pid','nonce','monitor_pid','monitor_start_ticks'} and owner['experiment']==name and owner['source_commit']==source,'guard owner differs')
    require(all(type(owner[k]) is int and owner[k]>0 for k in ('supervisor_pid','monitor_pid')),'owner PID type differs')
    require(isinstance(owner['monitor_start_ticks'],str) and owner['monitor_start_ticks'].isdecimal(),'owner start ticks differ')
    require(equal(documents['launch'],{k:v for k,v in owner.items() if k not in ('monitor_pid','monitor_start_ticks')}),'launch owner join differs')
    require(equal(live.get('owner_identity'),owner) and type(live.get('monitor_pid')) is int and live['monitor_pid']==owner['monitor_pid'],'live owner/monitor differs')
    expected_command=[str(root/'.venv/bin/python'),'-B','-m',MODULE,'--mode','worker','--root',str(root),'--registration',claim.get('registration'),'--experiment',name,'--source',source]
    require(isinstance(claim.get('registration'),str) and equal(live.get('command'),expected_command),'guard command differs from claim')
    require(death.get('phase')=='failed' and death.get('cleanup_verified') is True and death.get('live_sha256')==proof['live']['sha256'],'observer death certificate differs')
    joined=('owner_identity','monitor_pid','boot_id','cgroup','unit','command')
    require(all(k in live and k in death and equal(live[k],death[k]) for k in joined),'death/live ownership join differs')
    if 'final' in documents:
        require(all(k in documents['final'] and equal(documents['final'][k],live[k]) for k in joined),'final/live ownership join differs')
    require(observer.get('status')=='failed' and observer.get('cgroup_empty') is True
            and observer.get('owner_sha256')==proof['owner']['sha256']
            and observer.get('terminal_sha256')==proof['failed']['sha256']
            and observer.get('cell_ledger_sha256')==proof['cells']['sha256'],'observer terminal ownership join differs')
    evidence_keys=('launch','live','death','cells','journals')+(('final',) if 'final' in proof else ())
    require(equal(observer.get('evidence_sha256'),{str(paths[k].relative_to(base)):proof[k]['sha256'] for k in evidence_keys}),'observer evidence inventory differs')
    require(isinstance(documents['cells'],list) and isinstance(documents['journals'],list)
            and type(observer.get('unsealed_journals')) is int and observer['unsealed_journals']==len(documents['journals']),'observer journal count differs')
    group=Path(live['cgroup']);unit=live['unit']
    require(isinstance(unit,str) and re.fullmatch('onchain-replication-[A-Za-z0-9]+[.]service',unit)
            and group.is_absolute() and group.is_relative_to('/sys/fs/cgroup') and group.name==unit and group.resolve()==group,'cgroup ownership path differs')
    def dead():
        require(live['boot_id']==boot_id(),'cross-boot death requires separate review')
        require(not same_process_alive(owner['monitor_pid'],owner['monitor_start_ticks']),'predecessor monitor remains alive')
        # The historical supervisor has no saved start ticks: PID reuse is an
        # explicit conservative refusal, never permission to signal a process.
        require(not pid_exists(owner['supervisor_pid']),'supervisor/observer death not established')
        require(not group_populated(group),'owned cgroup remains populated')
    dead()
    for path,before in snapshots.items():require(path.resolve()==path and signature(path.stat())==before,'evidence changed after validation')
    dead()
    inventory()
    for path,before in snapshots.items():require(path.resolve()==path and signature(path.stat())==before,'evidence changed at final observation')
    return {'experiment':name,'source_commit':source,'claim_sha256':proof['claim']['sha256'],
            'observer_sha256':proof['observer']['sha256'],'checked_evidence_files':len(proof),
            'continuation_admitted':False,'outputs_verified':False,'arrays_read':False,
            'qualification':'Failed-owner death observation only; registered ancestry, workload and checkpoint admission remain required.'}
