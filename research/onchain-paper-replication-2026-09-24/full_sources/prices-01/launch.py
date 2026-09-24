"""External supervisor: a new guarded attempt followed by post-death reconciliation."""
from pathlib import Path
import importlib.util
import signal
import os
import uuid
import json
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication.provenance import durable_mkdir,sync_directory
import subprocess
import argparse
import sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def launch(asset):
    if asset not in ('BTC','ETH'):raise ValueError('unsupported asset')
    receipt=ROOT/('research_artifacts/onchain-paper-replication-2026-09-24/source-prices-01-'+asset.lower()+'-guard')
    ownership=receipt.parent/('source-prices-01-'+asset.lower()+'-supervisor')
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    durable_mkdir(ownership.parent);ownership.mkdir(exist_ok=False);sync_directory(ownership.parent)
    nonce=uuid.uuid4().hex
    _immutable(ownership/'owner.json',{'pid':os.getpid(),'nonce':nonce,'source':source,'asset':asset})
    if receipt.exists():raise FileExistsError('price identity already attempted; never relaunch')
    monitor=subprocess.Popen([sys.executable,'-B',str(HERE/'monitor.py'),'--source',source,'--asset',asset,'--owner-pid',str(os.getpid()),'--nonce',nonce],cwd=ROOT)
    def stop(signum,frame):
        if monitor.poll() is None:monitor.terminate()
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    code=monitor.wait()
    spec=importlib.util.spec_from_file_location('source_reconcile',HERE/'reconcile.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    identity=json.loads((ownership/'monitor.json').read_bytes())
    if identity['nonce']!=nonce:raise ValueError('monitor identity differs')
    result=module.reconcile(receipt,receipt.parent/'sources'/('paper-prices-'+asset.lower()+'-20260924'),source,identity,asset)
    print(result,flush=True)
    return 0 if code==0 and result['status']=='complete' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--asset',required=True,choices=('BTC','ETH'));args=parser.parse_args();raise SystemExit(launch(args.asset))
