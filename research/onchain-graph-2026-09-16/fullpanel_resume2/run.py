"""Successor namespace around the frozen first-continuation execution pipeline."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from tradingagents.research import ResearchRun

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE='research/onchain-graph-2026-09-16/fullpanel_resume2/'
EXPERIMENT='eth-full-history-feature-panel-resume2-20260922'
FROZEN_SOURCE='c739b6f0958e23b90ff5038dd46c9356581369c3'
FROZEN_FILES={
    'fullpanel_resume/run.py':'f5de48020b1c3e098ebee5affdfaa48636ecbcf48fc00ca9718149b51f2d292e',
    'fullpanel_resume/hash_union.py':'84b8bc65b2f9af2f14642efa5ae917c78d50df54baa76025076608865f356f28',
    'fullpanel/hash_audit.py':'ab66bf548c449ef55e41430b61709df73580d016636980a6ee00ce345944e5c1',
    'comparison/hash_audit.py':'e4c4c83c279dd3cfbd54be4c544ab7a773a8c946acf8716e257952afdd9447a2',
}


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def verify_frozen(directory):
    """Source-code bindings only; no retained source or hash payload reads."""
    for relative,digest in FROZEN_FILES.items():
        path=directory/relative
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('frozen continuation source differs: '+relative)


verify_frozen(HERE.parent)
pipeline=load('resume2_frozen_execution',HERE.parent/'fullpanel_resume/run.py')
# Only namespace ownership changes. Original daily and hash algorithms remain.
pipeline.EXPERIMENT=EXPERIMENT
pipeline.RESUME_BASE=BASE
execute=pipeline.execute


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    verify_frozen(HERE.parent)
    admission=load('resume2_runner_admission',HERE/'admission.py')
    if admission.EXPERIMENT!=EXPERIMENT:raise ValueError('successor identity differs')
    admission.admit_resume(ROOT,args.source)
    guard=load('resume2_runner_memory_guard',HERE/'memory_guard.py')
    guard.assert_guarded_worker(ROOT,args.source)
    def offline(event,args):
        if event.startswith(('socket.','http.client.','urllib.')):
            raise RuntimeError('offline successor network prohibited')
    sys.addaudithook(offline)
    with ResearchRun.start(root=ROOT,registration=BASE+'gates.json',experiment=EXPERIMENT,source=args.source) as run:
        run.finish(execute(ROOT,json.loads(run.read_input('plan')),run))


if __name__=='__main__':main()
