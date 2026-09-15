"""Unadmitted F1/F3 financial output routing; no empirical CLI or implicit run."""
from datetime import datetime,timezone
from fractions import Fraction as F
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

L=module('future_result_lending','lending_book.py')
LP=module('future_result_lp','lp_book.py')
C=module('future_result_wallet_controls','wallet_controls.py')
W=L.W
YEARS=('2024','2025','2026')
SCENARIOS=tuple(W.SCENARIOS)
BASELINES=['B'+str(i) for i in range(10)]+['wallet-cash','wallet-ETH25']


def policies(recipe):
    if recipe=='F1':return ('F1',)+C.POLICIES
    if recipe=='F3':return LP.POLICIES+C.POLICIES
    raise ValueError('fixed F1 or F3 recipe required')


def manifests(recipe):
    cells=[];outputs=['financial-summary.json']
    for year in YEARS:
        for policy in policies(recipe):
            for scenario in SCENARIOS:
                cid=f'{year}-{policy.lower()}-{scenario}';cells.append(cid)
                outputs.extend([cid+'-attempt.json',cid+'.json'])
        if recipe=='F1':
            for name in ('strict-entry-feasibility','opportunity-ceiling'):
                cid=year+'-'+name;cells.append(cid);outputs.extend([cid+'-attempt.json',cid+'.json'])
    for scenario in SCENARIOS:
        cells.extend('D-'+scenario+'-'+name for name in BASELINES+(['matched-entry-inventory'] if recipe=='F3' else []))
    cells.extend(['boundary-source-model','primary-decision','implementation','confirmation'])
    return cells,outputs


def unavailable(reason):return {'status':'unavailable','reason':reason,'implementation_admitted':False,'promotion_admitted':False}


def witnessed(summary):
    return summary['boundary_identity_witnesses_complete'] is True and summary['boundary_code_witnesses_equal'] is True


def prices(record):
    if record['block'] is None or record['oracle_prices']['status']!='complete':raise ValueError('qualified same-block dollar marks unavailable')
    values=record['oracle_prices']['value']
    if any(type(values[a]) is not int or values[a]<=0 for a in ('ETH','USDC')):raise ValueError('positive oracle price integer units required')
    return {a:F(values[a],10**8) for a in ('ETH','USDC')}


def word(record,key,index=0):
    field=record['fields'][key]
    if field['status']!='complete':raise ValueError('source field unavailable: '+key)
    return field['value']['words'][index]


def build_wallet_panel(summary):
    return [{'date':r['date'],'prices':prices(r)} for r in summary['rows']]


def lending_row(record,qualified,*,ceiling_role=None):
    row={'date':record['date'],'source_model_qualified':qualified,'source_block':record['block']}
    if ceiling_role!='entry':row['prices']=prices(record)
    if ceiling_role!='inception':
        if record['supply_identity']['status']!='complete':raise ValueError('scaled/index identity unavailable')
        row['income']=word(record,'aave-income')
    if ceiling_role is None:
        row.update(config=word(record,'aave-config'),contract_cash=word(record,'aave-contract-cash'),
                   scaled_supply=word(record,'aave-scaled-supply'),debt_bound_qualified=False)
    return row


def build_candidate_panel(summary,recipe):
    if summary['status']!='complete' or not witnessed(summary):raise ValueError('complete annual conditional source-model prerequisites unavailable')
    if recipe=='F1':return [lending_row(r,True) for r in summary['rows']]
    panel=[]
    for record in summary['rows']:
        p=prices(record);p['WETH']=p['ETH']
        slot=[word(record,'lp-slot0',i) for i in range(7)]
        row={'date':record['date'],'prices':p,'source_block':record['block'],'sqrt_price':slot[0],'tick':slot[1],'unlocked':slot[6],
             'liquidity':word(record,'lp-liquidity'),'growth0':word(record,'lp-fee0'),'growth1':word(record,'lp-fee1'),
             'source_model_qualified':True}
        if record['date']=='2025-09-02':
            row.update(lower_gross=word(record,'lp-lower'),upper_gross=word(record,'lp-upper'),max_tick_liquidity=word(record,'lp-max-liquidity'))
        panel.append(row)
    return panel


def financial(summary,benchmarks,recipe,publish):
    all_cells=[];results={};defect=None;auxiliary={};comparisons={}
    candidate_panel=wallet_panel=None
    try:wallet_panel=build_wallet_panel(summary)
    except (ValueError,KeyError,TypeError) as exc:wallet_reason=str(exc)
    try:candidate_panel=build_candidate_panel(summary,recipe)
    except (ValueError,KeyError,TypeError) as exc:candidate_reason=str(exc)
    boundary_ok=witnessed(summary)
    all_cells.append({'id':'boundary-source-model','status':'complete'} if boundary_ok else
                     {'id':'boundary-source-model',**unavailable('Entry/terminal identity/code model witness unavailable or changed')})

    def save(cid,out):
        publish(cid+'.json',out)
        all_cells.append({'id':cid,'status':out['status'],**({'reason':out['reason']} if out['status']!='complete' else {})})

    def intent(cid,attempted,reason,role):
        publish(cid+'-attempt.json',{'id':cid,'attempted':attempted,'reason':reason,'role':role,
                                    'started_utc':datetime.now(timezone.utc).isoformat(),'capital_usd':10000})

    for year in YEARS:
        if recipe=='F1':
            for role in ('strict-entry-feasibility','opportunity-ceiling'):
                cid=year+'-'+role;inputs=None;reason=None
                if year!='2026':reason='Earlier fixed annual cohort prerequisites unavailable; no backfill'
                elif defect:reason='Earlier measurement defect: '+defect
                elif not boundary_ok:reason='Boundary model identity witnesses unavailable'
                else:
                    try:
                        rows={r['date']:r for r in summary['rows']}
                        if role=='strict-entry-feasibility':
                            entry=lending_row(rows['2025-09-02'],True,ceiling_role='entry')
                            entry.update(config=word(rows['2025-09-02'],'aave-config'),
                                         scaled_supply=word(rows['2025-09-02'],'aave-scaled-supply'),debt_bound_qualified=False)
                            inputs=(prices(rows['2025-09-01']),entry)
                        else:
                            inputs=[lending_row(rows[d],True,ceiling_role=r) for d,r in
                              [('2025-09-01','inception'),('2025-09-02','entry'),('2026-09-01','terminal')]]
                    except (ValueError,KeyError,TypeError) as exc:reason='Endpoint prerequisites unavailable: '+str(exc)
                intent(cid,reason is None,reason,role)
                if reason:out=unavailable(reason)
                else:
                    try:
                        if role=='opportunity-ceiling':out={**L.opportunity_ceiling(inputs),'status':'complete'}
                        else:
                            p0,entry=inputs
                            usdc=W.floor((W.CAPITAL-F(W.RESERVE,10**18)*p0['ETH'])/p0['USDC']*10**6)
                            if usdc<=0:raise L.FinancialUnavailable('initial gas exhausts capital')
                            scaled,check=L.entry_preview(usdc*7//10,entry)
                            out={'status':'complete','scaled_atoms':scaled,'cap_check':check,
                                 'scope':'Strict conditional model entry feasibility only; no deployed or executable admission'}
                    except L.FinancialUnavailable as exc:out=unavailable(str(exc))
                    except (ValueError,ArithmeticError) as exc:
                        defect=type(exc).__name__+': '+str(exc);out=unavailable('Measurement failure: '+defect)
                save(cid,out)
                if year=='2026':auxiliary[role]=out
        for policy in policies(recipe):
            for scenario in SCENARIOS:
                cid=f'{year}-{policy.lower()}-{scenario}'
                panel=wallet_panel if policy in C.POLICIES else candidate_panel
                reason=('Earlier fixed annual cohort prerequisites unavailable; no backfill' if year!='2026' else
                        ('Earlier measurement defect: '+defect if defect else
                         (None if panel is not None else ('Wallet source unavailable: '+wallet_reason if policy in C.POLICIES else 'Candidate source unavailable: '+candidate_reason))))
                intent(cid,reason is None,reason,policy+' '+scenario)
                if reason:out=unavailable(reason)
                else:
                    progress={}
                    engine=C if policy in C.POLICIES else (L if recipe=='F1' else LP)
                    try:
                        if engine is L:result=L.run_book(panel,scenario,progress,cap_assumption='assume-cap-for-diagnostic')
                        else:result=engine.run_book(panel,policy,scenario,progress)
                        out={**result,'status':'complete'}
                    except engine.FinancialUnavailable as exc:
                        out={**unavailable('Conditional feasibility unavailable: '+str(exc)),'partial':engine.partial_snapshot(progress)}
                    except (ValueError,ArithmeticError) as exc:
                        defect=type(exc).__name__+': '+str(exc)
                        out={**unavailable('Financial measurement failure: '+defect),'partial':engine.partial_snapshot(progress)}
                save(cid,out)
                if year=='2026':results[(policy,scenario)]=out
    def exact_profit(result):
        exact=result.get('exact_net_cash_profit')
        return F(exact['numerator'],exact['denominator']) if exact else F(result['net_cash_profit_usd'])
    for scenario in SCENARIOS:
        candidate=results[(recipe,scenario)];contrasts={}
        for name in BASELINES+(['matched-entry-inventory'] if recipe=='F3' else []):
            other=benchmarks[name][scenario] if name.startswith('B') else results[(name,scenario)]
            if candidate['status']!='complete' or other['status']!='complete':row=unavailable('Fixed candidate or comparator unavailable')
            else:
                difference=exact_profit(candidate)-exact_profit(other)
                row={'status':'complete','difference_usd':W.render(difference),'difference_exact':W.fraction_record(difference),
                     'incremental_floor_pass_conditional':difference>=200,
                     'benchmark_numeric_risk_pass':other.get('numerical_risk_pass_conditional',other.get('conditional_numeric_risk_pass')),
                     'basis':'retained CEX book; oracle/bar/route basis differs' if name.startswith('B') else 'same-price same-capital fixed wallet control'}
            contrasts[name]=row;all_cells.append({'id':'D-'+scenario+'-'+name,'status':row['status'],
                **({'reason':row['reason']} if row['status']!='complete' else {})})
        comparisons[scenario]=contrasts
    candidate=results[(recipe,'primary')]
    known=[r for r in comparisons['primary'].values() if r['status']=='complete' and r['benchmark_numeric_risk_pass'] is True]
    numeric=candidate['status']=='complete' and candidate['absolute_floor_pass_conditional'] and candidate['numerical_risk_pass_conditional'] and all(r['incremental_floor_pass_conditional'] for r in known)
    decision={**unavailable('Actual B1, executable funding/exit routes, protocol counterfactual behavior, lock/horizon cash and fresh confirmation unavailable'),
              'primary_scenario':'primary','known_comparator_numerical_pass_only':numeric,'known_risk_eligible_comparator_count':len(known),
              'strict_entry_model_available':auxiliary.get('strict-entry-feasibility',{}).get('status')=='complete' if recipe=='F1' else None,
              'absolute_target_usd':1000,'incremental_target_usd':200,'all_fixed_comparators_retained':True,
              'no_metric_or_ceiling_rescue':True,'source_clock':'observed canonical block within1second before nominal daily target'}
    for name in ('primary-decision','implementation','confirmation'):all_cells.append({'id':name,**unavailable(decision['reason'])})
    publish('financial-summary.json',{'recipe':recipe,'cells':all_cells,'comparisons':comparisons,'primary_decision':decision,
                                     'auxiliary':auxiliary,'measurement_defect':defect,
                                     'scope':'Single exposed financial recipe with fixed assumption diagnostics; no strategy validation'})
    expected,_=manifests(recipe)
    if len(all_cells)!=len(expected) or {r['id'] for r in all_cells}!=set(expected):raise ValueError('financial denominator differs')
    return all_cells
