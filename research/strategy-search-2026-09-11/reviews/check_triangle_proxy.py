"""Independent Decimal reconstruction of the saved eight static proxy cases.

No producer engine/runner import and no network or new parameter selection.
The separate independent source checker is reused only for six raw schemas.
"""
import base64
from decimal import Decimal as D, localcontext
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
REVIEW=Path(__file__).resolve().parent
RUN=ROOT/'research_runs/triangle-proxy-20260911'
PARENT=ROOT/'research_runs/triangle-inputs-20260911'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())
def committed(commit,path):return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)


def check():
    spec=importlib.util.spec_from_file_location('independent_triangle_sources',REVIEW/'check_triangle_inputs.py')
    independent=importlib.util.module_from_spec(spec);spec.loader.exec_module(independent)
    source_check=independent.check()
    claim,done=read(RUN/'claim.json'),read(RUN/'complete.json')
    assert not (RUN/'failed.json').exists()
    commit=claim['source'];assert commit==done['source']==claim['design_source']
    assert done['claim_sha256']==sha((RUN/'claim.json').read_bytes())
    gate_raw=committed(commit,claim['registration']);gate=json.loads(gate_raw)
    assert sha(gate_raw)==claim['registration_sha256']==done['registration_sha256']
    exp=gate['experiments'][claim['experiment_id']]
    assert exp==claim['experiment'] and exp['parent']=='triangle-inputs-20260911'
    assert exp['stage']=='development' and exp['reuse']=='exploratory' and exp['selection'] is None
    assert claim['family']==gate['families'][exp['family']]
    old=json.loads(committed(commit,'research/strategy-search-2026-09-11/gates-triangle-inputs.json'))
    for group in ['families','datasets','experiments']:
        assert all(gate[group][k]==v for k,v in old[group].items())
    pins={**exp['source_files'],exp['charter']['path']:exp['charter']['sha256']}
    pins.update({'tradingagents/research/'+k:v for k,v in exp['runtime_hashes'].items()})
    for path,h in pins.items():assert sha(committed(commit,path))==h,path
    for info in exp['inputs'].values():assert sha((ROOT/info['path']).read_bytes())==info['sha256']
    assert exp['inputs']['capture']['path']=='research_runs/triangle-inputs-20260911/outputs/triangle-capture.json'
    assert exp['inputs']['admission']['path']=='research_runs/triangle-inputs-20260911/outputs/triangle-admission.json'
    raw=(RUN/'outputs/proxy.json').read_bytes();result=json.loads(raw)
    assert len(raw)<=2*1024**2
    assert exp['outputs']==['proxy.json'] and set(done['output_sha256'])=={'proxy.json'}
    assert {p.name for p in (RUN/'outputs').iterdir()}=={'proxy.json'}
    assert sha(raw)==done['output_sha256']['proxy.json']
    parent=read(PARENT/'outputs/triangle-capture.json');admission=read(PARENT/'outputs/triangle-admission.json')
    receipts={r['id']:r for r in parent['requests']};states={r['id']:r for r in admission['cells']}
    assert len(receipts)==len(states)==6 and set(result['source_availability'])==set(receipts)
    required=['triangle-exchange-info','triangle-book-ticker']
    assert result['required_source_ids']==required and result['all_six_source_cells_available'] is True
    for identifier,receipt in receipts.items():
        actual=result['source_availability'][identifier]
        assert actual=={'id':identifier,'required_for_static_proxy':identifier in required,'parent_status':'complete',
                       'request_utc':receipt['request_utc'],'retrieval_utc':receipt['retrieval_utc'],
                       'raw_integrity_status':'complete','schema_status':'complete','status':'complete'}
    ticker=receipts['triangle-book-ticker'];quotes={r['symbol']:r for r in json.loads(base64.b64decode(ticker['body_base64'],validate=True))}
    assert set(quotes)=={'BTCUSDT','ETHUSDT','ETHBTC'}
    for key in ['request_utc','retrieval_utc']:assert result['ticker_capture_clocks'][key]==ticker[key]
    expected_ids=[f'{direction}-{capital}-{label}' for direction in ('btc-eth','eth-btc') for capital in (1000,10000) for label in ('zero-fee','10bp')]
    assert exp['cells']==expected_ids and set(result['cases'])==set(expected_ids)
    assert result['cells']==done['cells']==[{'id':identity,'status':'complete'} for identity in expected_ids]
    assert result['case_count']==done['cell_count']==8 and done['unavailable_count']==0
    assert result['graduation'] is False
    expected_limits={'expected_return_confidence','power','market_beta','execution_frequency','annual_economic_relevance'}
    assert set(result['inference_limits'])==expected_limits
    assert all(r['status']=='unavailable' for r in result['inference_limits'].values())
    errors=[];summaries=[]
    def same(observed,expected):
        assert math.isfinite(observed)
        error=abs(D(str(observed))-expected);errors.append(error)
        assert error<D('1e-8'),(observed,str(expected))
    with localcontext() as context:
        context.prec=75
        ask_btc=D(quotes['BTCUSDT']['askPrice']);bid_btc=D(quotes['BTCUSDT']['bidPrice'])
        ask_eth=D(quotes['ETHUSDT']['askPrice']);bid_eth=D(quotes['ETHUSDT']['bidPrice'])
        ask_cross=D(quotes['ETHBTC']['askPrice']);bid_cross=D(quotes['ETHBTC']['bidPrice'])
        gross={'btc-eth':bid_eth/(ask_btc*ask_cross),'eth-btc':bid_cross*bid_btc/ask_eth}
        product_expected=(bid_btc/ask_btc)*(bid_eth/ask_eth)*(bid_cross/ask_cross)
        assert abs(gross['btc-eth']*gross['eth-btc']-product_expected)<D('1e-65') and product_expected<=1
        routes={'btc-eth':[('BTCUSDT','buy','USDT','BTC'),('ETHBTC','buy','BTC','ETH'),('ETHUSDT','sell','ETH','USDT')],
                'eth-btc':[('ETHUSDT','buy','USDT','ETH'),('ETHBTC','sell','ETH','BTC'),('BTCUSDT','sell','BTC','USDT')]}
        for direction in routes:
            for capital in (1000,10000):
                for label,fee in [('zero-fee',D(0)),('10bp',D('.001'))]:
                    identity=f'{direction}-{capital}-{label}';saved=result['cases'][identity]
                    C=D(capital);G=gross[direction];N=G*(1-fee)**3
                    wealth=C*N;profit=wealth-C;fee_total=C*G-wealth
                    assert saved['status']=='conditional_full_notional_proxy'
                    assert saved['direction']==direction and saved['initial_capital_usdt']==capital
                    same(saved['received_asset_fee_rate_per_leg'],fee)
                    assert saved['currency_path']==[routes[direction][0][2],*[r[3] for r in routes[direction]]]
                    wallets={'USDT':C,'BTC':D(0),'ETH':D(0)};fees=[];size_flags=[];flows=[]
                    for index,(symbol,side,spent_asset,received_asset) in enumerate(routes[direction]):
                        row=saved['trace'][index];before=dict(wallets)
                        price=D(quotes[symbol]['askPrice' if side=='buy' else 'bidPrice'])
                        spent=wallets[spent_asset]
                        received=spent/price if side=='buy' else spent*price
                        commission=received*fee;net=received-commission
                        base_quantity=received if side=='buy' else spent
                        depth=D(quotes[symbol]['askQty' if side=='buy' else 'bidQty'])
                        size_flags.append(base_quantity<=depth)
                        wallets[spent_asset]=D(0);wallets[received_asset]+=net
                        delta={asset:wallets[asset]-before[asset] for asset in wallets};flows.append(delta)
                        # Closed-form USDT equivalent of the actual fee on this leg.
                        fee_usdt=C*G*fee*(1-fee)**index;fees.append(fee_usdt)
                        assert row['leg']==index+1 and row['symbol']==symbol and row['side']==side
                        assert row['spent_asset']==spent_asset and row['acquired_asset']==row['fee_asset']==received_asset
                        values={'execution_side_price':price,'spent_quantity':spent,'acquired_gross_quantity':received,
                                'fee_quantity':commission,'acquired_net_quantity':net,'executed_base_quantity_before_fee':base_quantity,
                                'displayed_best_base_quantity':depth,'fee_usdt_equivalent_at_downstream_gross_quotes':fee_usdt}
                        for key,value in values.items():same(row[key],value)
                        assert row['displayed_best_size_sufficient']==size_flags[-1]
                        for key,mapping in [('wallets_before',before),('wallets_after',wallets),('signed_currency_flows',delta)]:
                            assert set(row[key])==set(wallets)
                            for asset,value in mapping.items():same(row[key][asset],value)
                    assert abs(wallets['USDT']-wealth)<D('1e-60') and wallets['BTC']==wallets['ETH']==0
                    assert abs(sum(fees)-fee_total)<D('1e-60')
                    for asset in wallets:
                        same(saved['initial_wallets'][asset],C if asset=='USDT' else D(0))
                        same(saved['terminal_wallets'][asset],wallets[asset])
                        same(saved['currency_flow_reconciliation'][asset],D(0))
                    values={'gross_roundtrip_factor':G,'after_fee_roundtrip_factor':N,'gross_terminal_usdt':C*G,
                            'terminal_usdt':wealth,'gross_cash_profit_usdt':C*(G-1),'cash_profit_usdt':profit,
                            'three_fees_terminal_usdt_equivalent':fee_total,'fee_decomposition_difference_usdt':D(0)}
                    for key,value in values.items():same(saved[key],value)
                    shadow=C*N.ln();diagnostic=saved['convention_diagnostic']
                    same(diagnostic['capital_times_log_factor_usdt'],shadow)
                    same(diagnostic['actual_simple_cash_profit_usdt'],profit)
                    same(diagnostic['log_shadow_minus_actual_usdt'],shadow-profit)
                    assert shadow<=profit
                    assert saved['all_displayed_best_sizes_sufficient']==all(size_flags)
                    screen=saved['necessary_after_10bp_screen']
                    assert screen['status']==('not_applicable' if fee==0 else 'evaluated')
                    assert screen['positive']==(None if fee==0 else profit>0)
                    assert saved['graduation'] is False and saved['execution']['status']=='unavailable'
                    assert saved['inference_limits']==result['inference_limits']
                    assert 'not an upper bound on wallet wealth' in saved['full_notional_scope']
                    assert 'factor at or below one' in saved['unit_factor_scope']
                    summaries.append({'id':identity,'gross_factor':str(G),'after_fee_factor':str(N),
                        'gross_profit_usdt':str(C*(G-1)),'net_profit_usdt':str(profit),'terminal_usdt':str(wealth),
                        'fee_usdt_equivalents_by_leg':list(map(str,fees)),'three_fee_usdt_drag':str(fee_total),
                        'size_flags':size_flags,'log_shadow_minus_cash_usdt':str(shadow-profit),'positive_net_proxy':profit>0})
    resources=read(REVIEW/'triangle-proxy-resource-execution.json')
    assert resources['child_exit_code']==0 and resources['limit_reason'] is None
    assert resources['peak_sampled_tree_rss_bytes']<=512*1024**2 and resources['elapsed_seconds']<=120
    return {'status':'pass','source':commit,'registration_sha256':sha(gate_raw),'output_sha256':sha(raw),
            'cells':8,'outputs':1,'output_bytes':len(raw),'numeric_comparisons':len(errors),'maximum_absolute_numeric_difference':str(max(errors)),
            'independent_arithmetic_precision_decimal_digits':75,'source_schema_reconstruction_status':source_check['status'],
            'independent_source_checker_sha256':sha((REVIEW/'check_triangle_inputs.py').read_bytes()),
            'all_six_source_cells_available':True,'ticker_capture_clocks':result['ticker_capture_clocks'],
            'reconstructed_cases':summaries,'resource_report':resources,'family':claim['family'],
            'financial_verdict':'BTC-first has a small positive zero-fee proxy erased by assumed three 10bp received-asset fees; ETH-first is negative before fees. No case supports execution or graduation.',
            'untested':['actual fees and fee assets','simultaneity, quote age, latency and fills','lot/dust/notional rules and account access',
                        'expected return, beta, power, annual frequency and actual inventory-risk outcomes','external backup']}


if __name__=='__main__':
    report=check()
    (REVIEW/'triangle-proxy-review.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ['status','cells','numeric_comparisons','maximum_absolute_numeric_difference','financial_verdict']}))
