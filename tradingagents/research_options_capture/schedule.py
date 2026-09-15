"""One finite prospective options source calendar; no market interpretation."""
DAY = 86400000
HOUR = 3600000
WINDOW = 5000
ASSETS = ('BTC', 'ETH')
JOURNALS = ('bootstrap', 'known', 'selected', 'daily', 'final')


def request(venue, route, **parameters):
    return {'endpoint': f'https://{venue}.binance.com/{venue}/v1/{route}', 'parameters': parameters}


def slot(name, at, req, cap=8192):
    return {'id': name, 'scheduled_ms': at, 'deadline_ms': at + WINDOW,
            'request': req, 'body_cap': cap}


def rules(prefix, at):
    return [slot(prefix + '-options-rules', at, request('eapi', 'exchangeInfo'), 5*1024**2),
            slot(prefix + '-futures-rules', at, request('fapi', 'exchangeInfo'), 5*1024**2),
            slot(prefix + '-funding-rules', at, request('fapi', 'fundingInfo'), 65536)]


def validate_entry(entry_ms):
    if type(entry_ms) is not int or entry_ms <= 2*DAY or entry_ms % HOUR:
        raise ValueError('positive absolute UTC hourly entry required')
    return entry_ms


def calendar(entry_ms, selection=None):
    validate_entry(entry_ms)
    out = {name: [] for name in JOURNALS}
    out['bootstrap'] = rules('initial', entry_ms - 60000)
    for h in range(1057):
        at = entry_ms + h*HOUR
        prefix = f'h{h:04d}'
        out['known'].extend([slot(prefix+'-options-time', at, request('eapi', 'time')),
                             slot(prefix+'-futures-time', at, request('fapi', 'time'))])
        for asset in ASSETS:
            symbol = asset+'USDT'
            out['known'].extend([
                slot(prefix+'-'+asset.lower()+'-index', at, request('eapi', 'index', underlying=symbol)),
                slot(prefix+'-'+asset.lower()+'-perp-depth', at, request('fapi', 'depth', symbol=symbol, limit=10)),
                slot(prefix+'-'+asset.lower()+'-perp-mark', at, request('fapi', 'premiumIndex', symbol=symbol))])
            if selection is not None:
                chosen = selection[asset]
                expiry = chosen['expiry_ms']
                if type(expiry) is not int or expiry % HOUR or not entry_ms+7*DAY <= expiry <= entry_ms+45*DAY:
                    raise ValueError('selected expiry outside fixed contract')
                for side in ('call', 'put'):
                    for role in ('depth', 'mark'):
                        params = {'symbol': chosen[side]}
                        if role == 'depth': params['limit'] = 10
                        out['selected'].append(slot(prefix+'-'+asset.lower()+'-'+side+'-'+role, at, request('eapi', role, **params)))
    for d in range(45):
        at = entry_ms+d*DAY+60000
        prefix = f'd{d:02d}'
        out['daily'].extend(rules(prefix, at))
        for asset in ASSETS:
            out['daily'].append(slot(prefix+'-'+asset.lower()+'-funding', at,
                request('fapi', 'fundingRate', symbol=asset+'USDT', startTime=at-2*DAY,
                        endTime=at, limit=1000), 524288))
    for asset in ASSETS:
        for i, (start, end) in enumerate(((entry_ms, entry_ms+22*DAY-1),
                                          (entry_ms+22*DAY, entry_ms+44*DAY+WINDOW))):
            out['final'].append(slot(f'final-{asset.lower()}-{i}', entry_ms+45*DAY,
                request('fapi', 'fundingRate', symbol=asset+'USDT', startTime=start, endTime=end, limit=1000), 524288))
    return out


def groups(slots):
    result = {}
    for item in slots:
        result.setdefault(item['scheduled_ms'], []).append(item['id'])
    return sorted(result.items())


def post_exit(name, at, selection):
    if name.endswith('-index'):
        return at > max(selection[a]['expiry_ms']-DAY for a in ASSETS)
    for asset in ASSETS:
        if '-'+asset.lower()+'-' in name:
            return at > selection[asset]['expiry_ms']-DAY
    return False
