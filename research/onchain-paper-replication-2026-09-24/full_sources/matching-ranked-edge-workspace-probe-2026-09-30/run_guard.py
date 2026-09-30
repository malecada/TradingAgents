"""One reviewed finite synthetic profile; preserve every exclusive identity."""
from pathlib import Path
import json
import sys
from tradingagents.research.onchain_replication.resources import guarded_run, GIB

root = Path.cwd()
here = Path(__file__).resolve().parent
r = guarded_run([str(root/'.venv/bin/python'), '-B', str(here/'probe.py')],
    cwd=root, receipt_dir=here/'guard01', memory_max_bytes=GIB,
    memory_high_bytes=3*GIB//4, memory_swap_max_bytes=0, reserve_bytes=3*GIB,
    start_reserve_bytes=4*GIB, disk_paths=[root], disk_floor_bytes=10*GIB,
    wall_seconds=1800)
print(json.dumps({k:r.get(k) for k in ('phase','elapsed_seconds',
    'peak_sampled_memory_current_bytes','memory_events','child_exit_code',
    'cleanup_verified','limit_reason')}), flush=True)
sys.exit(0 if r['phase']=='complete' and r['child_exit_code']==0
         and r['cleanup_verified'] else 1)
