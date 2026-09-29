"""Finite successor verification under the user-authorized 10 GiB disk reserve."""
import hashlib
import json
from pathlib import Path
import sys

from tradingagents.research.onchain_replication.resources import GIB, guarded_run

root=Path.cwd();here=Path(__file__).resolve().parent
bindings=json.loads((here/'offline02-bindings.json').read_bytes())
for path,expected in bindings['files'].items():
    if hashlib.sha256((root/path).read_bytes()).hexdigest()!=expected:
        raise ValueError('frozen source/input differs: '+path)
prior=json.loads((here/'offline01/final.json').read_bytes())
if prior['phase']!='failed' or prior['cleanup_verified'] is not True or Path(prior['cgroup']).exists():
    raise ValueError('prior owner is not closed')
policy=json.loads((root/bindings['disk_policy']).read_bytes())
if policy['schema_version']!=1 or policy['disk_floor_bytes']!=10*GIB:
    raise ValueError('unexpected disk reserve policy')
result=guarded_run([str(root/'.venv/bin/python'),'-B','scripts/verify_offline.py'],
    cwd=root,receipt_dir=here/'offline02',memory_max_bytes=3*GIB,
    memory_high_bytes=11*GIB//4,memory_swap_max_bytes=0,reserve_bytes=3*GIB,
    start_reserve_bytes=6*GIB,disk_paths=[root],disk_floor_bytes=policy['disk_floor_bytes'],
    wall_seconds=3600)
print(json.dumps({k:result.get(k) for k in ('phase','child_exit_code','cleanup_verified',
    'elapsed_seconds','peak_sampled_memory_current_bytes','limit_reason')}),flush=True)
sys.exit(0 if result['phase']=='complete' and result['child_exit_code']==0 and result['cleanup_verified'] else 1)
