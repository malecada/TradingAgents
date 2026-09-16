"""One resource-only successor; invoke the byte-identical original computation."""
import argparse
import importlib.util
from pathlib import Path
from tradingagents.research_amended import ResearchRun

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
EXPERIMENT='eth-temporal-motifs-8gib-20260916'
REGISTRATION='research/onchain-graph-2026-09-16/motifs8gib/gates.json'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True)
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('original_local_motif_computation',HERE.parent/'motifs/benchmark.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        run.finish(original.execute(run.read_input,run.write_json))


if __name__=='__main__':main()
