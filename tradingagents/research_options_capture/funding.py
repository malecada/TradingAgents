"""Conditional funding-source normalization; no requests, positions or PnL.

Primary documentation checked 2026-09-15 (one URL open, two in-page finds):
https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data
Funding history documents rateType Regular/Special, inclusive bounds and 1000
rows maximum. The optional missing-type COIN compatibility is the separately
labeled retained docs/funding-capture/SOURCE_POLICY.md research convention.
"""
from bisect import bisect_right
from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction
from .adapter import decode, literal
from .schedule import ASSETS, DAY, HOUR, WINDOW, calendar

DRIFT_MS = 1000
QUALIFICATION = ('Conditional hourly announcement coverage and at most 1000ms venue/local offset drift within one hour; '
                 'compatible calibration hull, never intersection tightening. Missing intrahour schedule changes and '
                 'unpublished events cannot be ruled out. Venue timestamp ordering is assumed monotone across the modeled path. Public funding history is not an account debit.')


def _integer(value):
    if type(value) is not int or not 0 < value < 2**53:
        raise ValueError('positive literal millisecond timestamp required')
    return value


def _number(value, positive=False):
    if not isinstance(value, (str, int)) or isinstance(value, bool) or len(str(value)) > 64:
        raise ValueError('bounded literal funding number required')
    number = Decimal(str(value))
    if not number.is_finite() or number and not -32 <= number.adjusted() <= 32 or positive and number <= 0:
        raise ValueError('funding number outside scope')
    return literal(Fraction(number))


def _read(receipts, group, spec):
    return decode(receipts.get(group, {})[spec['id']], spec['request'],
                  scheduled_ms=spec['scheduled_ms'], cap=spec['body_cap'])


def _bounds(event, clocks):
    candidates = []
    for clock in clocks:
        lo, hi = clock['offset_low_ms']-DRIFT_MS, clock['offset_high_ms']+DRIFT_MS
        early, late = event-hi, event-lo
        # Every possible local event time must lie within the declared span.
        if max(abs(early-clock['request_ms']), abs(late-clock['retrieval_ms'])) <= HOUR:
            candidates.append((lo, hi))
    if not candidates:
        raise ValueError('no venue clock calibration within one hour')
    if max(x[0] for x in candidates) > min(x[1] for x in candidates):
        raise ValueError('contradictory nearby clock calibrations')
    low, high = min(x[0] for x in candidates), max(x[1] for x in candidates)
    return [event-high, event-low]


def _outside(event, clocks, actions):
    # Boundary venue-time bands use calibrations near each actual local action.
    # This compares ordering in venue time; it does not extrapolate an offset to
    # the future event or assign that outside event a fabricated local clock.
    for label, action in [('before-entry', actions[0]), ('after-exit', actions[-1])]:
        nearby = [c for c in clocks if abs(c['request_ms']-action) < WINDOW]
        if not nearby:
            continue
        lows = [c['offset_low_ms']-DRIFT_MS for c in nearby]
        highs = [c['offset_high_ms']+DRIFT_MS for c in nearby]
        if max(lows) > min(highs):
            continue
        if label == 'before-entry' and event < action+min(lows):
            return label
        if label == 'after-exit' and event > action+max(highs):
            return label
    return None


def normalize(*, asset, entry_ms, exit_ms, receipts, bootstrap_receipt=None):
    """Return source diagnostics and engine_inputs only on known conditional coverage.

    receipts contains frozen slot-id maps under known/daily/final. Missing slots
    remain unavailable, not empty successful queries. Optional bootstrap_receipt
    is the exact initial futures exchangeInfo source, not a metadata assertion.
    Funding event time_ms is an ownership-equivalent integer representative of
    retained local bounds, not a claimed exact timestamp. All raw versions stay
    in event_versions, including excluded/unannounced/conflicting rows.
    """
    if asset not in ASSETS or type(exit_ms) is not int or not entry_ms+HOUR <= exit_ms <= entry_ms+44*DAY or (exit_ms-entry_ms)%HOUR:
        raise ValueError('fixed asset/hourly selected exit required')
    slots = calendar(entry_ms)
    if not isinstance(receipts, dict) or set(receipts)-{'known','daily','final'}:
        raise ValueError('frozen receipt groups')
    for group, mapping in receipts.items():
        if not isinstance(mapping, Mapping) or set(mapping)-{s['id'] for s in slots[group]}:
            raise ValueError('unexpected source slot identity')
    actions = list(range(entry_ms+WINDOW, exit_ms+WINDOW+1, HOUR))
    reasons, diagnostics, clocks, announcements, versions, queries = [], [], [], [], [], []
    expected = set()
    def unavailable(where, exc, required=True):
        (reasons if required else diagnostics).append({'source':where, 'reason':str(exc)})
    coin_compatibility = False
    if bootstrap_receipt is not None:
        try:
            spec = next(s for s in slots['bootstrap'] if s['id']=='initial-futures-rules')
            metadata, _, _ = decode(bootstrap_receipt, spec['request'], scheduled_ms=spec['scheduled_ms'], cap=spec['body_cap'])
            rows = [r for r in metadata['symbols'] if r.get('symbol')==asset+'USDT']
            coin_compatibility = len(rows)==1 and all(rows[0].get(k)==v for k,v in [('underlyingType','COIN'),('baseAsset',asset),('quoteAsset','USDT'),('marginAsset','USDT'),('contractType','PERPETUAL'),('status','TRADING')])
            if not coin_compatibility:raise ValueError('initial COIN/USDT perpetual identity unavailable')
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            unavailable('initial-futures-rules compatibility',exc,False)
    known = {s['id']:s for s in slots['known']}
    hours = (exit_ms-entry_ms)//HOUR
    for h in range(hours+1):
        name=f'h{h:04d}-futures-time';spec=known[name]
        try:
            value, _, meta = _read(receipts,'known',spec)
            server = _integer(value['serverTime'])
            if not meta['request_ms']-WINDOW <= server <= meta['controller_retrieval_ms']+WINDOW:
                raise ValueError('implausible venue clock')
            clocks.append({'source':name,'request_ms':meta['request_ms'],'retrieval_ms':meta['controller_retrieval_ms'],
                           'offset_low_ms':server-meta['controller_retrieval_ms'],'offset_high_ms':server-meta['request_ms']})
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            unavailable(name,exc)
    for h in range(hours):
        name=f'h{h:04d}-{asset.lower()}-perp-mark';spec=known[name]
        try:
            value, _, meta = _read(receipts,'known',spec)
            if value['symbol']!=asset+'USDT':raise ValueError('announcement symbol')
            provider = _integer(value['time']);nxt = _integer(value['nextFundingTime'])
            if nxt <= provider:raise ValueError('stale nextFundingTime is not a forecast')
            bounds = _bounds(provider,clocks)
            if bounds[0] < spec['scheduled_ms']-DRIFT_MS or bounds[1] > meta['controller_retrieval_ms']+DRIFT_MS:
                raise ValueError('stale or contradictory announcement clock')
            # Compare future venue timestamp with the contemporaneous venue-time
            # upper band at local receipt availability. This proves prospective
            # observation without extrapolating a calibration eight hours ahead.
            upper_offset = provider-bounds[0]
            if nxt <= meta['controller_retrieval_ms']+upper_offset:
                raise ValueError('nextFundingTime not proved future at local receipt availability')
            announcements.append({'source':name,'provider_time_ms':provider,'next_funding_time_ms':nxt,
                                  'local_provider_bounds_ms':bounds,'available_ms':meta['controller_retrieval_ms']})
            expected.add(nxt)
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            unavailable(name,exc)
    identities = {}
    final_ids = set()
    for group in ('daily','final'):
        for spec in slots[group]:
            if spec['request']['endpoint'].endswith('/fundingRate') is False or spec['request']['parameters']['symbol']!=asset+'USDT':
                continue
            params = spec['request']['parameters']
            required = group=='final' or params['startTime'] <= actions[-1] and params['endTime'] >= actions[0]
            query = {'source':spec['id'],'required_for_held_coverage':required,'status':'unavailable','rows':None}
            queries.append(query)
            try:
                rows, _, meta = _read(receipts,group,spec)
                if not isinstance(rows,list) or len(rows)>1000:raise ValueError('history array/row bound')
                query['rows']=len(rows)
                if len(rows)==1000:unavailable(spec['id'],'1000-row response is unexhausted; no extra page',required)
                previous = None
                for index, row in enumerate(rows):
                    retained={'source':spec['id'],'index':index,'raw':row,'retrieval_ms':meta['controller_retrieval_ms'],'status':'unavailable'}
                    versions.append(retained)
                    try:
                        if not isinstance(row,dict) or row.get('symbol')!=asset+'USDT':raise ValueError('event symbol identity')
                        t=_integer(row['fundingTime'])
                        if not params['startTime']<=t<=params['endTime']:raise ValueError('out-of-query funding row')
                        if previous is not None and t<previous:raise ValueError('nonascending funding rows')
                        previous=t
                        rate=_number(row['fundingRate']);mark=_number(row['markPrice'],True)
                        kind=row.get('rateType')
                        if kind=='Regular':label='Regular'
                        elif 'rateType' not in row and coin_compatibility:label='unspecified_crypto'
                        else:raise ValueError('unsupported or ambiguous funding rateType')
                        identity=(rate,mark,label)
                        retained.update(status='parsed',funding_time_ms=t,rate=rate,mark=mark,rate_type=label)
                        if t in identities and identities[t]!=identity:
                            unavailable(spec['id'],'conflicting duplicate funding event '+str(t),True)
                        else:identities[t]=identity
                        if group=='final':final_ids.add(t)
                    except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
                        retained['reason']=str(exc);unavailable(spec['id']+' row '+str(index),exc,required)
                query['status']='exhaustion-unproven' if len(rows)==1000 else 'received'
            except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
                query['reason']=str(exc);unavailable(spec['id'],exc,required)
    event_diagnostics, engine_events, engine_expected = [], [], []
    for venue_time in sorted(expected | set(identities)):
        item={'funding_time_ms':venue_time,'announced':venue_time in expected,'published':venue_time in identities,
              'final_published':venue_time in final_ids,'local_bounds_ms':None,'owner_segment':None,'status':'unavailable'}
        event_diagnostics.append(item)
        outside = _outside(venue_time,clocks,actions)
        try:
            early,late=_bounds(venue_time,clocks);item['local_bounds_ms']=[early,late]
        except ValueError as exc:
            if outside:
                item.update(status='outside-held-window',exclusion=outside,clock_reason=str(exc))
                continue
            item['reason']=str(exc);unavailable('event '+str(venue_time),exc)
            continue
        if outside:
            item.update(status='outside-held-window',exclusion=outside)
            continue
        try:
            if any(early<=action<=late for action in actions):raise ValueError('funding interval touches an action boundary; ownership unknown')
            if late<actions[0] or early>actions[-1]:
                item['status']='outside-held-window';continue
            segment=bisect_right(actions,early)-1
            if segment<0 or segment>=len(actions)-1 or not actions[segment]<early<=late<actions[segment+1]:raise ValueError('funding ownership segment unavailable')
            representative=(early+late)//2
            item.update(owner_segment=segment,representative_local_ms=representative)
            engine_expected.append(representative)
            if venue_time not in identities:raise ValueError('announced event missing from published history')
            if venue_time not in final_ids:raise ValueError('event missing from fixed final partitions')
            rate,mark,kind=identities[venue_time]
            item.update(status='known-conditional',rate=rate,mark=mark,rate_type=kind)
            engine_events.append({'time_ms':representative,'rate':rate,'mark':mark})
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            item['reason']=str(exc);unavailable('event '+str(venue_time),exc)
    if len(set(engine_expected))!=len(engine_expected):unavailable('ownership projection','distinct events collide in representative local time')
    engine_expected=sorted(set(engine_expected));engine_events.sort(key=lambda r:r['time_ms'])
    coverage = not reasons
    return {'schema_version':1,'asset':asset,'entry_action_ms':actions[0],'exit_action_ms':actions[-1],
            'status':'known-conditional' if coverage else 'unavailable','coverage_known':coverage,'qualification':QUALIFICATION,
            'announcements':announcements,'event_versions':versions,'events':event_diagnostics,'queries':queries,'clock_calibrations':clocks,
            'reasons':reasons,'diagnostics':diagnostics,
            'expected_funding_times':engine_expected,'funding_events':engine_events,
            'engine_inputs':{'expected_funding_times':engine_expected,'funding_events':engine_events} if coverage else None}
