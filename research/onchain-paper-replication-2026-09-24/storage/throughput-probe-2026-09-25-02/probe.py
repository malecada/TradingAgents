"""One-shot, bounded random-payload transport comparison; no research data."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication.resources import guarded_run,assert_guarded_worker
from tradingagents.research.onchain_replication.preservation import sha256

MIB=1024**2
GIB=1024**3


def stages():
    return [('single_before',1),('parallel',2),('single_after',1)]


def budget(size):
    if type(size) is not int or not 0<size<=128*MIB:raise ValueError('payload outside bound')
    return sum(n*(size+(size//32768+1)*32768) for _,n in stages())


def load():
    raw=(HERE/'contract.json').read_bytes();c=json.loads(raw)
    for name,wanted in c['source_sha256'].items():
        if sha256(ROOT/name)!=wanted:raise ValueError('bound source changed: '+name)
    if sha256(HERE/'CHARTER.md')!=c['charter_sha256']:raise ValueError('charter changed')
    if budget(c['payload_bytes'])>c['maximum_network_payload_bytes']:raise ValueError('network budget')
    return c,hashlib.sha256(raw).hexdigest()


def parent_transport():
    path=HERE.parent/'raw-preservation-2026-09-25-03/transfer.py'
    spec=importlib.util.spec_from_file_location('frozen_backup03',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    _,_,connection=m.load_contract()
    class Transport(m.Transport):
        def __init__(self,*args):
            super().__init__(*args)
            independent=['-o','ControlMaster=no','-o','ControlPath=none','-o','Compression=no']
            self.ssh[-1:-1]=independent
            self.scp.extend(independent)
        def run(self,args):
            return subprocess.run(args,check=True,capture_output=True,timeout=180)
    return Transport,connection


def backup_snapshot():
    snapshots=[]
    parent=HERE.parent/'raw-preservation-2026-09-25-03'
    for p in sorted(parent.glob('bulk[0-9][0-9]/guard/live.json')):
        if (p.parent/'final.json').exists():continue
        x=json.loads(p.read_text());processes=[]
        cg=Path(x['cgroup'])/'cgroup.procs'
        if cg.exists():
            for pid in cg.read_text().split():
                try:processes.append((Path('/proc')/pid/'comm').read_text().strip())
                except (FileNotFoundError,ProcessLookupError):pass
        snapshots.append({'phase':p.parent.parent.name,'guard_phase':x['phase'],
            'host_mem_available_bytes':x['host_mem_available_bytes'],'process_types':processes})
    return snapshots


def worker():
    c,ch=load();work=HERE/'run'
    assert_guarded_worker(work/'guard',sys.orig_argv,required_paths=[ROOT],wall_seconds=900,
                          memory_max_bytes=512*MIB,memory_high_bytes=384*MIB)
    _immutable(work/'intent.json',{'contract_sha256':ch,'random_payload_only':True})
    Transport,connection=parent_transport();sources=[];hashes=[]
    try:
        for i in range(2):
            p=work/f'payload-{i}.bin'
            with p.open('xb') as f:
                remaining=c['payload_bytes']
                while remaining:
                    block=os.urandom(min(MIB,remaining));f.write(block);remaining-=len(block)
                f.flush();os.fsync(f.fileno())
            sources.append(p);hashes.append(sha256(p))
        control=Transport(connection,c['scp_kbit_per_second'],0)
        control.mkdir(c['remote_directory'])
        results=[];remote_files=[]
        for name,n in stages():
            transports=[Transport(connection,c['scp_kbit_per_second'],384*MIB) for _ in range(n)]
            remotes=[c['remote_directory']+'/'+name+f'-{i}.bin' for i in range(n)]
            downloads=[work/(name+f'-{i}.download') for i in range(n)]
            def timed_upload(i):
                began=time.monotonic();transports[i].put(sources[i],remotes[i]);return time.monotonic()-began
            def timed_download(i):
                began=time.monotonic();transports[i].get(remotes[i],downloads[i]);return time.monotonic()-began
            background_before=backup_snapshot()
            with ThreadPoolExecutor(max_workers=n) as pool:
                began=time.monotonic();up=list(pool.map(timed_upload,range(n)));upload=time.monotonic()-began
                background_between=backup_snapshot()
                began=time.monotonic();down=list(pool.map(timed_download,range(n)));download=time.monotonic()-began
            background_after=backup_snapshot()
            observed=[sha256(p) for p in downloads]
            if observed!=hashes[:n]:raise ValueError('download hash differs')
            result={'stage':name,'connections':n,'bytes_each':c['payload_bytes'],
                    'upload_seconds':upload,'download_seconds':download,
                    'upload_aggregate_MiB_s':n*c['payload_bytes']/MIB/upload,
                    'download_aggregate_MiB_s':n*c['payload_bytes']/MIB/download,
                    'individual_upload_seconds':up,'individual_download_seconds':down,
                    'verified_sha256':observed,'remote_paths':remotes,
                    'background_backup_snapshots':[background_before,background_between,background_after]}
            _immutable(work/(name+'.json'),result);results.append(result);remote_files.extend(remotes)
            print(json.dumps(result),flush=True)
            for p in downloads:p.unlink()
        _immutable(work/'complete.json',{'status':'complete','contract_sha256':ch,'stages':results,
             'qualification':'Backup remains active; shared-link traffic/cache/time effects confound absolute isolated throughput.'})
        cleanup={}
        for remote in remote_files:
            try:control.run([*control.ssh,'rm',control.remote_path(remote)]);cleanup[remote]='removed verified generated probe payload'
            except subprocess.SubprocessError as error:cleanup[remote]=type(error).__name__
        for p in sources:p.unlink()
        _immutable(work/'cleanup.json',cleanup)
    except BaseException as error:
        _immutable(work/'failed.json',{'status':'failed','error_type':type(error).__name__,'reason':str(error),
                                     'partial_outputs_preserved':True,'retry':False})
        raise


if __name__=='__main__':
    if sys.argv[1:]==['--worker']:worker()
    elif sys.argv[1:]==['run']:
        c,ch=load();work=HERE/'run';work.mkdir(exist_ok=False)
        release=json.loads((HERE/'RELEASE.json').read_text())
        if release['status']!='released' or release['contract_sha256']!=ch:raise ValueError('release mismatch')
        outcome=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--worker'],
            cwd=ROOT,receipt_dir=work/'guard',memory_max_bytes=512*MIB,memory_high_bytes=384*MIB,
            memory_swap_max_bytes=0,reserve_bytes=4*GIB,start_reserve_bytes=int(4.5*GIB),
            disk_paths=[ROOT],disk_floor_bytes=20*GIB,wall_seconds=900)
        print(json.dumps({k:outcome.get(k) for k in ('phase','child_exit_code','cleanup_verified','elapsed_seconds','limit_reason')}),flush=True)
        raise SystemExit(0 if outcome['phase']=='complete' and outcome['child_exit_code']==0 and outcome['cleanup_verified'] else 1)
    else:raise ValueError('choose run; no retries')
