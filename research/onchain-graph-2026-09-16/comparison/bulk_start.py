"""Start the user-authorized finite download once; no scheduler or restart."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from tradingagents.research import admit


def publish(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    admit(root=root, registration='research/onchain-graph-2026-09-16/comparison/bulk-gates.json',
          experiment='eth-remaining-graph-capture-20260916', source=args.source)
    if (root/'research_runs/eth-remaining-graph-capture-20260916').exists():
        raise FileExistsError('claimed identity cannot be restarted')
    command = [sys.executable, '-B', str(here/'bulk_launch.py'), '--source', args.source]
    publish(here/'bulk-launch-intent.json', dict(source=args.source, command=command,
        root=str(root), requested_at=datetime.now(timezone.utc).isoformat(), automatic_restart=False))
    environment = dict(os.environ, PYTHONPATH=str(root), OPENBLAS_NUM_THREADS='2',
                       OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')
    with (here/'bulk-progress.log').open('x') as output:
        process = subprocess.Popen(command, cwd=root, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        ticks = int(Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19])
    except FileNotFoundError:
        ticks = None
    receipt = dict(source=args.source, pid=process.pid, process_start_ticks=ticks,
                   command=command, root=str(root), started_at=datetime.now(timezone.utc).isoformat(),
                   automatic_restart=False, qualification='Launch receipt; inspect claim, dated outputs and terminal/resource receipts for actual progress.')
    publish(here/'bulk-started.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
