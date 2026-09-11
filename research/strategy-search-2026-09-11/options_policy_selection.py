"""Pure fixed common-expiry/strike selection. No price ranking or market I/O."""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction as F
import json
import math
import re

DAY=86400000


def number(value):
    if isinstance(value,bool) or not isinstance(value,(str,int)):raise ValueError('literal numeric field required')
    text=str(value)
    if len(text)>64:raise ValueError('numeric length')
    value=Decimal(text)
    if not value.is_finite() or not -32<=value.adjusted()<=32 or value<=0:raise ValueError('positive bounded numeric field required')
    return F(value)


def literal(value):
    with localcontext() as ctx:
        ctx.prec=512
        result=Decimal(value.numerator)/Decimal(value.denominator)
    if F(result)!=value:raise ValueError('exact finite decimal projection unavailable')
    return format(result,'f')


def rule(row):
    if number(row['unit'])!=1:raise ValueError('only explicit unit1 supported')
    filters=row['filters']
    if not isinstance(filters,list) or any(not isinstance(f,dict) for f in filters):raise ValueError('filter list')
    lots=[f for f in filters if f.get('filterType')=='LOT_SIZE']
    prices=[f for f in filters if f.get('filterType')=='PRICE_FILTER']
    if len(lots)!=1 or len(prices)!=1:raise ValueError('unique lot/price filter required')
    lot=lots[0];minimum,maximum,step=[number(lot[k]) for k in ('minQty','maxQty','stepSize')]
    if number(row['minQty'])!=minimum or number(row['maxQty'])!=maximum or minimum>maximum:raise ValueError('top-level lot conflict')
    tick=number(prices[0]['tickSize'])
    return {'minimum':minimum,'maximum':maximum,'step':step,'tick':tick}


def select(metadata,*,asset,entry_ms,index):
    """Select identities first; a chosen pair's rule failure never picks another.

    Caller must separately admit raw metadata/index receipt and clock freshness.
    Numeric metadata enums and missing status do not establish account access.
    The result is one asset's complete/unavailable source selection, not a book.
    """
    if asset not in ('BTC','ETH') or type(entry_ms) is not int or entry_ms<=0 or entry_ms%3600000:raise ValueError('fixed asset/hour required')
    index=number(index)
    result={'asset':asset,'entry_ms':entry_ms,'index':literal(index),'status':'unavailable','selected':None,
            'scope':'Rule-bound public metadata only; no access, margin, fills, premium or profitability claim.'}
    try:
        rows=metadata['optionSymbols'];parents=metadata['optionContracts']
        if not isinstance(rows,list) or len(rows)>10000 or any(not isinstance(r,dict) for r in rows):raise ValueError('bounded metadata row list')
        if not isinstance(parents,list):raise ValueError('metadata parent list')
        parent=[r for r in parents if isinstance(r,dict) and r.get('underlying')==asset+'USDT']
        if len(parent)!=1 or any(parent[0].get(k)!=v for k,v in (('baseAsset',asset),('quoteAsset','USDT'),('settleAsset','USDT'))):raise ValueError('unique underlying/settlement parent required')
        counts=Counter(r.get('symbol') for r in rows if isinstance(r.get('symbol'),str))
        groups={};excluded=Counter()
        for row in rows:
            if row.get('underlying')!=asset+'USDT' or row.get('side') not in ('CALL','PUT'):continue
            try:
                name=row['symbol'];expiry=row['expiryDate'];strike=number(row['strikePrice'])
                if not isinstance(name,str) or len(name)>64 or counts[name]!=1:raise ValueError('unique bounded identity')
                if type(expiry) is not int or not 0<expiry<=2**63-1 or expiry%3600000 or not 7*DAY<=expiry-entry_ms<=45*DAY:raise ValueError('hour-aligned expiry band')
                suffix='C' if row['side']=='CALL' else 'P'
                match=re.fullmatch(re.escape(asset)+r'-(\d{6})-(\d+(?:\.\d+)?)-'+suffix,name)
                if not match or match[1]!=datetime.fromtimestamp(expiry//1000,timezone.utc).strftime('%y%m%d') or number(match[2])!=strike:raise ValueError('symbol/expiry/strike binding')
                if row.get('quoteAsset')!='USDT' or ('status' in row and row['status']!='TRADING'):raise ValueError('quote/status')
                groups.setdefault((expiry,strike),{'CALL':[],'PUT':[]})[row['side']].append(row)
            except (KeyError,ValueError,TypeError,ArithmeticError,OverflowError):excluded['identity_or_time_ineligible']+=1
        candidates=[(key,group) for key,group in groups.items() if len(group['CALL'])==len(group['PUT'])==1]
        result.update(candidate_count=len(candidates),excluded_counts=dict(excluded))
        if not candidates:raise ValueError('no unique shared call/put identity')
        expiry=min({k[0] for k,g in candidates},key=lambda t:(abs(t-entry_ms-30*DAY),t))
        key,pair=min((item for item in candidates if item[0][0]==expiry),key=lambda item:(abs(item[0][1]-index),item[0][1],item[1]['CALL'][0]['symbol'],item[1]['PUT'][0]['symbol']))
        chosen={'call':pair['CALL'][0]['symbol'],'put':pair['PUT'][0]['symbol'],'expiry_ms':expiry,'exit_ms':expiry-DAY,'strike':literal(key[1])}
        result['selected']=chosen
        cr,pr=rule(pair['CALL'][0]),rule(pair['PUT'][0])
        # Intersect minimum-anchored lot grids exactly (generalized CRT).
        scale=math.lcm(*(value.denominator for r in (cr,pr) for value in (r['minimum'],r['step'])))
        a,b=int(cr['minimum']*scale),int(pr['minimum']*scale)
        m,n=int(cr['step']*scale),int(pr['step']*scale)
        common=math.gcd(m,n)
        if (b-a)%common:raise ValueError('chosen minimum-anchored lot grids have no intersection')
        modulus=n//common
        k=0 if modulus==1 else ((b-a)//common*pow(m//common,-1,modulus))%modulus
        first=a+m*k;period=math.lcm(m,n);lower=max(a,b)
        first+=period*max(0,(lower-first+period-1)//period)
        quantity=F(first,scale)
        if quantity>min(cr['maximum'],pr['maximum']):raise ValueError('minimum common quantity exceeds maximum')
        if any(((quantity-r['minimum'])/r['step']).denominator!=1 for r in (cr,pr)):raise ValueError('common quantity violates minimum-anchored grid')
        if cr['tick']!=pr['tick']:raise ValueError('chosen pair tick disagreement; current common-tick engine unavailable')
        chosen.update(unit=1,quantity=literal(quantity),option_tick=literal(cr['tick']),
                      quantity_grid='(quantity-minQty) is an integer multiple of stepSize',
                      price_filter_compliance='unavailable; each execution still requires min/max/offset price validation',
                      call_rule={k:literal(v) for k,v in cr.items()},put_rule={k:literal(v) for k,v in pr.items()},
                      metadata_status={side:pair[side.upper()][0].get('status','unverified') for side in ('call','put')})
        result['status']='complete'
    except (KeyError,ValueError,TypeError,ArithmeticError,OverflowError) as exc:result['reason']=type(exc).__name__+': '+str(exc)
    if len(json.dumps(result).encode())>16384:raise ValueError('selection projection cap')
    return result
