"""Start the user-authorized finite download once; no scheduler or restart."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

from resume2_admission import admit_resume2


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
    # DNS-only health check before any new run claim or launch receipt.
    socket.getaddrinfo('aws-public-blockchain.s3.us-east-2.amazonaws.com', 443, type=socket.SOCK_STREAM)
    admit_resume2(root, args.source)
    if (root/'research_runs/eth-graph-source-resume2-20260918').exists():
        raise FileExistsError('claimed identity cannot be restarted')
    command = [sys.executable, '-B', str(here/'resume2_launch.py'), '--source', args.source]
    publish(here/'resume2-launch-intent.json', dict(source=args.source, command=command,
        root=str(root), requested_at=datetime.now(timezone.utc).isoformat(), automatic_restart=False))
    environment = dict(os.environ, PYTHONPATH=str(root), OPENBLAS_NUM_THREADS='2',
                       OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')
    with (here/'resume2-progress.log').open('x') as output:
        process = subprocess.Popen(command, cwd=root, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        ticks = int(Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19])
    except FileNotFoundError:
        ticks = None
    receipt = dict(source=args.source, pid=process.pid, process_start_ticks=ticks, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                   command=command, root=str(root), started_at=datetime.now(timezone.utc).isoformat(),
                   automatic_restart=False, qualification='Launch receipt; inspect claim, dated outputs and terminal/resource receipts for actual progress.')
    publish(here/'resume2-started.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
