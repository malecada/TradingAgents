"""Invented source/analysis integration proof; no transport or real research run.

Run each mode through the retained resource_guard_v2.py. Exclusive result/output
publication prevents replacing earlier failures. Full source inventories are
hashed before/after captured-mode inspection. No capture module is modified.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tradingagents.research_options_capture import analysis,returned
from tradingagents.research_options_capture.schedule import ASSETS,DAY,HOUR
from tests.research.test_options_capture_adapter import metadata,T


def write(path,value):
    raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    with path.open('xb') as stream:stream.write(raw)
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def known():
    options,futures=metadata();expiry=T+45*DAY
    date=datetime.fromtimestamp(expiry/1000,timezone.utc).strftime('%y%m%d')
    selection={};records={};benchmarks={};funding={}
    for asset in ASSETS:
        selection[asset]={'asset':asset,'call':f'{asset}-{date}-100-C','put':f'{asset}-{date}-100-P','expiry_ms':expiry,'strike':'100','quantity':'0.01','option_tick':'0.1'}
        for row in options['optionSymbols']:
            if row['underlying']==asset+'USDT':
                row['expiryDate']=expiry;row['symbol']=selection[asset]['call' if row['side']=='CALL' else 'put']
        for row in futures['symbols']:
            if row['symbol']==asset+'USDT':
                for f in row['filters']:
                    if f['filterType']=='MIN_NOTIONAL':f['notional']='0.01'
        records[asset]=[];benchmarks[asset]=[];times=[];events=[]
        for hour in range(1057):
            price=str(100+hour%7);nominal=T+hour*HOUR
            row={'time_ms':nominal,'action_time_ms':nominal+5000,'entry_available':True,'hedge_available':True,'exit_available':True,
                 'valuation_available':True,'option_valuation_available':True,'perp_valuation_available':True,'index':price,
                 'missing_sources':[],'stale_sources':[]}
            for side,delta in [('call',('1','.2','.7','.4')[hour%4]),('put','-.5'),('perp','0')]:
                row[side]={'unit':1,'bid':'10' if side!='perp' else price,'ask':'10.1' if side!='perp' else price,
                           'bid_qty':'100','ask_qty':'100','mark':'10' if side!='perp' else price,'delta':delta}
            records[asset].append(row);benchmarks[asset].append(price)
            times.append(nominal+3000)
            if hour:events.append({'time_ms':nominal+3000,'rate':'.0001' if hour%2 else '-.0001','mark':price})
        funding[asset]={'coverage_known':True,'engine_inputs':{'expected_funding_times':times,'funding_events':events}}
    rules={'options':options,'futures':futures}
    return {'entry_ms':T,'selection':selection,'records':records,'benchmarks':benchmarks,'funding':funding,
            'initial_rules':rules,'initial_rules_ms':T-60000,'rule_vintages':[dict(rules,available_ms=T+d*DAY) for d in range(1,45)]}


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['known','returned'],required=True)
    p.add_argument('--package',type=Path);p.add_argument('--data',type=Path);p.add_argument('--assignment-sha256')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--books',type=Path,required=True)
    args=p.parse_args();start=time.monotonic();report={'kind':'invented-engineering-only','mode':args.mode,'financial_evidence':False}
    before=None
    try:
        if args.mode=='known':inputs=known();report['source_scope']='Pure invented1057-hour metadata/records; bypasses capture admission intentionally to test the separate known-cash output path.'
        else:
            assignment=returned.package_assignment(args.package,args.assignment_sha256)
            before=returned._inventory(args.data,assignment['entry_ms']);report['raw_inventory_before']=before
            prepared=returned.prepare(package=args.package,data=args.data,expected_assignment_sha256=args.assignment_sha256)
            report['returned_source_report']=prepared['source_report']
            inputs=prepared['evaluate_kwargs']
            if inputs is None:
                raise ValueError('Full synthetic worker source did not produce frozen analysis inputs: '+str(prepared['unavailable_cells']))
            report['normalized_hours']={a:len(inputs['records'][a]) for a in ASSETS}
            report['funding_coverage']={a:inputs['funding'][a]['coverage_known'] for a in ASSETS}
            report['normalization_bytes']=len(json.dumps(inputs,sort_keys=True,allow_nan=False).encode())
        output=analysis.evaluate(**inputs)
        report['output']=write(args.books,output)
        report['cells']={k:{'status':row['status'],'reason':row.get('reason'),'trace_count':len(row.get('book',{}).get('trace',[])),
                            'trade_count':len(row.get('book',{}).get('trades',[])),'funding_count':len(row.get('book',{}).get('funding_events',[]))} for k,row in output['cells'].items()}
        report['exact_eight_cells']=set(output['cells'])==set(analysis.CELLS) and output['count']==8
        report['output_below_16MiB']=report['output']['bytes']<=16*1024**2
        if args.mode=='known':
            report['all_eight_cash_complete']=all(row['status']=='complete' and row['trace_count']==1057 and row['trade_count']>=1000 and row['funding_count']==1056 for row in report['cells'].values())
        else:
            after=returned._inventory(args.data,assignment['entry_ms']);report['raw_inventory_after']=after
            report['raw_unchanged']=before==after
            report['package_assignment_unchanged']=assignment==returned.package_assignment(args.package,args.assignment_sha256)
        report['pass']=report['exact_eight_cells'] and report['output_below_16MiB'] and (report['all_eight_cash_complete'] if args.mode=='known' else report['raw_unchanged'] and report['package_assignment_unchanged'])
    except Exception as exc:
        report.update(pass_=False,error=type(exc).__name__+': '+str(exc));report['pass']=False
        if args.mode=='returned' and before is not None:
            report['raw_inventory_after']=returned._inventory(args.data,assignment['entry_ms']);report['raw_unchanged']=before==report['raw_inventory_after']
    report['elapsed_seconds']=time.monotonic()-start
    report['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'tradingagents/research_options_capture').glob('*.py'))}
    write(args.output,report);print(json.dumps({'pass':report['pass'],'elapsed_seconds':report['elapsed_seconds'],'result':str(args.output)}))
    raise SystemExit(0 if report['pass'] else 1)


if __name__=='__main__':main()
