"""One finite named offline verification of the scoped synthetic disk fixtures and maintained matching ownership."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tradingagents.research.onchain_replication.resources import GIB, guarded_run
from tradingagents.research.onchain_replication.job import required_sources
from scripts.verify_offline import offline_paths

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True)
args = parser.parse_args()
if re.fullmatch('[0-9a-f]{40}', args.source) is None:
    raise ValueError('full committed source required')
if subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() != args.source:
    raise ValueError('frozen HEAD changed')
raw = (HERE/'source-bindings.json').read_bytes()
manifest_name = str((HERE/'source-bindings.json').relative_to(ROOT))
if subprocess.check_output(['git', 'show', args.source+':'+manifest_name]) != raw:
    raise ValueError('binding manifest differs from committed source')
bindings = json.loads(raw)
if sorted(required_sources()) != bindings['required_package_sources']:
    raise ValueError('dynamic package source inventory changed')
if sorted(offline_paths(ROOT)) != bindings['offline_test_inventory']:
    raise ValueError('named offline test inventory changed')
tracked = [name for name in subprocess.check_output(['git', 'ls-files', '--',
    'tradingagents', 'tests', 'scripts', 'research', 'docs', 'conftest.py'], text=True).splitlines()
    if name.endswith('.py') and not {'keys', 'apis', '.venv', 'node_modules', '.git'}.intersection(Path(name).parts)]
if sorted(tracked) != bindings['tracked_python_inventory']:
    raise ValueError('tracked Python source inventory changed')
for name, expected in bindings['files'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
        raise ValueError('frozen current source changed: '+name)
    committed = subprocess.check_output(['git', 'show', args.source+':'+name])
    if hashlib.sha256(committed).hexdigest() != expected:
        raise ValueError('frozen committed source changed: '+name)
policy = json.loads((ROOT/bindings['disk_policy']).read_bytes())
if policy['schema_version'] != 1 or policy['disk_floor_bytes'] != 10*GIB:
    raise ValueError('disk policy differs')
units = subprocess.check_output(['systemctl', '--user', 'list-units',
    '--state=active,activating', '--no-legend', 'onchain-replication-*.service'], text=True)
if units.strip():
    raise ValueError('another replication guard is active')
result = guarded_run([str(ROOT/'.venv/bin/python'), '-B', 'scripts/verify_offline.py'],
    cwd=ROOT, receipt_dir=HERE/'offline01', memory_max_bytes=3*GIB,
    memory_high_bytes=11*GIB//4, memory_swap_max_bytes=0, reserve_bytes=3*GIB,
    start_reserve_bytes=6*GIB, disk_paths=[ROOT], disk_floor_bytes=policy['disk_floor_bytes'],
    wall_seconds=3600, owner_identity={'kind': 'synthetic-disk-fixture-correction-offline01',
    'source_commit': args.source, 'bindings_sha256': hashlib.sha256(raw).hexdigest()})
print(json.dumps({k: result.get(k) for k in ('phase', 'child_exit_code', 'cleanup_verified',
    'elapsed_seconds', 'peak_sampled_memory_current_bytes', 'limit_reason')}), flush=True)
sys.exit(0 if result['phase'] == 'complete' and result['child_exit_code'] == 0
         and result['cleanup_verified'] else 1)
