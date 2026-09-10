"""Independent saved-evidence checks. No calculator import, market access or replay."""
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
KEY='dated_carry_feasibility_2026_09_10'
DOC=Path('docs/carry-feasibility-2026-09-10')
CAPTURE=Path('data/carry-feasibility/2026-09-10/capture')
LEDGER=CAPTURE.parent/'measurement_ledger.jsonl'
TOL=F('1e-20')
YEAR=365*86400


def require(condition,label):
    if not condition:raise AssertionError(label)


def number(value):
    require(type(value) in (str,int) or isinstance(value,(Decimal,F)), 'exact numeric type')
    try:return F(value)
    except (ValueError,OverflowError,ZeroDivisionError) as exc:raise AssertionError('finite numeric value') from exc


def near(actual,expected,label):
    require(abs(number(actual)-number(expected))<=TOL,label)


def ceil(value):return -((-value.numerator)//value.denominator)


def depth(book):
    result={}
    for side in ('bids','asks'):
        require(isinstance(book.get(side),list) and book[side], 'two-sided book')
        levels=[]
        for row in book[side]:
            require(isinstance(row,list) and len(row)==2, 'depth level shape')
            p,q=map(number,row)
            require(p>0 and q>0,'positive depth')
            if levels:require(p<levels[-1][0] if side=='bids' else p>levels[-1][0], 'strict depth order')
            levels.append((p,q))
        result[side]=levels
    require(result['bids'][0][0]<result['asks'][0][0],'noncrossed book')
    return result


def take(levels,quantity,multiplier=F(1)):
    result=F(0);count=0
    for price,available in levels:
        if quantity<=0:break
        amount=min(quantity,available);result+=amount*price*multiplier;quantity-=amount;count+=1
    require(quantity==0,'no depth extrapolation')
    return result,count


def expected_entry(pair,identity,gate):
    """Independent exact-rational maximal-lot feasibility, not a payoff search."""
    sb,fb=depth(pair['books']['spot']),depth(pair['books']['future'])
    spec=pair['instrument'];sr,fr=spec['spot_rules'],spec['future_rules']
    for rules in (sr,fr):
        require(number(rules['step_size'])>0 and number(rules['max_qty'])>0,'positive lot limits')
        require(0<=number(rules['min_qty'])<=number(rules['max_qty']),'quantity limits')
        require(number(rules['min_notional'])>=0,'minimum notional')
        if rules.get('max_notional') is not None:require(number(rules['max_notional'])>=number(rules['min_notional']),'notional bounds')
    cap=number(identity['capital']);reserve=number(identity['reserve']);scale=number(identity['fee_multiplier'])
    sf=number(gate['spot_fee'])*scale;ef=number(gate['future_entry_fee'])*scale;xf=number(gate['future_expiry_fee'])*scale
    require(cap>0 and 0<reserve<=1 and all(0<=r<1 for r in (sf,ef,xf)),'registered positive capital and valid rates')
    m=number(spec['future_multiplier']);step=number(fr['step_size']);spotstep=number(sr['step_size'])
    require(m>0,'positive contract multiplier')
    totalspot=sum(q for _,q in sb['asks']);totalfuture=sum(q for _,q in fb['bids'])
    def candidate(lots):
        contracts=lots*step;q=contracts*m;g=ceil(q/(1-sf)/spotstep)*spotstep
        if contracts>min(totalfuture,number(fr['max_qty'])) or g>min(totalspot,number(sr['max_qty'])):return None
        A,na=take(sb['asks'],g);B,nb=take(fb['bids'],contracts,m)
        if any(rules.get('max_notional') is not None and v>number(rules['max_notional']) for rules,v in [(sr,A),(fr,B)]):return None
        E=B*ef;committed=A+E+B*reserve
        if committed>cap:return None
        return dict(future_lots=lots,future_contracts=contracts,future_base_quantity=q,
            spot_gross_quantity=g,spot_entry_base_fee=g*sf,spot_net_quantity=g*(1-sf),
            residual_base_quantity=g*(1-sf)-q,spot_entry_cost=A,
            spot_entry_base_fee_quote_equivalent=A*sf,future_entry_notional=B,
            future_entry_cash_fee=E,reserve_committed=B*reserve,
            reserve_cash_numerator=B*reserve.numerator,entry_cash_required=committed,
            uncommitted_cash=cap-committed,spot_entry_vwap=A/g,future_entry_vwap=B/q,
            spot_ask_levels_used=na,future_bid_levels_used=nb)
    low=0;high=int(min(totalfuture,number(fr['max_qty']))//step)
    while low<high:
        mid=(low+high+1)//2
        if candidate(mid) is None:high=mid-1
        else:low=mid
    if low==0:return None
    e=candidate(low)
    if any(e[qty]<number(rules['min_qty']) or e[notional]<number(rules['min_notional']) for rules,qty,notional in [(sr,'spot_gross_quantity','spot_entry_cost'),(fr,'future_contracts','future_entry_notional')]):return None
    e.update(capital=cap,reserve_numerator=reserve.numerator,reserve_denominator=reserve.denominator,
        fee_multiplier=scale,spot_entry_fee_rate=sf,spot_exit_fee_rate=sf,future_entry_fee_rate=ef,
        future_expiry_fee_rate=xf,future_multiplier=m,initial_top_spot_ask=sb['asks'][0][0],
        future_entry_principal_cashflow=F(0))
    return e


def unavailable(record):
    require(record.get('status')=='unavailable' and isinstance(record.get('reason'),str) and bool(record['reason']),'explicit unavailable reason')
    require(not any(k in record for k in ('net_cash_profit','terminal_nav','net_return_on_capital')),'unavailable has no invented payoff')


def check_entry(entry,pair,identity,gate):
    expected=expected_entry(pair,identity,gate)
    if expected is None:
        unavailable(entry);return
    require(entry['status']=='complete','feasible entry retained')
    for k,v in expected.items():near(entry[k],v,'entry '+k)
    require(entry['reserve_fraction']==identity['reserve'],'reserve identity')
    require(entry['executable_admission'] is False,'conditional entry')
    require(entry['exact_matched_base_units']==(expected['residual_base_quantity']==0),'residual neutrality flag')
    require(entry['fee_status']=='registered_assumptions_not_verified_account_rates','fee qualification')
    require(entry['fee_rounding']=='unrounded_scenario_no_exchange_rounding_claim','fee rounding qualification')


def check_terminal(result,entry,ratio,bps,seconds,gate):
    require(result['status']=='complete','complete terminal case')
    for k,v in entry.items():require(result.get(k)==v,'terminal retains entry '+k)
    c,q,h,A,B,E=[number(entry[k]) for k in ('capital','future_base_quantity','spot_net_quantity','spot_entry_cost','future_entry_notional','future_entry_cash_fee')]
    ratio,bps,seconds=number(ratio),number(bps),number(seconds)
    require(ratio>0 and 0<=bps<10000 and seconds>0,'terminal coordinates')
    X=number(entry['initial_top_spot_ask'])*ratio;S=X*(1-bps/10000)
    sale=h*S;spotfee=sale*number(entry['spot_exit_fee_rate']);expiryfee=q*X*number(entry['future_expiry_fee_rate'])
    future=B-q*X;profit=sale-spotfee+future-A-E-expiryfee
    reserve=number(entry['reserve_cash_numerator'])/number(entry['reserve_denominator'])
    reserve_after=reserve+future-expiryfee
    expected=dict(terminal_index_ratio=ratio,adverse_exit_bps=bps,seconds_to_expiry=seconds,
        terminal_index=X,terminal_spot_sale_price=S,net_cash_profit=profit,terminal_nav=c+profit,
        net_return_on_capital=profit/c,annualized_simple_return=profit/c*YEAR/seconds,
        terminal_futures_reserve=reserve_after,terminal_residual_spot_value=(h-q)*S)
    for k,v in expected.items():near(result[k],v,'terminal '+k)
    components=dict(spot_entry_principal=-A,future_entry_principal=0,future_entry_cash_fee=E,
        spot_sale_gross=sale,spot_exit_fee=spotfee,spot_sale_net=sale-spotfee,
        future_settlement_pnl=future,future_expiry_fee=expiryfee,reserve_released=reserve,
        uncommitted_cash=number(entry['uncommitted_cash']),paid_financing=0,credited_interest=0)
    require(set(result['cash_components'])==set(components),'all terminal cash legs')
    for k,v in components.items():near(result['cash_components'][k],v,'cash leg '+k)
    near(result['terminal_nav'],components['uncommitted_cash']+sale-spotfee+reserve_after,'cash reconciliation')
    require(result['terminal_reserve_insufficient'] is (reserve_after<0),'terminal margin flag')
    require(result['pathwise_margin_survival_verified'] is False and result['executable_admission'] is False,'no executable survival claim')
    expected_rates={number(x) for x in gate['cash_benchmark_annual']}
    require({number(k) for k in result['benchmarks']}==expected_rates and len(result['benchmarks'])==len(expected_rates),'all benchmark identities')
    for k,row in result['benchmarks'].items():
        benchmark=c*number(k)*seconds/YEAR
        near(row['cash_profit'],benchmark,'benchmark cash')
        near(row['excess_cash_profit'],profit-benchmark,'benchmark excess cash')
        near(row['excess_return_on_capital'],(profit-benchmark)/c,'benchmark excess return')


def expected_ids(gate):
    entries=[];rows=[]
    for n,a,c,r,f in itertools.product(range(gate['snapshots']),gate['assets'],gate['capital'],gate['reserve_fractions'],gate['fee_multipliers']):
        identity=f'{n}|{a}|{c}|{r}|{f}';entries.append(identity)
        rows.extend(identity+'|'+x+'|'+b for x,b in itertools.product(gate['terminal_index_ratios'],gate['adverse_exit_bps']))
    return entries,rows


def check_ids(entries,rows,gate):
    expected_entries,expected_rows=expected_ids(gate)
    require(entries==expected_entries and len(entries)==48,'48 exact ordered entry identities')
    require(rows==expected_rows and len(rows)==432,'432 exact ordered scenario identities')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canon(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def check_receipts(root,manifest):
    """Verify every raw byte/receipt and the immutable complete output manifest."""
    out=root/CAPTURE
    expected={str(p.relative_to(root)) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'}
    require(set(manifest['files'])==expected,'all saved capture files hashed')
    for name,digest in manifest['files'].items():require(sha(root/name)==digest,'saved hash '+name)
    receipts={};payloads={}
    for receipt in manifest['requests']:
        key=receipt['id'];require(key not in receipts,'unique request identity');receipts[key]=receipt
        prefix={'spot':'https://api.binance.com/api/v3/','future':'https://fapi.binance.com/fapi/v1/'}[receipt['market']]
        require(receipt['endpoint'] in ('time','exchangeInfo','depth') and receipt['url'].split('?')[0]==prefix+receipt['endpoint'],'registered public endpoint')
        require(read(root/CAPTURE/'raw'/f'{key}.json')==receipt,'raw receipt agreement')
        expected_path=str(CAPTURE/'raw'/f'{key}.bin')
        require(receipt['raw_path']==expected_path,'registered raw path')
        raw=(root/expected_path).read_bytes()
        require(hashlib.sha256(raw).hexdigest()==receipt['sha256'] and len(raw)==receipt['bytes'],'raw body hash/size')
        require(type(receipt['start_ns']) is int and type(receipt['end_ns']) is int and receipt['end_ns']>=receipt['start_ns'] and receipt['elapsed_ns']>=0,'receipt clock order')
        if receipt['http_status']==200 and receipt['error'] is None:payloads[key]=json.loads(raw)
    require({p.stem for p in (out/'raw').glob('*.json')}==set(receipts),'no omitted request receipts')
    return receipts,payloads


def check_pair(pair,receipts,payloads,clocks):
    """Check raw-to-normalized books and saved event-age/time-skew admission."""
    selected=[];expected_errors=[];expected_qualifications=[]
    for market in ('spot','future'):
        key=pair['receipts'][market];receipt=receipts[key];selected.append(receipt)
        require(receipt['market']==market and receipt['endpoint']=='depth','book receipt identity')
        require(receipt['parameters']=={'symbol':pair['instrument'][market+'_id'],'limit':100},'depth request parameters')
        body=payloads.get(key)
        if not isinstance(body,dict) or 'asks' not in body or 'bids' not in body:
            expected_errors.append(market+'_book_unavailable');continue
        require(pair['books'][market]=={k:body[k] for k in ('bids','asks')},'book agrees with raw response')
        event=body.get('E')
        if event is None:expected_qualifications.append(market+'_event_timestamp_unavailable');continue
        if type(event) is not int or not 1500000000000<event<4100000000000:
            expected_errors.append(market+'_event_time_invalid');continue
        end=F(receipt['end_ns'],1000000)+number(clocks[market]['offset_ms'])
        upper=end+number(clocks[market]['uncertainty_ms']);age=upper-event
        near(pair['maximum_age_ms'][market],age,'maximum event age')
        if age>5000:expected_errors.append(market+'_book_stale')
        if event>upper+1000:expected_errors.append(market+'_book_future_dated')
    span=F(max(x['end_ns'] for x in selected)-min(x['start_ns'] for x in selected),1000000000)
    if span>5:expected_errors.insert(0,'quote_pair_exceeds_five_seconds')
    near(pair['pair_span_seconds'],span,'pair time span')
    near(pair['decision_future_ms'],F(max(x['end_ns'] for x in selected),1000000)+number(clocks['future']['offset_ms']),'future decision clock')
    require(pair['errors']==expected_errors,'pair failure admission')
    require(pair['qualifications']==expected_qualifications,'freshness unknown retained')


def check_saved(root=ROOT):
    root=Path(root);out=root/CAPTURE;manifest=read(out/'manifest.json');start=read(out/'start.json')
    gate=start['gate'];baseline=start['baseline'];source=manifest['source_commit']
    require(manifest['experiment']==KEY and source==start['source_commit'],'registered source identity')
    current=read(root/'data/predlab/gates.json')
    require(current[KEY]==gate,'current registered gate unchanged')
    require(sha(root/gate['charter'])==gate['charter_sha256'],'charter pin')
    require(read(root/DOC/'baseline.json')==baseline,'baseline receipt unchanged')
    for key,digest in baseline['old_gate_objects'].items():require(canon(current[key])==digest,'old gate '+key)
    oldledger=(root/'data/predlab/trial_ledger.jsonl').read_bytes()
    require(hashlib.sha256(oldledger).hexdigest()==baseline['financial_ledger_sha256']==gate['original_ledger_sha256'] and len(oldledger.splitlines())==820,'old financial ledger unchanged')
    for name in ('scripts/capture_dated_carry_2026_09_10.py','scripts/carry_feasibility_math_2026_09_10.py','data/predlab/gates.json',gate['charter']):
        committed=subprocess.check_output(['git','show',source+':'+name],cwd=root)
        require((root/name).read_bytes()==committed,'committed measurement source '+name)
    require(manifest['ledger_path']==str(LEDGER) and sha(root/LEDGER)==manifest['ledger_sha256'],'measurement ledger pin')
    receipts,payloads=check_receipts(root,manifest)
    inventory=read(out/'inventory.json');clocks=inventory['clocks']
    for market,clock in clocks.items():
        keys=[k for k,r in receipts.items() if r['market']==market and r['endpoint']=='time']
        require(len(keys)==1,'single calibration per market');r=receipts[keys[0]];body=payloads[keys[0]]
        server=body['serverTime'];require(type(server) is int and 1500000000000<server<4100000000000,'UTC millisecond server clock')
        uncertainty=F(r['elapsed_ns'],2000000);require(0<=uncertainty<=2500,'calibration uncertainty limit')
        near(clock['offset_ms'],server-F(r['start_ns']+r['end_ns'],2000000),'calibration offset')
        near(clock['uncertainty_ms'],uncertainty,'calibration uncertainty');require(clock['server_ms']==server,'server clock identity')
    snapshots=[read(out/f'snapshot_{i}.json') for i in range(3)]
    for i,snapshot in enumerate(snapshots):
        require(snapshot['number']==i and snapshot['scheduled_offset_seconds']==gate['snapshot_offsets_seconds'][i],'snapshot schedule identity')
        require(snapshot['errors']==inventory['errors'],'global admission errors retained')
        require(snapshot['actual_offset_seconds']>=snapshot['scheduled_offset_seconds'],'no early scheduled snapshot')
        selected=inventory['inventory']['selected'] if inventory['inventory'] else {}
        require(set(snapshot['pairs'])==set(selected),'all selected quote pairs retained')
        for asset,pair in snapshot['pairs'].items():
            require(pair['instrument']==inventory['inventory']['selected'][asset],'frozen instrument identity')
            check_pair(pair,receipts,payloads,clocks)
    entries=read(out/'entries.json');rows=[json.loads(line) for line in (root/LEDGER).read_text().splitlines()]
    check_ids([e['id'] for e in entries],[r['measurement_id'] for r in rows],gate)
    byid={e['id']:e for e in entries};complete=0
    for entry in entries:
        n,a,c,reserve,fee=entry['id'].split('|');identity=dict(snapshot=int(n),asset=a,capital=c,reserve=reserve,fee_multiplier=fee)
        require(all(entry[k]==v for k,v in identity.items()),'full entry identity')
        snapshot=snapshots[int(n)];pair=snapshot['pairs'].get(a)
        if snapshot['errors'] or pair is None or pair['errors']:unavailable(entry['entry'])
        else:
            try:expected_entry(pair,entry,gate)
            except (AssertionError,KeyError,ValueError):unavailable(entry['entry'])
            else:check_entry(entry['entry'],pair,entry,gate)
    for row in rows:
        fields=row['measurement_id'].split('|');eid='|'.join(fields[:5]);entry=byid[eid];ratio,bps=fields[5:]
        require(row['experiment']==KEY and all(row[k]==entry[k] for k in ('snapshot','asset','capital','reserve','fee_multiplier')),'full scenario identity')
        require(row['terminal_index_ratio']==ratio and row['adverse_exit_bps']==bps,'terminal identity')
        require(row['executable_admission'] is False and row['strategy_validated'] is False,'conditional measurement flags')
        pair=snapshots[entry['snapshot']]['pairs'].get(entry['asset'])
        require(row['instrument']==(pair['instrument']['future_id'] if pair else None),'scenario instrument')
        if entry['entry']['status']!='complete':
            unavailable(row['result']);require(row['result']['reason']==entry['entry']['reason'],'unavailable reason propagated')
        else:
            seconds=(number(pair['instrument']['expiry_ms'])-number(pair['decision_future_ms']))/1000
            check_terminal(row['result'],entry['entry'],ratio,bps,seconds,gate);complete+=1
    require(manifest['measurement_rows']==432 and manifest['complete_rows']==complete,'manifest denominators')
    require(manifest['financial_ledger_unchanged'] is True and manifest['validated_strategies']==0,'no promotion or central trial')
    return dict(status='pass',source_commit=source,manifest_sha256=sha(out/'manifest.json'),
        entries=48,scenarios=432,complete_scenarios=complete,unavailable_scenarios=432-complete,
        requests=len(receipts),numeric_absolute_tolerance='1e-20',arithmetic='independent exact fractions',
        calculator_imported=False,market_requests=0,financial_ledger_unchanged=True,validated_strategies=0)


if __name__=='__main__':
    result=check_saved()
    with Path(__file__).with_name('saved-review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
