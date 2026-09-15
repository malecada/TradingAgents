"""Actual history hash scans plus invented output publication, no financial replay.

Invoke under resource_guard_v2.py. This is a modular workload envelope, not a
literal new claim/terminal lifecycle. Scratch/progress/failures remain retained.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tradingagents.research_options_capture import control


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--result',type=Path,required=True)
    parser.add_argument('--synthetic-books',type=Path,required=True)
    args=parser.parse_args();began=time.monotonic()
    scratch=Path(tempfile.mkdtemp(prefix='options-history-output-envelope-'))
    baseline_path=ROOT/'research/strategy-search-2026-09-11/reviews/options-current-history-20260915.json'
    baseline=json.loads(baseline_path.read_bytes())['prior_claims']
    expected_output='43f5870a56b4c46a90fb06c1cb4ee435ee8deb865101edcd0c836b487d84d1a5'
    progress=args.result.with_suffix('.progress.jsonl')
    report={'scope':'Read-only actual nineteen-history reconstruction plus invented full-output atomic staging. No historical output values parsed or financial calculation executed.',
            'kind':'modular-history-output-resource-envelope','scratch':str(scratch),'history_baseline':str(baseline_path),
            'history_baseline_sha256':control.file_sha(baseline_path),'expected_history_count':19,'expected_complete':16,'expected_failed':3,
            'literal_runner_history_scans':7,'envelope_history_scans':8,'scans':[],'actual_options_claim_created':False,
            'literal_new_protocol_terminal_verified':False,'source_hashes_before':control.runtime_hashes(),
            'publication_engineering_only':True,'pass':False}
    with progress.open('x') as log:
        def record(value):log.write(json.dumps(value,sort_keys=True)+'\n');log.flush()
        record({'event':'start','scratch':str(scratch)})
        try:
            if len(baseline)!=19 or sum(v['terminal']=='complete.json' for v in baseline.values())!=16 or sum(v['terminal']=='failed.json' for v in baseline.values())!=3:raise ValueError('saved actual baseline count/status changed')
            for index in range(8):
                start=time.monotonic();actual,claims=control.inventory(ROOT)
                if actual!=baseline:raise ValueError('actual historical claim/terminal/output hashes differ from saved baseline')
                item={'scan':index+1,'seconds':time.monotonic()-start,'history_count':len(actual),'complete':sum(v['terminal']=='complete.json' for v in actual.values()),'failed':sum(v['terminal']=='failed.json' for v in actual.values()),'inventory_sha256':control.sha(control.canonical(actual))}
                report['scans'].append(item);record(item)
                # Publish between pre- and post-analysis-style scans, then retain
                # scans7/8 as after-publication history-byte checks.
                if index==5:
                    if control.file_sha(args.synthetic_books)!=expected_output:raise ValueError('invented known-output identity mismatch')
                    raw=args.synthetic_books.read_bytes()
                    if len(raw)!=11618712 or len(raw)>16*1024**2:raise ValueError('bounded11.6MB known-output fixture')
                    before=time.monotonic();control.immutable(scratch/'books.json',raw)
                    source=control.encoded({'scope':'Invented output envelope; no empirical inputs or claim','input_sha256':expected_output})
                    control.immutable(scratch/'source-report.json',source)
                    sizes=control.member_sizes(scratch,{'books.json','source-report.json'},64*1024**2,16*1024**2)
                    hashes={name:control.file_sha(scratch/name) for name in sizes}
                    if hashes['books.json']!=expected_output or any(p.name.startswith('.pending-') for p in scratch.iterdir()):raise ValueError('publication identity or unclosed staging')
                    duplicate_refused=False
                    try:control.immutable(scratch/'books.json',raw)
                    except FileExistsError:duplicate_refused=True
                    if not duplicate_refused or any(p.name.startswith('.pending-') for p in scratch.iterdir()):raise ValueError('immutable replay/staging refusal')
                    report['publication']={'seconds':time.monotonic()-before,'retained_sizes':sizes,'output_sha256':hashes,
                        'peak_book_staging_logical_bytes':2*len(raw),'staging_reserve_bytes':16*1024**2,'registered_output_total_ceiling':64*1024**2,
                        'duplicate_refused_without_orphan':duplicate_refused,'method':'actual control.immutable fsync+exclusive hardlink publication; scratch only, not Episode.write_output or terminal'}
                    record({'event':'publication',**report['publication']})
            report['source_hashes_after']=control.runtime_hashes()
            report['history_unchanged_all_eight_scans']=all(item['inventory_sha256']==report['scans'][0]['inventory_sha256'] for item in report['scans'])
            report['source_unchanged']=report['source_hashes_before']==report['source_hashes_after']
            report['pass']=report['history_unchanged_all_eight_scans'] and report['source_unchanged']
        except Exception as exc:report['error']=type(exc).__name__+': '+str(exc)
        report['elapsed_seconds']=time.monotonic()-began
        with args.result.open('x') as result:json.dump(report,result,indent=2,sort_keys=True);result.write('\n')
        record({'event':'finished','pass':report['pass'],'seconds':report['elapsed_seconds']})
    print(json.dumps({'pass':report['pass'],'result':str(args.result),'seconds':report['elapsed_seconds']}))
    raise SystemExit(0 if report['pass'] else 1)


if __name__=='__main__':main()
