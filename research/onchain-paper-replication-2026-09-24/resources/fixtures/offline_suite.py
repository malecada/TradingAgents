"""Named synthetic offline suite under the same verified local process limits."""
from pathlib import Path
import sys
from tradingagents.research.onchain_replication.resources import guarded_run
ROOT=Path(__file__).resolve().parents[4]
if __name__=='__main__':
    result=guarded_run([sys.executable,'-B',str(ROOT/'scripts/verify_offline.py')],cwd=ROOT,receipt_dir=ROOT/'research/onchain-paper-replication-2026-09-24/resources/offline-postchange-01',disk_paths=[ROOT],wall_seconds=3600)
    print(result['phase'],result['limit_reason'],flush=True)
    raise SystemExit(0 if result['phase']=='complete' else 1)
