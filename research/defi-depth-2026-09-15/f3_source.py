"""F3 exact indivisible acquisition/financial runner; committed admission required."""
import argparse
import importlib.util
import json
from pathlib import Path
from tradingagents.research import ResearchRun
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
EXPERIMENT='defi-depth-f3-20260915';REGISTRATION='research/defi-depth-2026-09-15/gates-f3.json'


def module(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


S=module('f3_exact_source_collector','protocol_financial_source.py')
R=module('f3_exact_financial_results','protocol_financial_results.py')
C=module('f3_exact_context','f3_context.py')
P=module('f3_parent_recovery_provenance','recovery_chain.py')


def manifests(design):
    source=S.request_inventory(design);cells,outputs=R.manifests('F3')
    return ['retained-history']+source['cells']+cells,['history.json']+source['outputs']+outputs


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);args=p.parse_args()
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        design=json.loads(run.read_input('design'));packet=json.loads(run.read_input('source_context'))
        parent={name:run.read_input(name) for name in P.INPUTS}
        recovery=P.verify(parent,ROOT)
        context=C.verify_packet(packet,design,parent['f1_claim'],parent['f1_terminal'])
        run.write_json('history.json',{'prior_request_keys':design['prior_request_keys'],
            'price_field_history':design['price_field_history'],'f1_audit':packet['f1_audit'],'f1_recovery_provenance':recovery,
            'scope':'No common observation retry or prior-result backfill; terminal-bound retained source bytes'})
        summary,cells=S.capture(design,context,run.write_json)
        cells+=R.financial(summary,json.loads(run.read_input('benchmarks')),'F3',run.write_json)
        cells.append({'id':'retained-history','status':'complete'});run.finish(cells)


if __name__=='__main__':main()
