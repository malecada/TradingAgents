"""Finite engineering temp-volume check; no empirical claim or input read."""
from pathlib import Path
import json
import sys
from tradingagents.research.onchain_replication.resources import guarded_run,GIB
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
script=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/graph-storage-probe-2026-09-29/check_temp_volume.py'
r=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(script)],cwd=ROOT,receipt_dir=HERE/'temp-check02',memory_max_bytes=GIB//4,memory_high_bytes=GIB//8,memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=4*GIB,disk_paths=[ROOT],disk_floor_bytes=10*GIB,wall_seconds=30)
print(json.dumps({k:r.get(k) for k in ('phase','child_exit_code','cleanup_verified','limit_reason')}))
sys.exit(0 if r['phase']=='complete' and r['child_exit_code']==0 and r['cleanup_verified'] else 1)
