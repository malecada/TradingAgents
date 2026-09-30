"""One-shot bounded saved-array verification; not a research claim launcher."""
import json
from pathlib import Path
import sys

from tradingagents.research.onchain_replication.resources import GIB, guarded_run

root = Path.cwd()
here = Path(__file__).resolve().parent
result = guarded_run(
    [str(root/'.venv/bin/python'), '-B', str(here/'verify.py')],
    cwd=root, receipt_dir=here/'guard01', memory_max_bytes=3*GIB,
    memory_high_bytes=2*GIB, memory_swap_max_bytes=0, reserve_bytes=3*GIB,
    start_reserve_bytes=6*GIB, disk_paths=[root], disk_floor_bytes=10*GIB,
    wall_seconds=1800,
)
print(json.dumps({k: result.get(k) for k in (
    'phase','child_exit_code','cleanup_verified','elapsed_seconds',
    'peak_sampled_memory_current_bytes','memory_events','limit_reason')}), flush=True)
sys.exit(0 if result['phase'] == 'complete' else 1)
