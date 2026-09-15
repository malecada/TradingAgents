"""One admitted local options evaluation after sealed source/quiescence review.

A failure after the exclusive analysis intent never authorizes a replay. This
entry point reads only the fixed normalized source binding, not live endpoints.
Use the frozen resource guard. Interrupted execution requires forensic closure.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tradingagents.research_options_timing import analysis,control,independent_verify


def run(*,root,binding,commit,quiescence_evidence,now_utc):
    root=Path(root).resolve()
    proof=independent_verify.verify(root=root,now_utc=now_utc,quiescence_evidence=quiescence_evidence)
    if proof['status']!='active' or proof['quiescence']!='externally-reviewed':raise ValueError('active externally reviewed quiescent episode required')
    episode=control.Episode.resume(root=root,now_utc=now_utc)
    if episode.claim['experiment']['outputs']!=['books.json','source-report.json'] or episode.claim['experiment']['cells']!=list(analysis.CELLS):raise ValueError('fixed eight-case output grammar')
    # This binds all source hashes before reserving the sole computation. No
    # normalized observations are parsed into prices/books before the intent.
    bound=episode._analysis_binding(binding,commit,now_utc)
    if set(bound['inputs'])!={'observations'}:raise ValueError('fixed normalized input binding required')
    path=control.local(root,bound['inputs']['observations']['path'])
    if path.stat().st_size>64*1024**2:raise ValueError('bounded normalized source input')
    episode.analysis_intent(binding=binding,commit=commit,now_utc=now_utc)
    product=json.loads(path.read_bytes())
    if set(product)!={'source_report','evaluate_kwargs','unavailable_cells'}:raise ValueError('frozen returned product schema')
    if product['evaluate_kwargs'] is None:
        cells=product['unavailable_cells']
        if {r['id'] for r in cells}!=set(analysis.CELLS) or len(cells)!=8 or any(r['status']!='unavailable' or not r.get('reason') for r in cells):raise ValueError('all unavailable cases retained')
        result={'cells':{r['id']:r for r in cells},'count':8,'strategy_validated':False,'inference':'Source unavailable; no economic rejection inferred.'}
    else:
        result=analysis.evaluate(**product['evaluate_kwargs'])
        cells=[{k:r[k] for k in ('id','status','reason') if k in r} for r in result['cells'].values()]
    clock=lambda:datetime.now(timezone.utc).isoformat()
    episode.write_output('books.json',control.encoded(result),now_utc=clock())
    episode.write_output('source-report.json',control.encoded(product['source_report']),now_utc=clock())
    terminal=episode.finish(status='complete',cells=cells,reason='One frozen conditional development episode; completion is not strategy validation.',now_utc=clock())
    verified=independent_verify.verify(root=root,now_utc=clock(),quiescence_evidence=quiescence_evidence)
    return {'terminal':terminal,'independent_protocol':verified,'scientific_validation':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding-path',required=True);parser.add_argument('--binding-sha256',required=True)
    parser.add_argument('--binding-commit',required=True);parser.add_argument('--quiescence-path',required=True)
    parser.add_argument('--quiescence-sha256',required=True);parser.add_argument('--quiescence-commit',required=True)
    args=parser.parse_args()
    print(json.dumps(run(root=ROOT,binding={'path':args.binding_path,'sha256':args.binding_sha256},commit=args.binding_commit,
        quiescence_evidence={'path':args.quiescence_path,'sha256':args.quiescence_sha256,'commit':args.quiescence_commit},now_utc=datetime.now(timezone.utc).isoformat()),indent=2))


if __name__=='__main__':main()
