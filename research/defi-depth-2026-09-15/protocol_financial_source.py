"""Unadmitted F1/F3 daily-source collector; no CLI and no automatic acquisition.

Source configuration/ownership and complete lifecycle packet must be committed
and independently reviewed before this injected-transport interface may be used.
"""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

P=module('future_protocol_source_policy','financial_source_policy.py')
F2=module('future_retained_oracle_encoding','f2_source.py')
L=module('future_lending_integer_checks','lending_math.py')
LP=module('future_lp_qualification','lp_book.py')
O=module('future_canonical_price_ownership','source_ownership.py')
BOUNDARIES=('2025-09-02','2026-09-01')
BOUNDARY_KEYS={'F1':('usdc-decimals','aave-pool-identity','aave-underlying','usdc-code','aave-pool-code','atoken-code'),
               'F3':('usdc-decimals','weth-decimals','lp-factory','lp-token0','lp-token1','lp-fee','lp-spacing','lp-max-liquidity','lp-lower','lp-upper','lp-code','weth-code','usdc-code')}
DAILY={'F1':('aave-income','aave-config','aave-contract-cash','aave-scaled-supply','aave-total-supply'),
       'F3':('lp-slot0','lp-liquidity','lp-fee0','lp-fee1')}


def request_inventory(design):
    """Logical observation inventory; all3 physical slots have durable outputs."""
    requests=[];cells=[];outputs=['source-summary.json']
    keys=[]
    for day in design['days']:
        date=day['date'];prefix=date+'-';ownership=design['ownership'][date]
        cells.extend(prefix+k for k in ('actual-clock','oracle-prices','model-row'))
        if ownership['header']=='new':requests.append((prefix+'header','eth_getBlockByNumber'))
        if ownership['prices']=='new':requests.append((prefix+'oracle-prices','eth_call'))
        actions=design['daily_actions']+(design['boundary_actions'] if date in BOUNDARIES else [])
        for action in actions:
            cells.append(prefix+action['key'])
            if ownership['fields'][action['key']]=='new':requests.append((prefix+action['key'],action['method']))
        if design['recipe']=='F1':cells.append(prefix+'supply-identity')
        outputs.append(prefix+'source.json')
        keys.append(date)
    if len(set(keys))!=len(keys):raise ValueError('duplicate source calendar')
    ids=[r[0] for r in requests]
    if len(set(ids))!=len(ids):raise ValueError('duplicate logical source IDs')
    for rid,method in requests:
        for i in (1,2,3):outputs.extend([f'{rid}-try{i}-attempt.json',f'{rid}-try{i}-receipt.json'])
    return {'requests':requests,'cells':cells,'outputs':outputs,
            'max_physical_requests':3*len(requests),'worst_case_raw_bytes':sum(3*P.CAPS[method] for _,method in requests)}


def validate_design(design,context):
    from datetime import date,timedelta
    if design['recipe'] not in DAILY:raise ValueError('fixed financial recipe required')
    if tuple(a['key'] for a in design['boundary_actions'])!=BOUNDARY_KEYS[design['recipe']]:raise ValueError('boundary identity inventory differs')
    if tuple(a['key'] for a in design['daily_actions'])!=DAILY[design['recipe']]:raise ValueError('daily field inventory differs')
    expected=[(date(2025,9,1)+timedelta(days=i)).isoformat() for i in range(366)]
    if [d['date'] for d in design['days']]!=expected:raise ValueError('fixed annual source calendar required')
    order=['2025-09-01','2025-09-02','2026-09-01']+[d for d in expected if d not in ('2025-09-01','2025-09-02','2026-09-01')]
    if design['acquisition_order']!=order:raise ValueError('frozen endpoint-first chronological acquisition required')
    if set(design['ownership'])!=set(expected):raise ValueError('complete first-acquisition ownership map required')
    for day in design['days']:
        expected_stamp=int(datetime.fromisoformat(day['date']).replace(tzinfo=timezone.utc).timestamp())
        if type(day['timestamp']) is not int or day['timestamp']!=expected_stamp:
            raise ValueError('calendar label must bind its exact midnight UTC target')
        if type(day['candidate_block']) is not int or day['candidate_block']<0:
            raise ValueError('candidate height must be an exact nonnegative integer')
        d=day['date'];owner=design['ownership'][d];retained=context.get(d,{})
        for field in ('header','prices'):
            if owner[field] not in ('retained','new','unavailable'):raise ValueError('invalid source ownership')
            if owner[field]=='retained' and field not in retained:raise ValueError('retained source bytes/qualification absent')
            if owner[field]=='new' and field in retained:raise ValueError('new acquisition would repeat retained source')
        if owner['prices']=='retained':
            if owner['header']!='retained':raise ValueError('retained prices need exact retained canonical block')
            if retained['prices']['block_hash']!=retained['header']['hash']:raise ValueError('retained price/header hash differs')
        if owner['header']=='new' and owner.get('first_header_acquisition_proved') is not True:
            raise ValueError('unsent-header ownership not proved')
        if owner['prices']=='new' and owner.get('first_overlapping_price_fields_proved') is not True:
            raise ValueError('unsent overlapping oracle-field ownership not proved')
        actions=design['daily_actions']+(design['boundary_actions'] if d in BOUNDARIES else [])
        if set(owner['fields'])!={a['key'] for a in actions}:raise ValueError('complete per-field ownership required')
        for action in actions:
            key=action['key'];role=owner['fields'][key];prior=retained.get('fields',{}).get(key)
            if role not in ('retained','new','unavailable'):raise ValueError('invalid field acquisition ownership')
            if role=='retained':
                if not prior or prior['block_hash']!=retained['header']['hash'] or prior['action']!=action:
                    raise ValueError('retained field action/block binding differs')
            elif role=='new' and prior:raise ValueError('new field would repeat retained observation')
    canonical=O.price_fields(design['prior_request_keys'])
    if canonical!=design['price_field_history']:raise ValueError('canonical overlapping price exclusions differ')
    inv=request_inventory(design)
    for key in ('max_physical_requests','worst_case_raw_bytes'):
        if design[key]!=inv[key]:raise ValueError('source reservation differs from complete physical inventory')
    return inv


def unavailable(cid,reason):return {'id':cid,'status':'unavailable','reason':reason}


def capture(design,context,publish,fetch=P.T.public_post,**clocks):
    validate_design(design,context)
    source=P.Source(design,publish,fetch,**clocks)
    days={d['date']:d for d in design['days']};daily=[];all_cells=[];witnesses={};model_inputs={}
    for date in design['acquisition_order']:
        day=days[date];prefix=date+'-';owner=design['ownership'][date];local=[];retained=context.get(date,{})
        if owner['header']=='retained':
            block=retained['header']
            if block['number']!=day['candidate_block'] or not day['timestamp']-1<=block['timestamp']<=day['timestamp']:
                raise ValueError('retained actual-clock qualification differs')
            header={'id':prefix+'actual-clock','status':'complete','value':block,'source_role':'qualified retained raw header at its actual clock'}
        elif owner['header']=='new':
            raw=source.request(prefix+'header','eth_getBlockByNumber',[hex(day['candidate_block']),False],
                lambda value,observed:P.actual_clock_header(value,day,observed))
            header={**raw,'id':prefix+'actual-clock'}
            block=raw['value'] if raw['status']=='complete' else None
        else:
            block=None;header=unavailable(prefix+'actual-clock',owner.get('header_unavailable_reason','Inherited header unavailable; no retry'))
        local.append(header)
        tag={'blockHash':block['hash'],'requireCanonical':True} if block else None
        if owner['prices']=='retained':
            prices={a:retained['prices']['prices_atoms_1e8'][a] for a in ('ETH','USDC')}
            if any(type(v) is not int or v<=0 for v in prices.values()):raise ValueError('invalid retained price units')
            price_row={'id':prefix+'oracle-prices','status':'complete','value':prices,'source_role':'retained F2/F1 same-block oracle vector'}
        elif owner['prices']=='new':
            if block:O.assert_new_price_fields(block['hash'],[F2.TOKENS[a] for a in ('ETH','USDC')],design['price_field_history'])
            price_row=source.request(prefix+'oracle-prices','eth_call',
              [{'to':F2.ORACLE,'data':F2.encode_prices(['ETH','USDC'])},tag],
              lambda value,observed:F2.parse_prices(value,['ETH','USDC']),dependency=None if block else 'actual-clock header unavailable')
        else:price_row=unavailable(prefix+'oracle-prices',owner.get('prices_unavailable_reason','Inherited overlapping price field unavailable; no retry'))
        local.append(price_row)
        values={}
        actions=design['daily_actions']+(design['boundary_actions'] if date in BOUNDARIES else [])
        for action in actions:
            method=action['method']
            params=[{'to':action['to'],'data':action['data']},tag] if method=='eth_call' else [action['to'],tag]
            role=owner['fields'][action['key']]
            if role=='retained':
                row={'id':prefix+action['key'],'status':'complete','value':retained['fields'][action['key']]['value'],
                     'source_role':'qualified retained same-block same-action source'}
            elif role=='unavailable':
                row=unavailable(prefix+action['key'],'Inherited field failed/uncertain; no new attempt or alias')
            else:
                row=source.request(prefix+action['key'],method,params,
                    lambda value,observed,action=action:P.Q.old.parse_action(value,action),
                    dependency=None if block else 'actual-clock header unavailable')
            local.append(row);values[action['key']]=row
        if date in BOUNDARIES:
            witnesses[date]={a['key']:values[a['key']] for a in design['boundary_actions']}
        try:
            if design['recipe']=='F1':
                needed=('aave-income','aave-scaled-supply','aave-total-supply')
                if any(values[k]['status']!='complete' for k in needed):raise ValueError('scaled/index source identity inputs unavailable')
                income,scaled,total=[values[k]['value']['words'][0] for k in needed]
                L.index(income);residual=total-L.ray_mul(scaled,income)
                if abs(residual)>1:raise ValueError('scaled/index aggregate identity differs by more than one atom')
                supply={'id':prefix+'supply-identity','status':'complete','value':{'residual_atoms':residual}}
                local.append(supply)
        except (ValueError,TypeError,KeyError) as exc:
            supply=unavailable(prefix+'supply-identity',str(exc));local.append(supply)
        complete=block is not None and price_row['status']=='complete' and all(values[k]['status']=='complete' for k in DAILY[design['recipe']])
        if design['recipe']=='F1':complete=complete and supply['status']=='complete'
        record={'date':date,'block':block,'oracle_prices':price_row,'fields':values,
                'daily_source_complete':complete,'supply_identity':supply if design['recipe']=='F1' else None}
        model_inputs[date]=record
        # Boundary identity across the interval is assessed after collection; no
        # provisional true flag implies final source-model qualification here.
        local.append({'id':prefix+'model-row','status':'complete' if complete else 'unavailable',
                      'reason':None if complete else 'One or more daily model prerequisites unavailable',
                      'boundary_semantics_and_implementation_not_proved':True})
        all_cells.extend(local);daily.append(record)
        publish(prefix+'source.json',{'day':day,'cells':local,'model_inputs':record,
                                      'physical_requests':source.attempts,'raw_bytes':source.raw_bytes,'endpoint_stop':source.stopped})
        print(json.dumps({'date':date,'recipe':design['recipe'],'daily_source_complete':complete,
                          'physical_requests':source.attempts,'raw_bytes':source.raw_bytes,'endpoint_stop':source.stopped}),flush=True)
    required_witness_keys=[a['key'] for a in design['boundary_actions']]
    witness_complete=all(date in witnesses and all(witnesses[date][k]['status']=='complete' for k in required_witness_keys) for date in BOUNDARIES)
    codes_stable=True
    if witness_complete:
        for action in design['boundary_actions']:
            if action['method']=='eth_getCode':
                k=action['key']
                if witnesses[BOUNDARIES[0]][k]['value']!=witnesses[BOUNDARIES[1]][k]['value']:codes_stable=False
    source_complete=witness_complete and codes_stable and all(r['daily_source_complete'] for r in daily)
    summary={'status':'complete' if source_complete else 'unavailable','rows':sorted(daily,key=lambda r:r['date']),
             'boundary_identity_witnesses_complete':witness_complete,'boundary_code_witnesses_equal':codes_stable if witness_complete else None,
             'physical_requests':source.attempts,'raw_bytes':source.raw_bytes,'endpoint_stop':source.stopped,
             'scope':'conditional fixed actual-clock model observations; no nearest-bracket, deployed-semantics, counterfactual-path or execution proof'}
    publish('source-summary.json',summary)
    return summary,all_cells
