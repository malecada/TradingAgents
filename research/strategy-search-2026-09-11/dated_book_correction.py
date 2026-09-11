"""Resource-only correction of preserved failed dated episode; unchanged economics."""
import argparse
import json
from pathlib import Path
import resource
import signal

# Preload real statistical dependencies before claiming/opening research inputs.
import dated_statistics
from dated_book_run import evaluate
from tradingagents.research import ResearchRun


def terminated(signum, frame):
    raise RuntimeError('external resource guard terminated the corrected run')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, terminated)
    with ResearchRun.start(root=Path(__file__).resolve().parents[2],
            registration='research/strategy-search-2026-09-11/gates-dated-correction.json',
            experiment='dated-book-resource-correction-20260911', source=args.source) as run:
        inputs = [json.loads(run.read_input(name)) for name in ('capture','admission','spot_capture','spot_admission')]
        books, summary, cells = evaluate(*inputs)
        run.write_json('books.json', books)
        run.write_json('summary.json', summary)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if peak > 512*1024:
            raise RuntimeError('financial process historical RSS peak exceeds 512 MiB')
        run.write_json('resource.json', {'linux_self_ru_maxrss_kib': peak, 'memory_limit_mib': 512,
            'scope':'Linux resident memory; parent separately records sampled aggregate process-tree RSS. No virtual-address cap.'})
        run.finish(cells)


if __name__ == '__main__':
    main()
