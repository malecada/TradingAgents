"""Single owned bounded artifact consistency check of the closed census."""
from pathlib import Path
import hashlib,json,subprocess,sys
from tradingagents.research.onchain_replication.resources import GIB,guarded_run
root=Path.cwd();here=Path(__file__).resolve().parent
binding=json.loads((here/'bindings.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==binding['head']
for name in ('verify_arrays.py',):
    path=here/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==binding['files'][str(path.relative_to(root))]
result=guarded_run([str(root/'.venv/bin/python'),'-B',str(here/'verify_arrays.py')],cwd=root,
    receipt_dir=here/'guard01',memory_max_bytes=GIB//2,memory_high_bytes=3*GIB//8,
    memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=7*GIB//2,
    disk_paths=[root],disk_floor_bytes=10*GIB,wall_seconds=180)
print(json.dumps({k:result.get(k) for k in ('phase','child_exit_code','cleanup_verified','elapsed_seconds','limit_reason','peak_sampled_memory_current_bytes')}),flush=True)
sys.exit(0 if result['phase']=='complete' and result['child_exit_code']==0 and result['cleanup_verified'] else 1)
