"""Named synthetic offline suite under the same verified local process limits."""
from pathlib import Path
import sys
import argparse
from tradingagents.research.onchain_replication.resources import guarded_run
ROOT=Path(__file__).resolve().parents[4]
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--receipt-id',required=True);args=parser.parse_args()
    if not args.receipt_id.startswith('offline-postchange-') or '/' in args.receipt_id:raise ValueError('invalid verification receipt identity')
    result=guarded_run([sys.executable,'-B',str(ROOT/'scripts/verify_offline.py')],cwd=ROOT,receipt_dir=ROOT/'research/onchain-paper-replication-2026-09-24/resources'/args.receipt_id,disk_paths=[ROOT],wall_seconds=3600)
    print(result['phase'],result['limit_reason'],flush=True)
    raise SystemExit(0 if result['phase']=='complete' else 1)
