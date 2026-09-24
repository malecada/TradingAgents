"""Finite tiny containment probe, no scientific claim or empirical inputs."""
from pathlib import Path
import sys
from tradingagents.research.onchain_replication.resources import guarded_run
root=Path(__file__).resolve().parents[5]
result=guarded_run([sys.executable,'-B',str(Path(__file__).with_name('liveness_worker.py')),sys.argv[2]],cwd=root,receipt_dir=Path(sys.argv[1]),disk_paths=[root,Path('/home/malecada/Data')],wait_seconds=0,lease_seconds=5,wall_seconds=40)
raise SystemExit(0 if result['phase']=='complete' else 1)
