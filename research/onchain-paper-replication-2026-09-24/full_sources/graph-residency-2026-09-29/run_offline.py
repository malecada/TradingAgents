"""Finite named engineering verification; no empirical research claim."""
import hashlib
import json
from pathlib import Path
import sys

from tradingagents.research.onchain_replication.resources import GIB, guarded_run

root=Path.cwd();here=Path(__file__).resolve().parent
bindings=json.loads((here/'source-bindings.json').read_bytes())
for path,expected in bindings['files'].items():
    if hashlib.sha256((root/path).read_bytes()).hexdigest()!=expected:
        raise ValueError('frozen source differs: '+path)
result=guarded_run([str(root/'.venv/bin/python'),'-B','scripts/verify_offline.py'],
    cwd=root,receipt_dir=here/'offline01',memory_max_bytes=3*GIB,
    memory_high_bytes=11*GIB//4,memory_swap_max_bytes=0,reserve_bytes=3*GIB,
    start_reserve_bytes=6*GIB,disk_paths=[root],disk_floor_bytes=20*GIB,
    wall_seconds=3600)
print(json.dumps({k:result.get(k) for k in ('phase','child_exit_code','cleanup_verified',
    'elapsed_seconds','peak_sampled_memory_current_bytes','limit_reason')}),flush=True)
sys.exit(0 if result['phase']=='complete' else 1)
