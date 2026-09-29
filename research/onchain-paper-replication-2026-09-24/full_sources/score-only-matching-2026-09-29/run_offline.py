"""Finite named verification of the optional matching consumer and guard edit."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tradingagents.research.onchain_replication.resources import GIB,guarded_run

ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
bindings=json.loads((HERE/'source-bindings.json').read_text())
if subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=bindings['head']:
    raise ValueError('frozen HEAD changed')
for name,expected in bindings['files'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
        raise ValueError('frozen source changed: '+name)
policy=json.loads((ROOT/bindings['disk_policy']).read_text())
if policy['schema_version']!=1 or policy['disk_floor_bytes']!=10*GIB:
    raise ValueError('disk policy differs')
result=guarded_run([str(ROOT/'.venv/bin/python'),'-B','scripts/verify_offline.py'],
    cwd=ROOT,receipt_dir=HERE/'offline01',memory_max_bytes=3*GIB,
    memory_high_bytes=11*GIB//4,memory_swap_max_bytes=0,reserve_bytes=3*GIB,
    start_reserve_bytes=6*GIB,disk_paths=[ROOT],disk_floor_bytes=policy['disk_floor_bytes'],wall_seconds=3600)
print(json.dumps({k:result.get(k) for k in ('phase','child_exit_code','cleanup_verified',
    'elapsed_seconds','peak_sampled_memory_current_bytes','limit_reason')}),flush=True)
sys.exit(0 if result['phase']=='complete' and result['child_exit_code']==0 and result['cleanup_verified'] else 1)
