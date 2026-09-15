"""Seven actual historical double checks and invented full-book output workload.

Modular evidence only: no actual successor grant/claim/certificate is produced.
The final committed successor's own admission bindings remain separate checks.
"""
from datetime import datetime,timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tradingagents.research_options_timing import closed_history,control,analysis
from scripts.check_options_return_integration_20260915 import known


def preserve_new_source(proof, source):
    # Exact source-preservation work retained in the successor admission loops;
    # the parent registration already contains all20 retained contracts. This
    # is engineering provenance, not a fabricated successor grant or parent.
    parent=proof['verified_claims']['options-episode-20260911']
    spec=json.loads(control._blob(ROOT,source,parent['registration']))
    for name,old in proof['verified_claims'].items():
        oldspec=json.loads(control._blob(ROOT,old['source'],old['registration']))
        for group in ('experiments','families','datasets'):
            if any(spec[group].get(k)!=v for k,v in oldspec[group].items()):raise ValueError('historical gate object changed')
        baseline=control._blob(ROOT,'46edb5d39512b502e9824f9a4193ea4338b15cf5',old['registration'])
        if (ROOT/old['registration']).read_bytes()!=baseline or control._blob(ROOT,source,old['registration'])!=baseline:raise ValueError('physical old registration changed')
        pins=dict(old['experiment']['source_files'])
        for key in ('charter','selection'):
            if old['experiment'].get(key):pins[old['experiment'][key]['path']]=old['experiment'][key]['sha256']
        for path,digest in pins.items():control.reference(ROOT,{'path':path,'sha256':digest},source)
    runtime=control.runtime_hashes()
    for path,digest in runtime.items():
        # Read both execution and design identities separately, conservatively,
        # even when they refer to this same engineering commit.
        for _ in range(2):control.reference(ROOT,{'path':'tradingagents/'+path,'sha256':digest},source)
    for old in proof['verified_claims'].values():
        package='research_spread' if 'budget_book_grant' in old['experiment'] else 'research_extended' if 'budget_extension' in old['experiment'] else 'research_amended' if 'budget_amendment' in old['experiment'] else 'research'
        for name,digest in old['experiment']['runtime_hashes'].items():
            if '/' in name:
                prefix,filename=name.split('/',1);name={'original':'research','amended':'research_amended','extended':'research_extended'}.get(prefix,prefix)+'/'+filename
            else:name=package+'/'+name
            if runtime.get(name)!=digest:raise ValueError('frozen ancestor runtime changed')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    name='options-timing-history-output-envelope-20260915-v2'
    result_path=ROOT/'research/strategy-search-2026-09-11/reviews'/f'{name}.json'
    progress=result_path.with_suffix('.progress.jsonl')
    if result_path.exists() or progress.exists():raise SystemExit('retained attempt exists')
    baseline=json.loads((ROOT/'research/strategy-search-2026-09-11/reviews/options-timing-history-preflight-20260915.json').read_bytes())['before']
    closure=json.loads((ROOT/'research/strategy-search-2026-09-11/reviews/options-actual-failure-close-20260915.json').read_bytes())
    begin=time.monotonic();scratch=Path(tempfile.mkdtemp(prefix='options-timing-envelope-'))
    report={'kind':'actual-doubled-history-plus-invented-analysis-output','scratch':str(scratch),'history_count':20,'literal_analyzer_reconstruction_count':7,'pairs':[],'pass':False,
            'scope':'Seven actual certificate-bound closed-parent reconstructions, all20 new-source/gate preservation loops and six-package execution/design pin checks; one invented1057-hour8-case financial workload and exclusive outputs. No historical financial values parsed.',
            'limitations':['Modular workload; no new actual grant, certificate or claim created.','Successor target-only grant/future-window/control metadata checks remain separate synthetic tests; this workload includes actual full20history and successor-style new-source preservation plus6-package sourcepins.','Full source return normalization is a separate pre-analysis stage.'],
            'engineering_source':args.source,'runtime_before':control.runtime_hashes()}
    with progress.open('x') as log:
        def record(v):log.write(json.dumps(v,sort_keys=True)+'\n');log.flush()
        record({'event':'start','scratch':str(scratch)})
        try:
            for i in range(7):
                at=time.monotonic();clock=datetime.now(timezone.utc).isoformat()
                proof=closed_history.verify_parent(root=ROOT,certificate={'path':'research/strategy-search-2026-09-11/options-closed-parent-20260915.json','sha256':'b448ab270473b75e52cb53ef40e17bab49bbe52b4e3fe18393cf3d515076d5f3'},source=args.source,design_source=args.source,now_utc=clock)
                midway=time.monotonic();preserve_new_source(proof,args.source);observed=proof['verified_inventory']
                if observed!=baseline or proof['status']!='failed':raise ValueError('retained20 protocol/inventory differs')
                pair={'index':i+1,'closed_parent_seconds':midway-at,'new_source_preservation_seconds':time.monotonic()-midway,'seconds':time.monotonic()-at,'inventory_sha256':hashlib.sha256(control.canonical(observed)).hexdigest()}
                report['pairs'].append(pair);record(pair)
                if i==0:
                    estimate=7*pair['seconds']+5
                    record({'event':'first_pair_projection','projected_seconds_with_five_second_synthetic_allowance':estimate,'not_a_success':True})
                if i==2:
                    started=time.monotonic();inputs=known()
                    # Exercise representative normalized serialization/parsing as
                    # the real CLI does, using only the invented fixture.
                    product=control.encoded({'source_report':{'synthetic_only':True},'evaluate_kwargs':inputs,'unavailable_cells':[]})
                    output=analysis.evaluate(**json.loads(product)['evaluate_kwargs'])
                    if output['count']!=8 or any(c['status']!='complete' or len(c['book']['trace'])!=1057 for c in output['cells'].values()):raise ValueError('invented fullknown denominator')
                    raw=control.encoded(output)
                    if len(raw)>16*1024**2:raise ValueError('invented output cap')
                    control.immutable(scratch/'books.json',raw)
                    control.immutable(scratch/'source-report.json',{'synthetic_only':True})
                    if control.file_sha(scratch/'books.json')!=hashlib.sha256(raw).hexdigest():raise ValueError('publication digest')
                    report['synthetic_work']={'seconds':time.monotonic()-started,'normalized_bytes':len(product),'books_bytes':len(raw),'books_sha256':hashlib.sha256(raw).hexdigest(),'cells':8,'trace_rows_each':1057}
                    record({'event':'synthetic_work',**report['synthetic_work']})
            after,_=control.inventory(ROOT)
            if after!=baseline:raise ValueError('final independently rescanned20 inventory differs')
            report['final_rescan_matches']=True
            report['runtime_after']=control.runtime_hashes()
            if report['runtime_before']!=report['runtime_after']:raise ValueError('runtime changed during proof')
            report['pass']=True
        except Exception as exc:report['error']=type(exc).__name__+': '+str(exc)
        report['elapsed_seconds']=time.monotonic()-begin
        with result_path.open('x') as result:json.dump(report,result,indent=2,sort_keys=True);result.write('\n')
        record({'event':'finished','pass':report['pass'],'elapsed_seconds':report['elapsed_seconds']})
    print(json.dumps({k:report.get(k) for k in ('pass','elapsed_seconds','error')}))
    raise SystemExit(0 if report['pass'] else 1)


if __name__=='__main__':main()
