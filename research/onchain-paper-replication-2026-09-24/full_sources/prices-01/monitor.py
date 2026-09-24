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
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--asset',required=True,choices=('BTC','ETH'));parser.add_argument('--owner-pid',required=True,type=int);parser.add_argument('--nonce',required=True);args=parser.parse_args();asset=args.asset
    receipt=ROOT/('research_artifacts/onchain-paper-replication-2026-09-24/source-prices-01-'+asset.lower()+'-guard')
    ownership=receipt.parent/('source-prices-01-'+asset.lower()+'-supervisor')
    bind_parent_death(args.owner_pid)
    prior=json.loads((ownership/'owner.json').read_bytes())
    if prior['nonce']!=args.nonce or prior['pid']!=args.owner_pid or prior['source']!=args.source or prior['asset']!=asset:raise ValueError('supervisor identity differs')
    identity={'nonce':args.nonce,'asset':asset,'supervisor_pid':args.owner_pid,'monitor_pid':os.getpid(),'monitor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}
    _immutable(ownership/'monitor.json',identity)
    command=[sys.executable,'-B',str(HERE/'worker.py'),'--source',args.source,'--asset',asset]
    result=guarded_run(command,cwd=ROOT,receipt_dir=receipt,disk_paths=[ROOT],wall_seconds=300,memory_max_bytes=512*1024**2,memory_high_bytes=384*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*1024**3,owner_identity=identity)
    signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
    spec=importlib.util.spec_from_file_location('source_reconcile',HERE/'reconcile.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    observed=module.reconcile(receipt,receipt.parent/'sources'/('paper-prices-'+asset.lower()+'-20260924'),args.source,identity,asset)
    print(result['phase'],result['limit_reason'],observed['status'],flush=True)
    raise SystemExit(0 if result['phase']=='complete' else 1)
