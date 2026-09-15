"""Serialize the funded ledger even if higher-level event valuation has failed."""

def snapshot(book, initial_atoms, assets):
    names={key:asset for asset,key in assets.items()}
    replay=dict(initial_atoms)
    receipts=[]
    for event in book.events:
        deltas=[]
        for identity,delta in event['deltas'].items():
            if delta!=int(delta):raise ValueError('literal ledger contains fractional atoms')
            asset=names.get(identity)
            deltas.append({'location':identity[0],'asset_identity':identity[1],
                           'symbol':asset,'delta_atoms':int(delta)})
            if asset is not None:replay[asset]=replay.get(asset,0)+int(delta)
        receipts.append({'id':event['id'],'kind':event['kind'],'deltas':deltas,
                         'evidence':event.get('evidence')})
    balances=[];current={}
    for identity,quantity in book.balances.items():
        if quantity!=int(quantity):raise ValueError('literal ledger contains fractional balance')
        asset=names.get(identity)
        balances.append({'location':identity[0],'asset_identity':identity[1],
                         'symbol':asset,'atoms':int(quantity)})
        if asset is not None:current[asset]=int(quantity)
    for asset in assets:current.setdefault(asset,0)
    recognized=all(row['symbol'] is not None for row in balances) and all(d['symbol'] is not None for e in receipts for d in e['deltas'])
    return {'literal_ledger_events':receipts,'literal_balance_rows':balances,'current_atoms':current,
            'literal_balances_reconciled':recognized and replay==current,
            'literal_replay_atoms':replay,'attribution_partial_only':True}


def json_safe(value):
    from fractions import Fraction
    from decimal import Decimal
    if isinstance(value,Fraction):
        return {'numerator':value.numerator,'denominator':value.denominator}
    if isinstance(value,Decimal):return str(value)
    if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_safe(v) for v in value]
    if value is None or isinstance(value,(str,int,bool)):return value
    raise ValueError('unsupported partial receipt value')
