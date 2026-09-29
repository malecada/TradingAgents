"""One finite synthetic-only scale check under memory/disk/wall containment."""
from pathlib import Path
import json
import hashlib
import subprocess
import sys
from tradingagents.research.onchain_replication.resources import GIB,guarded_run

ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
bindings=json.loads((HERE/'scale-bindings.json').read_text())
if subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=bindings['head']:raise ValueError('HEAD changed')
for name,want in bindings['files'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=want:raise ValueError('source changed: '+name)
result=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(HERE/'synthetic_scale.py')],cwd=ROOT,
    receipt_dir=HERE/'scale_guard01',memory_max_bytes=GIB,memory_high_bytes=3*GIB//4,
    memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=4*GIB,
    disk_paths=[ROOT],disk_floor_bytes=10*GIB,wall_seconds=180)
print(json.dumps({k:result.get(k) for k in ('phase','child_exit_code','cleanup_verified','elapsed_seconds','limit_reason','peak_sampled_memory_current_bytes')}),flush=True)
sys.exit(0 if result['phase']=='complete' and result['child_exit_code']==0 and result['cleanup_verified'] else 1)
