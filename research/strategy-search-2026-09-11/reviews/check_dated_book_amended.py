"""Independent completed-book reconstruction; no financial engine/stats imports."""
import base64
import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, getcontext
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile
from urllib.parse import urlsplit, parse_qs

import numpy as np
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
RUN = ROOT / 'research_runs/dated-book-amended-20260911'
START, DAY, HOUR, N = 1777593600000, 86400000, 3600000, 56
END = START + N * DAY
getcontext().prec = 60
D = lambda x: Decimal(str(x))
sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda p: json.loads(p.read_bytes())
comparisons, max_error = 0, 0.0


def eq(actual, expected, label, tolerance=1e-8):
    global comparisons, max_error
    assert np.isfinite(float(actual)) and np.isfinite(float(expected)), label
    error = abs(float(actual) - float(expected))
    assert error <= tolerance, (label, actual, str(expected), error)
    comparisons += 1
    max_error = max(max_error, error)


def fields(actual, expected, label):
    for key, value in expected.items():
        eq(actual[key], value, label + '.' + key)


def raw(record):
    assert record['attempted'] and record['http_status'] == 200
    assert record['body_complete'] and record['error'] is None
    assert datetime.fromisoformat(record['request_utc']) <= datetime.fromisoformat(record['retrieval_utc'])
    body = base64.b64decode(record['body_base64'], validate=True)
    assert len(body) == record['body_bytes'] and sha(body) == record['body_sha256']
    return body


def bars(rows, first, interval):
    for i, row in enumerate(rows):
        assert len(row) == 12 and int(row[0]) == first + i * interval
        assert int(row[6]) == first + (i + 1) * interval - 1
        values = [D(x) for x in row]
        assert all(x.is_finite() for x in values)
        assert 0 < values[3] <= min(values[1], values[4]) <= max(values[1], values[4]) <= values[2]
        assert all(values[k] >= 0 for k in (5, 7, 8, 9, 10))
        assert values[8] == values[8].to_integral_value()


def check():
    claim = read(RUN/'claim.json')
    receipt = read(RUN/'complete.json')
    assert claim['source'] == receipt['source'] == 'd75b6d15b3e08c10616fe25fbca4c01cf46b29ba'
    assert sha((RUN/'claim.json').read_bytes()) == receipt['claim_sha256']
    assert receipt['cell_count'] == 8 and receipt['unavailable_count'] == 0
    assert all(x['status'] == 'complete' for x in receipt['cells'])
    assert set(receipt['output_sha256']) == {'books.json','summary.json','resource.json'}
    assert datetime.fromisoformat(claim['started_at']) < datetime.fromisoformat(receipt['ended_at'])
    committed_at=subprocess.check_output(['git','show','-s','--format=%cI',claim['source']],cwd=ROOT,text=True).strip()
    assert datetime.fromisoformat(committed_at)<datetime.fromisoformat(claim['started_at'])
    for key,value in claim['experiment']['runtime_hashes'].items():
        name='tradingagents/'+('research/'+key[9:] if key.startswith('original/') else 'research_amended/'+key)
        assert sha(subprocess.check_output(['git','show',claim['source']+':'+name],cwd=ROOT))==value
        assert sha((ROOT/name).read_bytes())==value
    for name, value in receipt['output_sha256'].items():
        assert sha((RUN/'outputs'/name).read_bytes()) == value
    inputs = {}
    for name, spec in claim['inputs'].items():
        body = (ROOT/spec['path']).read_bytes()
        assert sha(body) == spec['sha256']
        inputs[name] = json.loads(body)
    assert set(inputs) == {'capture','admission','spot_capture','spot_admission'}
    for capture, admission, count in (('capture','admission',8),('spot_capture','spot_admission',10)):
        rr, aa = inputs[capture]['requests'], inputs[admission]['cells']
        assert len(rr) == len(aa) == count and len({x['id'] for x in rr}) == count
        assert {x['id'] for x in rr} == {x['id'] for x in aa}
        assert all(x['status'] == 'complete' for x in aa)
    archived = {x['id']:x for x in inputs['capture']['requests']}
    spots = {x['id']:x for x in inputs['spot_capture']['requests']}
    output = read(RUN/'outputs/books.json'); summary = read(RUN/'outputs/summary.json')
    assert output['input_errors'] == {}
    data = {}
    for asset in ('BTC','ETH'):
        daily = json.loads(raw(spots[asset.lower()+'-spot']))
        assert len(daily) == 91
        bars(daily, 1775001600000, DAY)
        url=urlsplit(spots[asset.lower()+'-spot']['request_url'])
        assert url.netloc=='api.binance.com' and url.path=='/api/v3/klines'
        assert parse_qs(url.query)['symbol']==[asset+'USDT']
        hours = []
        for month in (5,6):
            key = asset.lower()+f'-2026-{month:02d}'
            zipbytes = raw(archived[key+'-zip']); checksum = raw(archived[key+'-checksum'])
            fn = f'{asset}USDT_260626-1h-2026-{month:02d}.zip'
            url=f'https://data.binance.vision/data/futures/um/monthly/klines/{asset}USDT_260626/1h/{fn}'
            assert archived[key+'-zip']['url']==url and archived[key+'-checksum']['url']==url+'.CHECKSUM'
            assert checksum.decode('ascii').strip() == sha(zipbytes)+'  '+fn
            with zipfile.ZipFile(io.BytesIO(zipbytes)) as z:
                assert z.namelist() == [fn[:-4]+'.csv'] and z.testzip() is None
                rows = list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode('utf-8'))))
            assert rows.pop(0) == 'open_time open high low close volume close_time quote_volume count taker_buy_volume taker_buy_quote_volume ignore'.split()
            assert len(rows) == (744 if month == 5 else 609)
            bars(rows, START if month == 5 else START+31*DAY, HOUR)
            hours.extend(rows)
        selected_spot = [r for r in daily if START <= int(r[0]) < END]
        selected_future = [r for r in hours if START <= int(r[0]) < END]
        assert len(selected_spot) == 56 and len(selected_future) == 1344
        bars(selected_spot, START, DAY); bars(selected_future, START, HOUR)
        for label, source_rows, selected in (('spot',daily,selected_spot),('dated',hours,selected_future)):
            assert output['input_clipping'][asset][label] == {
                'source_rows':len(source_rows),'retained_rows':len(selected),
                'excluded_before_start':sum(int(r[0]) < START for r in source_rows),
                'excluded_at_or_after_end':sum(int(r[0]) >= END for r in source_rows)}
        assert all(D(r[5]) > 0 and D(r[8]) > 0 for r in (selected_spot[0],selected_spot[-1],selected_future[0],selected_future[-1]))
        data[asset] = selected_spot, selected_future
    benchmark = {}
    for asset, (spot, _) in data.items():
        closes = [D(r[4]) for r in spot]
        previous = [D(spot[0][1])] + closes[:-1]
        benchmark[asset] = np.array([float(a/b-1) for a,b in zip(closes,previous)])
    X = np.column_stack([np.ones(N),benchmark['BTC'],benchmark['ETH']])
    assert np.linalg.matrix_rank(X) == 3
    bread = np.linalg.inv(X.T@X)
    cases = {r['id']:r for r in summary['cases']}
    expected_ids = [f'{a.lower()}-{c}-{s}' for a in ('BTC','ETH') for c in (1000,10000) for s in ('base','stress')]
    assert set(cases) == set(output['primary_books']) == set(expected_ids)
    assert [c['id'] for c in receipt['cells']] == expected_ids
    findings = []
    for identity in expected_ids:
        b = output['primary_books'][identity]; report = cases[identity]
        asset, capital, scenario = identity.split('-'); capital = D(capital); asset = asset.upper()
        spot, future = data[asset]
        sf, ff, slip = (D('.001'),D('.0005'),D('.0002')) if scenario == 'base' else (D('.002'),D('.001'),D('.0004'))
        fields(b['costs'],{'spot_fee':sf,'perp_fee':ff,'slippage':slip},identity+'.costs')
        so, fo, sz, fz = D(spot[0][1]),D(future[0][1]),D(spot[-1][4]),D(future[-1][4])
        se, fe, sx, fx = so*(1+slip),fo*(1-slip),sz*(1-slip),fz*(1+slip)
        lot = D('.001') if asset=='BTC' else D('.01')
        q = ((capital*D('.4'))/(lot*(se*(1+sf)+fe*ff))).to_integral_value(rounding=ROUND_FLOOR)*lot
        assert q > 0
        reserve = capital/2
        purchase, sfe, ffe = q*se,q*se*sf,q*fe*ff
        idle = capital-reserve-purchase-sfe-ffe
        assert idle >= capital/10
        initial = {'quantity':q,'spot_quantity':q,'future_quantity':-q,'assumed_common_lot':lot,'spot_entry_price':se,
                   'future_entry_price':fe,'spot_purchase_principal':purchase,'spot_entry_fee':sfe,'future_entry_fee':ffe,
                   'futures_reserve':reserve,'idle_cash':idle}
        fields(b['initial'],initial,identity+'.initial')
        def liquidation(sx, fx):
            proceeds, realized, sfee, ffee = q*sx,q*(fe-fx),q*sx*sf,q*fx*ff
            futures_cash=reserve+realized-ffee
            cash=idle+futures_cash+proceeds-sfee
            return {'spot_exit_price':sx,'future_exit_price':fx,'spot_sale_proceeds':proceeds,'spot_exit_fee':sfee,
                    'future_realized_price_pnl':realized,'future_exit_fee':ffee,'cumulative_funding_cash':0,
                    'futures_cash_after_close':futures_cash,'idle_cash':idle,'final_cash':cash,'cash_profit':cash-capital,
                    'terminal_spot_quantity':0,'terminal_future_quantity':0}
        final=liquidation(sx,fx)
        basis=q*((sz-so)+(fo-fz)); price=q*((sx-se)+(fe-fx)); fees=sfe+ffe+q*sx*sf+q*fx*ff
        final.update(raw_basis_convergence=basis,zero_friction_same_quantity_profit=basis,executed_price_pnl=price,
                     slippage_cost=basis-price,all_fees=fees,cash_profit_from_signed_components=price-fees,cash_reconciliation_difference=0)
        fields(b['final_ledger'],final,identity+'.final')
        assert final['cash_profit'] == price-fees
        trace=b['daily_trace']; assert len(trace)==N
        navs=[]; returns=[]; buffers=[]; peak=capital; dd=D(0);previous=capital
        for day,row in enumerate(trace):
            sc,fc=D(spot[day][4]),D(future[(day+1)*24-1][4]);high=max(D(r[2]) for r in future[day*24:(day+1)*24])
            mtm=q*(fe-fc);value=q*sc;nav=idle+reserve+mtm+value
            pre={'nav':nav,'futures_wallet':reserve,'short_mtm':mtm,'spot_value':value,'idle_cash':idle,
                 'spot_quantity':q,'future_quantity':-q,'net_base_quantity':0,'gross_market_notional':q*(sc+fc),'net_market_notional':q*(sc-fc)}
            expected={**pre,'pre_exit_nav':nav,'spot_close':sc,'future_close':fc,'future_trade_high':high,
                      'funding_cash':0,'cumulative_funding_cash':0,'trade_high_reserve_buffer_proxy':reserve+q*(fe-high)-D('.01')*q*high}
            if day==N-1:
                fields(row['pre_exit_components'],pre,identity+'.pre_exit')
                nav=final['final_cash']
                expected.update(nav=nav,futures_wallet=final['futures_cash_after_close'],short_mtm=0,spot_value=0,
                                spot_quantity=0,future_quantity=0,net_base_quantity=0,gross_market_notional=0,
                                net_market_notional=0,idle_cash=idle+final['spot_sale_proceeds']-final['spot_exit_fee'])
            ret=nav/previous-1;expected['full_capital_daily_return']=ret
            fields(row,expected,identity+f'.day{day}')
            assert row['date']==datetime.fromtimestamp((START+day*DAY)/1000,timezone.utc).date().isoformat()
            eq(row['nav'],D(row['futures_wallet'])+D(row['short_mtm'])+D(row['spot_value'])+D(row['idle_cash']),identity+'.wallet-nav')
            navs.append(nav);returns.append(ret);buffers.append(expected['trade_high_reserve_buffer_proxy'])
            peak=max(peak,nav);dd=max(dd,(peak-nav)/peak);previous=nav
        total=final['cash_profit']/capital
        metrics={'cash_profit':final['cash_profit'],'full_capital_return':total,'annualized_simple_return_365':total*365/N,
                 'max_drawdown':dd,'minimum_trade_high_reserve_buffer_proxy':min(buffers)}
        fields(b['metrics'],metrics,identity+'.metrics');fields(report['metrics'],metrics,identity+'.summarymetrics')
        assert b['metrics']['trade_high_proxy_breach']==any(x<0 for x in buffers)
        logsum=sum((1+x).ln() for x in returns);arithmetic=sum(returns)
        fields(b['convention_diagnostic'],{'log1p_sum':logsum,'arithmetic_daily_simple_return_sum':arithmetic,
              'terminal_simple_return':total,'log_sum_minus_arithmetic_daily_sum':logsum-arithmetic,
              'arithmetic_daily_sum_minus_terminal_simple_return':arithmetic-total},identity+'.conventions')
        for label,multiple in (('half',D('.5')),('double',D(2))):
            stress=liquidation(so*multiple*(1-slip),fo*multiple*(1+slip));h=max(fo,fo*multiple)
            stress.update(quantity=q,price_multiple=multiple,trade_high_reserve_buffer_proxy=reserve+q*(fe-h)-D('.01')*q*h)
            fields(b['quantity_price_stresses'][label],stress,identity+'.stress'+label)
        y=np.array([float(x) for x in returns]); coefficients=np.linalg.lstsq(X,y,rcond=None)[0]
        residual=y-X@coefficients;scores=X*residual[:,None];meat=scores.T@scores
        for lag in range(1,8):
            cross=scores[lag:].T@scores[:-lag];meat+=(1-lag/8)*(cross+cross.T)
        covariance=bread@meat@bread
        width=t.ppf(.9875,N-3)*np.sqrt(np.diag(covariance))
        exposure=report['statistics']['market_exposure']
        assert exposure['status']=='complete' and exposure['observations']==N and exposure['hac_lags']==7 and exposure['individual_confidence']==.975
        for index,key in enumerate(('intercept','btc_beta','eth_beta')):eq(exposure[key],coefficients[index],identity+'.'+key,1e-10)
        for index,key in ((1,'btc_interval'),(2,'eth_interval')):
            for actual,expect in zip(exposure[key],(coefficients[index]-width[index],coefficients[index]+width[index])):eq(actual,expect,identity+'.'+key,1e-10)
        for key in ('expected_return_confidence','power'):assert report['statistics'][key]['status']=='unavailable'
        for key in ('actual_margin_risk','execution'):assert report[key]['status']=='unavailable'
        assert not report['graduation'] and not report['adoption_or_execution_validated']
        assert report['necessary_historical_cash_screen']['case_positive_and_annualized_at_least_3pct']==(total>0 and total*365/N>=D('.03'))
        for rate in ('0','0.03','0.05'):eq(report['cash_benchmarks'][rate],capital*D(rate)*N/365,identity+'.benchmark')
        fields(report,{'raw_basis_convergence':basis,'same_quantity_frictionless_profit':basis,'slippage_cost':basis-price,'commissions':fees},identity+'.decomposition')
        zero_volume=[START+i*HOUR for i,r in enumerate(future) if D(r[5])==0];zero_trades=[START+i*HOUR for i,r in enumerate(future) if D(r[8])==0]
        assert b['held_activity']==report['held_activity']=={'all_hour_count':1344,'zero_volume_hour_count':len(zero_volume),'zero_volume_hour_ids_ms':zero_volume,'zero_trade_hour_count':len(zero_trades),'zero_trade_hour_ids_ms':zero_trades}
        findings.append({'id':identity,'quantity':float(q),'capital':float(capital),'raw_basis_convergence':float(basis),
                         'slippage_cost':float(basis-price),'commissions':float(fees),'cash_profit':float(final['cash_profit']),
                         'full_capital_return':float(total),'descriptive_annualized_return':float(total*365/N),
                         'max_drawdown':float(dd),'minimum_trade_high_reserve_buffer_proxy':float(min(buffers)),
                         'btc_beta':float(coefficients[1]),'btc_interval':exposure['btc_interval'],
                         'eth_beta':float(coefficients[2]),'eth_interval':exposure['eth_interval']})
    for r in summary['cases']:
        group=[x for x in summary['cases'] if x['asset']==r['asset'] and x['capital']==r['capital']]
        assert r['necessary_historical_cash_screen']['same_capital_base_and_stress_pass']==all(x['necessary_historical_cash_screen']['case_positive_and_annualized_at_least_3pct'] for x in group)
    assert summary['primary_count']==8 and summary['additional_portfolio_counterfactual_count']==0 and summary['validated_strategies']==0 and not summary['graduation']
    guard=read(HERE/'dated-amended-resource-execution.json');self_resource=read(RUN/'outputs/resource.json')
    assert guard['child_exit_code']==0 and guard['limit_reason'] is None
    assert guard['peak_sampled_tree_rss_bytes']<guard['rss_limit_bytes']==512*1024**2 and guard['elapsed_seconds']<guard['wall_limit_seconds']==120
    assert self_resource['linux_self_ru_maxrss_kib']*1024<512*1024**2
    from tradingagents.research_amended.verify import verify_run
    verified=verify_run(RUN)
    assert verified['status']=='complete' and verified['cell_count']==8 and verified['output_count']==3
    assert claim['budget_amendment']['original_budget']==4 and claim['budget_amendment']['effective_budget']==5 and claim['budget_amendment']['prior_claim_count']==3 and claim['budget_amendment']['prior_attempts']==1
    return {'status':'PASS','method':'60-digit Decimal raw-source signed cash/wallet reconstruction; independent least-squares and Bartlett HAC7 sandwich with t53 quantile. No economic engine/runner/statistics import, new experiment or network.',
            'source':claim['source'],'registration_sha256':receipt['registration_sha256'],'output_sha256':receipt['output_sha256'],
            'comparisons':comparisons,'maximum_absolute_comparison_error':max_error,'cells':8,'unavailable_cells':0,
            'daily_nav_rows':448,'stress_scenarios_reconstructed':16,'findings':findings,'resource':guard,'structural_verification':verified,
            'scope':'One spent 56-day pre-terminal episode per asset, eight correlated accounting cases. Cash values conditional on fee/lot/fill assumptions; no expected-return or power inference. Trade-high reserve is a nonconservative proxy.',
            'not_verified':['Actual fees/lots/eligibility/fills','Actual mark/maintenance/liquidation path','Expiry settlement','Fresh confirmation or expected profitability','External backup timing or remote equality','Economic outcomes before failed receipts beyond preserved records']}


if __name__=='__main__':
    result=check()
    with (HERE/'dated-amended-review.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'comparisons':result['comparisons'],'maximum_error':result['maximum_absolute_comparison_error'],'findings':result['findings']}))
