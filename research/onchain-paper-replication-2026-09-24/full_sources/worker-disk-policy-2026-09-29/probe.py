"""Tiny real guard/worker admission check; no data, network or large allocation."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tradingagents.research.onchain_replication.resources import GIB,guarded_run,assert_guarded_worker

for name,expected in json.loads((HERE/'bindings.json').read_text()).items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
        raise ValueError('probe bound source changed')
if sys.argv[1:]==['--worker']:
    state=assert_guarded_worker(HERE/'probe01',sys.orig_argv,required_paths=[ROOT],
        wall_seconds=60,memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,
        disk_floor_bytes=10*GIB)
    if state['disk_floor_bytes']!=10*GIB:raise ValueError('unexpected live floor')
    print(json.dumps({'worker_admitted':True,'disk_floor_bytes':state['disk_floor_bytes'],
                      'reserve_bytes':state['reserve_bytes']}),flush=True)
elif sys.argv[1:]:raise ValueError('unexpected arguments')
else:
    result=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--worker'],
        cwd=ROOT,receipt_dir=HERE/'probe01',memory_max_bytes=256*1024**2,
        memory_high_bytes=192*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*GIB,
        start_reserve_bytes=int(3.5*GIB),disk_paths=[ROOT],disk_floor_bytes=10*GIB,wall_seconds=60)
    print(json.dumps({k:result.get(k) for k in ('phase','child_exit_code','cleanup_verified','limit_reason')}),flush=True)
    sys.exit(0 if result['phase']=='complete' and result['child_exit_code']==0 and result['cleanup_verified'] else 1)
