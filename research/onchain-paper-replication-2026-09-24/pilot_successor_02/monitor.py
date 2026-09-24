"""Guard process; external launch supervisor reconciles after this process ends."""
from pathlib import Path
import argparse
import ctypes
import os
import signal
import importlib.util
import sys
from tradingagents.research.onchain_replication.resources import guarded_run,bind_parent_death
from tradingagents.research.lifecycle import _immutable
import json
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--owner-pid',required=True,type=int);parser.add_argument('--nonce',required=True);args=parser.parse_args()
    bind_parent_death(args.owner_pid)
    ownership=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02-supervisor'
    prior=json.loads((ownership/'owner.json').read_bytes())
    if prior['nonce']!=args.nonce or prior['pid']!=args.owner_pid or prior['source']!=args.source:raise ValueError('supervisor identity differs')
    identity={'nonce':args.nonce,'supervisor_pid':args.owner_pid,'monitor_pid':os.getpid(),'monitor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}
    _immutable(ownership/'monitor.json',identity)
    receipt=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02-guard'
    command=[sys.executable,'-B',str(HERE/'run.py'),'--source',args.source,'--guard',str(receipt)]
    limits=json.loads((HERE/'resource-contract-v4.json').read_bytes())
    result=guarded_run(command,cwd=ROOT,receipt_dir=receipt,disk_paths=[ROOT,Path('/home/malecada/Data')],wall_seconds=28800,owner_identity=identity,
        memory_max_bytes=limits['memory_max_bytes'],memory_high_bytes=limits['memory_high_bytes'])
    signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
    spec=importlib.util.spec_from_file_location('pilot_reconcile',HERE/'reconcile.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    observed=module.reconcile(receipt,receipt.parent/'pilot-02',args.source,identity)
    print(result['phase'],result['limit_reason'],observed['status'],flush=True)
    raise SystemExit(0 if result['phase']=='complete' else 1)
