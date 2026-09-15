"""F1 exact indivisible acquisition/financial runner; requires committed admission."""
import argparse
import importlib.util
import json
from pathlib import Path
from tradingagents.research import ResearchRun
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
EXPERIMENT='defi-depth-f1-20260915';REGISTRATION='research/defi-depth-2026-09-15/gates-f1.json'

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

S=module('f1_exact_source_collector','protocol_financial_source.py')
R=module('f1_exact_financial_results','protocol_financial_results.py')
C=module('f1_exact_retained_context','f1_context.py')


def manifests(design):
    source=S.request_inventory(design)
    cells,outputs=R.manifests('F1')
    return ['retained-history']+source['cells']+cells,['history.json']+source['outputs']+outputs


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        design=json.loads(run.read_input('design'));packet=json.loads(run.read_input('source_context'))
        C.verify_registered_evidence(packet,run.read_input)
        context=C.verify_packet(packet,design)
        if packet['inherited_endpoint_stop']:raise ValueError('inherited endpoint stop precludes new source acquisition')
        run.write_json('history.json',{'prior_request_keys':packet['prior_request_keys'],
                      'price_field_history':design['price_field_history'],'f2_audit':packet['f2_audit'],
                      'first_owner_scope':'Terminal-audited suppressed keys only; prior failures and F2 results unchanged'})
        summary,cells=S.capture(design,context,run.write_json)
        benchmarks=json.loads(run.read_input('benchmarks'))
        cells+=R.financial(summary,benchmarks,'F1',run.write_json)
        cells.append({'id':'retained-history','status':'complete'})
        run.finish(cells)


if __name__=='__main__':main()
