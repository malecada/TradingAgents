"""Pure canonical exclusion inventory; no source requests or financial outcomes."""
import json

ORACLE='0x2cc0fc26ed4563a5ce5e8bdcfe1a2878676ae156'


def address_word(word):
    if len(word)!=64 or word[:24]!='0'*24:raise ValueError('noncanonical oracle asset address padding')
    int(word,16)
    return '0x'+word[24:].lower()


def price_fields(request_keys):
    """Expand actual/uncertain scalar and vector calls to block+asset exclusions.

    This covers the single fixed oracle and reviewed getter encodings. Unknown
    historical block tags are retained as unresolved; they never prove novelty.
    """
    fields=set();unresolved=[]
    for key in request_keys:
        method,params=json.loads(key)
        if method!='eth_call' or not params or not isinstance(params[0],dict):continue
        call=params[0]
        if str(call.get('to','')).lower()!=ORACLE:continue
        data=str(call.get('data','')).lower()
        if data.startswith('0xb3596f07'):
            if len(data)!=74:raise ValueError('prior scalar oracle call shape unsupported')
            assets=[address_word(data[10:])]
        elif data.startswith('0x9d23d9f2'):
            body=data[10:]
            if len(body)<128 or len(body)%64 or int(body[:64],16)!=32:raise ValueError('prior oracle vector layout unsupported')
            count=int(body[64:128],16)
            if count<=0 or len(body)!=128+64*count:raise ValueError('prior oracle vector length unsupported')
            assets=[address_word(body[128+i*64:192+i*64]) for i in range(count)]
        else:continue
        tag=params[1] if len(params)==2 else None
        block_hash=tag.get('blockHash') if isinstance(tag,dict) else None
        if not isinstance(block_hash,str) or len(block_hash)!=66 or not block_hash.startswith('0x'):
            unresolved.append({'request_key':key,'assets':assets,'reason':'prior price block tag unresolved'});continue
        int(block_hash[2:],16)
        fields.update(block_hash.lower()+'|'+asset for asset in assets)
    return {'prior_oracle_fields':sorted(fields),'unresolved_prior_price_tags':unresolved}


def assert_new_price_fields(block_hash,assets,inventory):
    if inventory['unresolved_prior_price_tags']:raise ValueError('unresolved prior price tags cannot prove first acquisition')
    previous=set(inventory['prior_oracle_fields'])
    if any(block_hash.lower()+'|'+asset.lower() in previous for asset in assets):
        raise ValueError('new oracle vector would remeasure inherited actual or uncertain price field')
