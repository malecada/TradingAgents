"""Independent raw WBETH completed-book reconstruction, no strategy imports."""
import base64
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, getcontext
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlencode, urlsplit, parse_qs
import numpy as np
from scipy.stats import t

getcontext().prec=60
D=lambda x:Decimal(str(x))
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
RUN=ROOT/'research_runs/wbeth-book-20260911'
START,DAY,N=1775001600000,86400000,91
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes())
comparisons=0;maximum=0.


def eq(a,b,label,tol=1e-8):
    global comparisons,maximum
    assert np.isfinite(float(a)) and np.isfinite(float(b)),label
    error=abs(float(a)-float(b));assert error<=tol,(label,a,str(b),error)
    comparisons+=1;maximum=max(maximum,error)


def fields(actual,expected,label):
    for k,v in expected.items():eq(actual[k],v,label+'.'+k)


def strict(raw):
    def pairs(items):
        out={}
        for k,v in items:
            assert k not in out,'duplicate JSON key';out[k]=v
        return out
    def invalid(x):raise AssertionError('nonfinite JSON '+x)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)


def verify():
    claim=read(RUN/'claim.json');receipt=read(RUN/'complete.json')
    assert claim['source']==receipt['source']=='04e1fa48336bdb10e6a9795a91e24a72526c9ef7'
    assert receipt['registration_sha256']=='9e92592a79b88716a15e7d5bba2a1b0e3c3b0891fdc415ee245c3136142c2afa'
    assert sha((RUN/'claim.json').read_bytes())==receipt['claim_sha256']
    assert datetime.fromisoformat(claim['started_at'])<datetime.fromisoformat(receipt['ended_at'])
    stamp=subprocess.check_output(['git','show','-s','--format=%cI',claim['source']],cwd=ROOT,text=True).strip()
    assert datetime.fromisoformat(stamp)<datetime.fromisoformat(claim['started_at'])
    for name,value in claim['experiment']['runtime_hashes'].items():
        path='tradingagents/research/'+name
        assert sha((ROOT/path).read_bytes())==sha(subprocess.check_output(['git','show',claim['source']+':'+path],cwd=ROOT))==value
    env={}
    for name,ref in claim['inputs'].items():
        raw=(ROOT/ref['path']).read_bytes();assert sha(raw)==ref['sha256'];env[name]=strict(raw)
    observed={};rawbytes=0
    for prefix,count in (('carry',10),('wbeth',2)):
        capture,admission=env[prefix+'_capture'],env[prefix+'_admission']
        spec=capture['request_spec']['requests'];records=capture['requests'];cells=admission['cells']
        assert len(spec)==len(records)==len(cells)==count
        assert len({r['id'] for r in records})==count
        assert {r['id'] for r in spec}=={r['id'] for r in records}=={r['id'] for r in cells}
        byid={r['id']:r for r in spec};parent={r['id']:r for r in cells}
        source_run=ROOT/'research_runs'/('carry-inputs-20260911' if prefix=='carry' else 'wbeth-inputs-20260911')
        total=0
        for r in records:
            assert all(r[k]==v for k,v in byid[r['id']].items())
            assert r==read(source_run/'outputs'/(r['id']+'-receipt.json'))
            assert r['attempted'] is True and r['body_complete'] is True and r['http_status']==200 and r['error'] is None
            assert datetime.fromisoformat(r['request_utc'])<=datetime.fromisoformat(r['retrieval_utc'])<datetime.fromisoformat(claim['started_at'])
            raw=base64.b64decode(r['body_base64'],validate=True)
            assert len(raw)==r['body_bytes'] and sha(raw)==r['body_sha256']
            total+=len(raw);rawbytes+=len(raw);observed[r['id']]=strict(raw)
            assert parent[r['id']]['status']=='complete'
            if prefix=='carry':
                actual=urlsplit(r['request_url']);base=urlsplit(r['url'])
                assert (actual.scheme,actual.netloc,actual.path)==(base.scheme,base.netloc,base.path)
                assert parse_qs(actual.query)=={k:[str(v)] for k,v in r['parameters'].items()}
        assert total==capture['total_body_bytes']
    barsids=('wbeth-spot','btc-spot','eth-spot','btc-perp','eth-perp','btc-mark','eth-mark')
    for key in barsids:
        rows=observed[key];assert len(rows)==N
        for i,r in enumerate(rows):
            assert len(r)==12 and type(r[0]) is int and type(r[6]) is int
            assert r[0]==START+i*DAY and r[6]==START+(i+1)*DAY-1
            v=[D(x) for x in r];assert all(x.is_finite() for x in v)
            assert 0<v[3]<=min(v[1],v[4])<=max(v[1],v[4])<=v[2]
            assert all(v[k]>=0 for k in (5,7,8,9,10)) and v[8]==v[8].to_integral_value()
    for asset in ('btc','eth'):
        events=observed[asset+'-funding'];assert len(events)==273
        assert len({r['fundingTime'] for r in events})==273
        for i,r in enumerate(events):
            assert r['symbol']==asset.upper()+'USDT' and type(r['fundingTime']) is int
            assert START<=r['fundingTime']<START+91*DAY and abs(r['fundingTime']-(START+i*DAY//3))<=5000
            assert D(r['markPrice']).is_finite() and D(r['markPrice'])>0 and D(r['fundingRate']).is_finite()
            daily=observed[asset+'-mark'][(r['fundingTime']-START)//DAY]
            assert D(daily[3])-D('.000001')<=D(r['markPrice'])<=D(daily[2])+D('.000001')
    info=observed['wbeth-exchange-info'];assert len(info['symbols'])==1
    metadata=info['symbols'][0]
    assert metadata==env['wbeth_admission']['cells'][0]['symbol_metadata']
    assert metadata['symbol']=='WBETHUSDT' and metadata['baseAsset']=='WBETH' and metadata['quoteAsset']=='USDT'
    assert metadata['status']=='TRADING' and metadata['isSpotTradingAllowed'] is True
    for field in metadata['filters']:assert isinstance(field,dict) and 'filterType' in field
    carrycells={r['id']:r for r in env['carry_admission']['cells']}
    carryrecords={r['id']:r for r in env['carry_capture']['requests']}
    for key in barsids[1:]:assert carrycells[key]['observations']==carrycells[key]['expected_days']==91
    assert env['wbeth_admission']['cells'][1]['observations']==env['wbeth_admission']['cells'][1]['expected_days']==91
    for asset in ('btc','eth'):
        cell=carrycells[asset+'-funding'];coverage=cell['coverage']
        assert cell['observations']==cell['expected_events']==coverage['observed_events']==coverage['matched_unique_slots']==273
        assert coverage['missing_canonical_slots_ms']==coverage['duplicate_timestamps_ms']==coverage['unexpected_timestamps_ms']==[]
    exchange={r['symbol']:r for r in observed['exchange-info']['symbols']}
    for symbol in ('BTCUSDT','ETHUSDT'):
        meta=exchange[symbol]
        assert meta['status']=='TRADING' and meta['contractType']=='PERPETUAL' and meta['quoteAsset']==meta['marginAsset']=='USDT'
    record=carryrecords['server-time'];server=observed['server-time']['serverTime'];normalized=carrycells['server-time']
    lower=int(datetime.fromisoformat(record['request_utc']).timestamp()*1000)-5000
    upper=int(datetime.fromisoformat(record['retrieval_utc']).timestamp()*1000)+5000
    assert lower<=server<=upper and normalized['server_time_ms']==server
    assert normalized['clock_check']=={'earliest_allowed_ms':lower,'latest_allowed_ms':upper,'server_minus_request_ms':server-lower-5000,
                                      'server_minus_retrieval_ms':server-upper+5000,'agrees':True}
    books=read(RUN/'outputs/books.json');summary=read(RUN/'outputs/summary.json')
    assert books['source_availability']==summary['source_availability']
    assert len(books['source_availability'])==12 and all(r['status']=='complete' for r in books['source_availability'].values())
    wb,eth,future,mark,events=[observed[k] for k in ('wbeth-spot','eth-spot','eth-perp','eth-mark','eth-funding')]
    assert all(D(r[5])>0 and D(r[8])>0 for r in (wb[0],wb[-1],future[0],future[-1]))
    benchmark=[]
    for key in ('btc-spot','eth-spot'):
        rows=observed[key];closes=[D(r[4]) for r in rows];prev=[D(rows[0][1])]+closes[:-1]
        benchmark.append([float(x/y-1) for x,y in zip(closes,prev)])
    X=np.column_stack([np.ones(N),*benchmark]);assert np.linalg.matrix_rank(X)==3
    bread=np.linalg.inv(X.T@X)
    ids=[f'wbeth-{c}-{s}'+('-zero-funding' if z else '') for z in (False,True) for c in (1000,10000) for s in ('base','stress')]
    reported={r['id']:r for r in summary['cases']}
    assert set(books['cases'])==set(reported)==set(ids)
    assert [r['id'] for r in receipt['cells']]==ids and all(r['status']=='complete' for r in receipt['cells'])
    assert receipt['cell_count']==8 and receipt['unavailable_count']==0
    findings=[]
    for identity in ids:
        b=books['cases'][identity];report=reported[identity];zero=identity.endswith('-zero-funding')
        capital=D(identity.split('-')[1]);scenario=identity.split('-')[2]
        sf,ff,slip=(D('.001'),D('.0005'),D('.0002')) if scenario=='base' else (D('.002'),D('.001'),D('.0004'))
        fields(b['costs'],{'spot_fee':sf,'perp_fee':ff,'slippage':slip},identity+'.costs')
        w0,e0,f0=D(wb[0][1]),D(eth[0][1]),D(future[0][1]);ratio=w0/e0;we=w0*(1+slip);fe=f0*(1-slip)
        qw=(capital*D('.4')/(we*(1+sf)+ratio*fe*ff)/D('.0001')).to_integral_value(rounding=ROUND_FLOOR)*D('.0001')
        qe=(qw*ratio/D('.001')).to_integral_value(rounding=ROUND_FLOOR)*D('.001')
        reserve=capital/2;spent=qw*we*(1+sf)+qe*fe*ff;idle=capital-reserve-spent
        assert qw>0 and qe>0 and idle>=capital/10 and spent<=capital*D('.4')
        fields(b['initial'],{'wbeth_quantity':qw,'eth_perp_quantity':-qe,'raw_wbeth_to_eth_spot_price_ratio':ratio,
            'assumed_wbeth_lot':D('.0001'),'assumed_eth_perp_lot':D('.001'),'wbeth_entry_price':we,'eth_perp_entry_price':fe,
            'wbeth_purchase_principal':qw*we,'wbeth_entry_fee':qw*we*sf,'eth_perp_entry_fee':qe*fe*ff,'joint_entry_spend':spent,
            'futures_reserve':reserve,'idle_cash':idle,'raw_entry_net_market_value':qw*w0-qe*e0},identity+'.entry')
        owned=[r for r in events if r['fundingTime']>START+5000];excluded=[r['fundingTime'] for r in events if r['fundingTime']<=START+5000]
        assert len(owned)==272 and len(excluded)==1 and b['excluded_first_funding_timestamps']==excluded
        dayevents=[[qe*D(r['markPrice'])*D(r['fundingRate']) for r in owned if (r['fundingTime']-START)//DAY==i] for i in range(N)]
        observedfund=sum(sum(x) for x in dayevents);fund=D(0) if zero else observedfund
        def close(sx,fx,funding):
            sfee,ffee=qw*sx*sf,qe*fx*ff;pnl=qe*(fe-fx);fwallet=reserve+funding+pnl-ffee
            proceeds=qw*sx;cash=idle+fwallet+proceeds-sfee
            return {'wbeth_exit_price':sx,'eth_perp_exit_price':fx,'wbeth_sale_proceeds':proceeds,'wbeth_exit_fee':sfee,
                    'eth_perp_exit_fee':ffee,'wbeth_price_pnl':qw*(sx-we),'eth_perp_price_pnl':pnl,'cumulative_funding_cash':funding,
                    'futures_cash_after_close':fwallet,'idle_cash_before_exit':idle,'final_cash':cash,'cash_profit':cash-capital,
                    'terminal_wbeth_quantity':0,'terminal_eth_perp_quantity':0}
        sx,fx=D(wb[-1][4])*(1-slip),D(future[-1][4])*(1+slip);final=close(sx,fx,fund)
        fees=qw*(we+sx)*sf+qe*(fe+fx)*ff;gross=qw*(D(wb[-1][4])-w0)+qe*(f0-D(future[-1][4]))
        slipping=qw*(we-w0+D(wb[-1][4])-sx)+qe*(f0-fe+fx-D(future[-1][4]))
        signed=final['wbeth_price_pnl']+final['eth_perp_price_pnl']+fund-fees
        final.update(all_fees=fees,same_quantity_frictionless_price_pnl=gross,slippage_cost=slipping,
                     cash_profit_from_signed_components=signed,cash_reconciliation_difference=0)
        fields(b['final_ledger'],final,identity+'.final');assert final['cash_profit']==signed
        previous=capital;peak=capital;drawdown=D(0);cumulative=D(0);returns=[];buffers=[]
        assert len(b['daily_trace'])==N
        for i,row in enumerate(b['daily_trace']):
            observedday=sum(dayevents[i]);daily=D(0) if zero else observedday
            negative=D(0) if zero else sum(min(x,D(0)) for x in dayevents[i])
            prior=cumulative;cumulative+=daily
            mc,mh=D(mark[i][4]),D(mark[i][2]);wc=D(wb[i][4]);wallet=reserve+cumulative;mtm=qe*(fe-mc);wv=qw*wc
            nav=idle+wallet+mtm+wv;equity=reserve+prior+negative+qe*(fe-mh);maintenance=D('.01')*qe*mh
            pre={'nav':nav,'idle_cash':idle,'futures_wallet':wallet,'short_mtm':mtm,'wbeth_value':wv,'wbeth_quantity':qw,
                 'eth_perp_quantity':-qe,'net_market_value':wv-qe*mc,'gross_market_value':wv+qe*mc}
            expected={**pre,'wbeth_close':wc,'eth_spot_close':D(eth[i][4]),'eth_perp_close':D(future[i][4]),'eth_mark_close':mc,
                      'eth_mark_high':mh,'funding_event_count':len(dayevents[i]),'funding_cash':daily,'observed_same_quantity_funding_cash':observedday,
                      'negative_funding_cash':negative,'cumulative_funding_cash':cumulative,'pre_exit_nav':nav,'margin_equity_lower_bound':equity,
                      'assumed_maintenance_requirement':maintenance,'margin_buffer_lower_bound':equity-maintenance}
            if i==90:
                fields(row['pre_exit_components'],pre,identity+'.pre-exit')
                nav=final['final_cash'];expected.update(nav=nav,idle_cash=idle+final['wbeth_sale_proceeds']-final['wbeth_exit_fee'],
                    futures_wallet=final['futures_cash_after_close'],short_mtm=0,wbeth_value=0,wbeth_quantity=0,eth_perp_quantity=0,net_market_value=0,gross_market_value=0)
            ret=nav/previous-1;returns.append(ret);expected['full_capital_daily_return']=ret;previous=nav
            fields(row,expected,identity+f'.day{i}');assert row['date']==datetime.fromtimestamp((START+i*DAY)/1000,timezone.utc).date().isoformat()
            eq(row['nav'],D(row['idle_cash'])+D(row['futures_wallet'])+D(row['short_mtm'])+D(row['wbeth_value']),identity+'.wallet-NAV')
            peak=max(peak,nav);drawdown=max(drawdown,(peak-nav)/peak);buffers.append(equity-maintenance)
        total=signed/capital;annual=total*365/N
        metrics={'cash_profit':signed,'full_capital_return':total,'annualized_simple_return_365':annual,'max_drawdown':drawdown,
                 'minimum_margin_buffer_lower_bound':min(buffers),'funding_cash':fund,'applied_funding_events':272}
        fields(b['metrics'],metrics,identity+'.metrics');fields(report['metrics'],metrics,identity+'.reportedmetrics')
        assert b['metrics']['margin_buffer_breach']==any(x<0 for x in buffers)
        assert b['metrics']['nonpositive_nav']==any(row['nav']<=0 for row in b['daily_trace'])
        for rate in ('0','0.03','0.05'):
            eq(b['cash_benchmarks'][rate],capital*D(rate)*N/365,identity+'.cashbench');eq(report['cash_benchmarks'][rate],capital*D(rate)*N/365,identity+'.reportbench')
        logsum=sum((1+x).ln() for x in returns);arithmetic=sum(returns)
        fields(b['convention_diagnostic'],{'log1p_sum':logsum,'arithmetic_daily_simple_return_sum':arithmetic,'terminal_simple_return':total,
            'invalid_log_cash_shadow':capital*logsum,'log_sum_minus_arithmetic_daily_sum':logsum-arithmetic},identity+'.convention')
        for label,wm,em in (('common_half',D('.5'),D('.5')),('common_double',D(2),D(2)),('wbeth_depeg_10pct',D('.9'),D(1)),('wbeth_depeg_50pct',D('.5'),D(1))):
            stress=close(w0*wm*(1-slip),f0*em*(1+slip),D(0));high=max(D(mark[0][1]),D(mark[0][1])*em)
            stress.update(wbeth_quantity=qw,eth_perp_quantity=-qe,wbeth_price_multiple=wm,eth_price_multiple=em,
                          margin_buffer_scenario=reserve+qe*(fe-high)-D('.01')*qe*high)
            fields(b['quantity_price_stresses'][label],stress,identity+'.'+label)
        y=np.array([float(x) for x in returns]);beta=np.linalg.lstsq(X,y,rcond=None)[0];scores=X*(y-X@beta)[:,None];meat=scores.T@scores
        for lag in range(1,8):
            cross=scores[lag:].T@scores[:-lag];meat+=(1-lag/8)*(cross+cross.T)
        widths=t.ppf(.9875,N-3)*np.sqrt(np.diag(bread@meat@bread));exposure=report['statistics']['market_exposure']
        assert exposure['status']=='complete' and exposure['observations']==91 and exposure['hac_lags']==7 and exposure['individual_confidence']==.975
        for i,k in enumerate(('intercept','btc_beta','eth_beta')):eq(exposure[k],beta[i],identity+'.'+k,1e-10)
        for i,k in ((1,'btc_interval'),(2,'eth_interval')):
            for actual,expected in zip(exposure[k],(beta[i]-widths[i],beta[i]+widths[i])):eq(actual,expected,identity+'.'+k,1e-10)
        beta_pass=all(abs(beta[i])<=.1 and beta[i]-widths[i]>=-.2 and beta[i]+widths[i]<=.2 for i in (1,2))
        assert report['necessary_historical_screens']['beta']=={'status':'complete','passes':bool(beta_pass)}
        assert report['necessary_historical_screens']['observed_drawdown_at_most_10pct']==(drawdown<=D('.1'))
        for k in ('expected_return_confidence','power'):assert report['statistics'][k]['status']=='unavailable'
        for k in ('realized_net_base_delta_at_most_1pct_nav','execution','future_tail_risk','true_eth_delta'):assert report[k]['status']=='unavailable'
        assert b['true_eth_delta']['status']=='unavailable' and not report['graduation']
        assert b['held_zero_activity_bars']=={'wbeth':sum(D(r[5])==0 or D(r[8])==0 for r in wb),'eth_perp':sum(D(r[5])==0 or D(r[8])==0 for r in future)}
        findings.append({'id':identity,'capital':float(capital),'wbeth_quantity':float(qw),'eth_short_quantity':float(qe),'gross_price_pnl':float(gross),
            'slippage':float(slipping),'commissions':float(fees),'funding_cash':float(fund),'cash_profit':float(signed),'full_capital_return':float(total),
            'descriptive_annualized_return':float(annual),'max_drawdown':float(drawdown),'btc_beta':float(beta[1]),'eth_beta':float(beta[2]),
            'btc_interval':exposure['btc_interval'],'eth_interval':exposure['eth_interval'],'depeg_10pct_cash':b['quantity_price_stresses']['wbeth_depeg_10pct']['cash_profit'],
            'depeg_50pct_cash':b['quantity_price_stresses']['wbeth_depeg_50pct']['cash_profit']})
    for c in (1000,10000):
        pair=[books['cases'][f'wbeth-{c}-{s}'] for s in ('base','stress')];cashpass=all(r['metrics']['cash_profit']>0 and r['metrics']['annualized_simple_return_365']>=.03 for r in pair)
        for s in ('base','stress'):
            primary,zero=[books['cases'][f'wbeth-{c}-{s}'+suffix] for suffix in ('','-zero-funding')]
            assert primary['initial']==zero['initial']
            eq(primary['metrics']['cash_profit']-zero['metrics']['cash_profit'],primary['metrics']['funding_cash'],'paired profit difference')
            for suffix in ('','-zero-funding'):assert reported[f'wbeth-{c}-{s}'+suffix]['necessary_historical_screens']['primary_positive_cash_and_3pct_annual_base_and_stress']==cashpass
    assert summary['case_count']==8 and summary['primary_count']==summary['counterfactual_count']==4 and summary['validated_strategies']==0 and not summary['graduation']
    assert set(receipt['output_sha256'])=={'books.json','summary.json'}
    for name,h in receipt['output_sha256'].items():assert sha((RUN/'outputs'/name).read_bytes())==h
    size=sum((RUN/'outputs'/name).stat().st_size for name in receipt['output_sha256']);assert size<=20*1024**2
    guard=read(HERE/'wbeth-book-resource-execution.json');assert guard['child_exit_code']==0 and guard['limit_reason'] is None
    assert guard['peak_sampled_tree_rss_bytes']<guard['rss_limit_bytes']==512*1024**2 and guard['elapsed_seconds']<guard['wall_limit_seconds']==120
    from tradingagents.research.verify import verify_run
    structural=verify_run(RUN);assert structural['cell_count']==8 and structural['unavailable_count']==0 and structural['output_count']==2
    return {'status':'PASS','source':claim['source'],'registration_sha256':receipt['registration_sha256'],'comparisons':comparisons,'maximum_absolute_error':maximum,
            'cells':8,'primary_cases':4,'paired_zero_funding_cases':4,'daily_nav_rows':728,'stress_scenarios_reconstructed':32,'raw_receipts_verified':12,
            'raw_body_bytes':rawbytes,'output_bytes':size,'output_sha256':receipt['output_sha256'],'findings':findings,'resource':guard,'structural_verification':structural,
            'method':'60-digit Decimal signed two-quantity cash/wallet reconstruction; raw hashes/schema/clocks; independent OLS and Bartlett HAC7 sandwich with t88 intervals. No financial implementation/statistics-module import or new experiment/network.',
            'limitations':['Market-value hedge is not contractual ETH delta','One spent episode, no expected-profit confidence/power','No staking attribution from zero funding','Assumed fee assets/lots/fills','Actual margin/liquidation and redemption unavailable','Scenarios are not universal tail bounds','External backup or pre-result push timing not established by receipt verification']}


if __name__=='__main__':
    result=verify()
    with (HERE/'wbeth-book-review.json').open('x') as out:json.dump(result,out,indent=2,allow_nan=False);out.write('\n')
    print(json.dumps({'status':result['status'],'comparisons':result['comparisons'],'maximum_error':result['maximum_absolute_error'],'findings':result['findings']}))
